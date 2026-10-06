"""Streaming Cycle 6 reductions. Exact scalar quantiles use a disk-backed store.

No raw trajectories are retained. SQLite has a fixed 2 MiB cache; Theil-Sen
retains only the preregistered every-tenth subsample (at most 500 observations).
Outputs are derived artifacts outside immutable run directories.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import tempfile


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json(raw):
    def invalid(value):
        raise ValueError(f"nonfinite JSON value: {value}")
    def finite_float(raw_value):
        value = float(raw_value)
        if not math.isfinite(value):
            invalid(raw_value)
        return value
    return json.loads(raw, object_pairs_hook=_unique_pairs, parse_constant=invalid, parse_float=finite_float)


def json_lines(path, optional=False, max_line_bytes=16 * 1024 * 1024):
    path = Path(path)
    if optional and not path.exists():
        return
    with path.open("rb") as stream:
        index = 0
        while True:
            line = stream.readline(max_line_bytes + 1)
            if not line:
                break
            index += 1
            if len(line) > max_line_bytes or not line.endswith(b"\n"):
                raise ValueError(f"{path.name}:{index}: oversized or torn JSONL line")
            try:
                value = strict_json(line)
            except (ValueError, UnicodeDecodeError) as exc:
                raise ValueError(f"{path.name}:{index}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path.name}:{index}: JSON object required")
            yield value


class ScalarStore:
    """External scalar ordering with fixed-memory page cache, no outcome cache."""
    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="csc-cycle6-reduction-")
        self.db = sqlite3.connect(str(Path(self.temporary.name) / "scalars.sqlite"))
        self.db.execute("PRAGMA cache_size=-2048")
        self.db.execute("PRAGMA temp_store=FILE")
        self.db.execute("CREATE TABLE samples (name TEXT, epoch INTEGER, value REAL)")
        self.db.execute("CREATE INDEX scalar_order ON samples(name,value)")

    def add(self, name, epoch, value):
        if value is None:
            return
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"invalid numeric metric {name}: {value!r}")
        self.db.execute("INSERT INTO samples VALUES(?,?,?)", (name, epoch, value))

    def count(self, name, lower=None, upper=None):
        clause, args = self._filter(name, lower, upper)
        return self.db.execute("SELECT count(*) FROM samples WHERE " + clause, args).fetchone()[0]

    @staticmethod
    def _filter(name, lower, upper):
        clause, args = "name=?", [name]
        if lower is not None:
            clause += " AND epoch>=?"
            args.append(lower)
        if upper is not None:
            clause += " AND epoch<?"
            args.append(upper)
        return clause, args

    def quantile(self, name, p, lower=None, upper=None):
        clause, args = self._filter(name, lower, upper)
        n = self.count(name, lower, upper)
        if not n:
            return None
        rank = (n - 1) * p
        left = math.floor(rank)
        rows = self.db.execute("SELECT value FROM samples WHERE " + clause +
                               " ORDER BY value LIMIT 2 OFFSET ?", args + [left]).fetchall()
        a, b = rows[0][0], rows[-1][0]
        return a + (b - a) * (rank - left)

    def distribution(self, name, lower=None, upper=None):
        result = {"n": self.count(name, lower, upper)}
        for label, p in (("p50", .5), ("p90", .9), ("p95", .95), ("p99", .99), ("max", 1)):
            result[label] = self.quantile(name, p, lower, upper)
        return result

    def close(self):
        self.db.close()
        self.temporary.cleanup()


def memory_trend(store, name, warmup, duration, bound, quartile_bound):
    """Frozen second-half OLS/every-tenth Theil-Sen, units bytes per epoch."""
    measured = duration - warmup
    midpoint = warmup + measured // 2
    n, mean_x, mean_y, xx, xy = 0, 0., 0., 0., 0.
    subsample = []
    start = end = minimum = maximum = None
    for epoch, value in store.db.execute(
            "SELECT epoch,value FROM samples WHERE name=? AND epoch>=? ORDER BY epoch", (name, warmup)):
        if start is None:
            start = value
        end = value
        minimum = value if minimum is None else min(minimum, value)
        maximum = value if maximum is None else max(maximum, value)
        if epoch < midpoint:
            continue
        if n % 10 == 0:
            if len(subsample) >= 500:
                raise ValueError("Theil-Sen sample exceeds frozen 10,000-epoch design")
            subsample.append((epoch, value))
        n += 1
        dx = epoch - mean_x
        mean_x += dx / n
        dy = value - mean_y
        mean_y += dy / n
        xx += dx * (epoch - mean_x)
        xy += dx * (value - mean_y)
    ols = xy / xx if xx else None
    # Pair slopes are also external; only the frozen subsample stays in memory.
    slope_name = "__theil_sen__" + name
    for i, (x, y) in enumerate(subsample):
        for other_x, other_y in subsample[i + 1:]:
            if other_x != x:
                store.add(slope_name, 0, (other_y - y) / (other_x - x))
    theil = store.quantile(slope_name, .5)
    quarter = measured // 4
    first = store.quantile(name, .5, warmup, warmup + quarter)
    last = store.quantile(name, .5, duration - quarter, duration)
    difference = None if first is None or last is None else last - first
    classification = "inconclusive"
    expected_n = duration - midpoint
    complete_samples = n == expected_n and store.count(name, warmup, duration) == measured
    if complete_samples and ols is not None and theil is not None and difference is not None:
        if abs(ols) <= bound and abs(theil) <= bound and abs(difference) <= quartile_bound:
            classification = "supports a plateau at study resolution"
        elif ols > bound and theil > bound:
            classification = "positive trend remains"
    return {"metric": name, "units": "bytes/epoch", "second_half_start_epoch": midpoint,
            "second_half_n": n, "theil_sen_subsample_n": len(subsample),
            "complete_sample_coverage": complete_samples, "ols_slope": ols,
            "theil_sen_slope": theil, "equivalence_bound": bound,
            "first_quartile_median_bytes": first, "last_quartile_median_bytes": last,
            "quartile_difference_bytes": difference, "quartile_bound_bytes": quartile_bound,
            "start_bytes": start, "end_bytes": end, "min_bytes": minimum,
            "max_bytes": maximum, "classification": classification}


def analyze_run(run_path, factors=None):
    """Reduce required finalized scalars; optional CFR loss keeps denominators."""
    run_path = Path(run_path)
    manifest = strict_json((run_path / "manifest.json").read_bytes())
    config = manifest["config"]
    warmup, duration = config["warmup_epochs"], config["duration_epochs"]
    if duration > 10000:
        raise ValueError("outside frozen Cycle 6 epoch bound")
    denominator = duration - warmup
    store = ScalarStore()
    db = store.db
    db.execute("CREATE TABLE epochs(epoch INTEGER PRIMARY KEY, final TEXT, cfr TEXT, committed REAL)")
    db.execute("CREATE TABLE branches(epoch INTEGER,bid TEXT PRIMARY KEY,role TEXT,status TEXT,latency REAL)")
    db.execute("CREATE TABLE deliveries(rid TEXT PRIMARY KEY,status TEXT,latency REAL)")
    production_epochs, statuses = 0, Counter()
    resource_fields = ("production_interval_ms", "production_decision_ms", "production_path_ms",
                       "coordinator_cpu_ms", "coordinator_rss_bytes", "coordinator_python_current_bytes",
                       "coordinator_python_peak_bytes", "worker_rss_bytes", "coordinator_handles",
                       "worker_count", "warm_worker_count", "worker_pool_rss_bytes", "pending_epochs", "retained_completed_epochs", "duplicate_cache_size",
                       "physical_queue_depth", "physical_inflight_tasks", "physical_queue_bytes",
                       "physical_inflight_bytes", "evidence_spool_items", "evidence_spool_bytes",
                       "artifact_storage_bytes", "evidence_age_ms", "durable_availability_ms")
    resource_maxima = {}
    try:
        journal_path = run_path / "epoch_journal.jsonl"
        if not journal_path.exists():
            journal_path = run_path / "production_journal.jsonl"
        for record in json_lines(journal_path):
            epoch = record["epoch"]
            db.execute("INSERT INTO epochs(epoch,committed) VALUES(?,?)", (epoch, record["committed_monotonic_s"]))
            production_epochs += 1
            for branch in record["branches"]:
                db.execute("INSERT INTO branches(epoch,bid,role) VALUES(?,?,?)",
                           (epoch, branch["branch_id"], branch["role"]))
        for record in json_lines(run_path / "resource_metrics.jsonl"):
            epoch = record["epoch"]
            for key, value in record.items():
                if (key.startswith("physical_") or key.startswith("evidence_spool_")) and type(value) in (int, float):
                    resource_maxima[key] = max(resource_maxima.get(key, 0), value)
            if warmup <= epoch < duration:
                for field in resource_fields:
                    store.add(field, epoch, record.get(field))
                for field in ("requested_k", "admitted_k", "completed_k"):
                    store.add(field, epoch, record.get(field))
        for record in json_lines(run_path / "lifecycle.jsonl", optional=True):
            epoch = record.get("epoch", -1)
            status = record.get("status")
            if status == "FINALIZED":
                old = db.execute("SELECT final FROM epochs WHERE epoch=?", (epoch,)).fetchone()
                if old is None or old[0] is not None:
                    raise ValueError("duplicate or unknown finalized epoch")
                db.execute("UPDATE epochs SET final=? WHERE epoch=?", (json.dumps(record), epoch))
            if warmup <= epoch < duration:
                statuses[status] += 1
                if status == "COMPLETED":
                    store.add("branch_completion_ms", epoch, record.get("branch_completion_ms"))
            if status in ("COMPLETED", "FAILED", "TIMED_OUT", "EXPIRED", "DROPPED", "REJECTED"):
                db.execute("UPDATE branches SET status=?,latency=? WHERE bid=?",
                           (status, record.get("branch_completion_ms"), record.get("branch_id")))
        delivery_counts = Counter()
        for record in json_lines(run_path / "evidence_delivery.jsonl", optional=True):
            rid = record.get("record_id", "")
            db.execute("INSERT INTO deliveries VALUES(?,?,?)", (rid, record["status"], record.get("persistence_latency_ms")))
            if rid.startswith("epoch:") and rid.endswith(":comparison"):
                epoch = int(rid.split(":")[1])
                if warmup <= epoch < duration:
                    delivery_counts[record["status"]] += 1
                    if record["status"] == "PERSISTED":
                        store.add("durable_availability_ms", epoch, record.get("persistence_latency_ms"))
        for record in json_lines(run_path / "cfr.jsonl", optional=True):
            epoch = record["epoch"]
            old = db.execute("SELECT cfr FROM epochs WHERE epoch=?", (epoch,)).fetchone()
            if old is None or old[0] is not None:
                raise ValueError("duplicate or unknown persisted CFR epoch")
            # Retain only scalar availability, never raw branches or trajectories.
            compact = {key: record.get(key) for key in ("evidence_completeness", "requested_k", "admitted_k",
                        "completed_k", "evidence_age_ms", "comparison_completion_ms", "mirror_completed")}
            compact["accepted_mirrors"] = sum(b.get("role") == "MIRROR" and
                b.get("status") == "REPORTED" and b.get("utility") is not None and
                b.get("synchronization", {}).get("comparable", False) for b in record["branches"])
            compact["accepted_alternatives"] = sum(b.get("role") == "SHADOW" and
                b.get("status") == "REPORTED" and b.get("utility") is not None and
                b.get("synchronization", {}).get("comparable", False) for b in record["branches"])
            db.execute("UPDATE epochs SET cfr=? WHERE epoch=?", (json.dumps(compact), epoch))
        complete = partial = production_only = mirror = alternatives = persisted = unknown = finalized = durably_complete = 0
        admitted = completed = 0
        for epoch, final_raw, cfr_raw in db.execute("SELECT epoch,final,cfr FROM epochs WHERE epoch>=? AND epoch<? ORDER BY epoch", (warmup, duration)):
            final = json.loads(final_raw) if final_raw else {}
            cfr = json.loads(cfr_raw) if cfr_raw else {}
            record = dict(cfr)
            record.update({key: value for key, value in final.items() if value is not None})
            if final_raw:
                finalized += 1
            if cfr_raw:
                persisted += 1
            state = record.get("evidence_completeness")
            if state is None:
                unknown += 1
                continue
            is_complete = state == "COMPLETE_COMPARISON"
            expected_records = [f"epoch:{epoch}:comparison"] + [f"epoch:{epoch}:branch:{bid}" for bid, role in
                db.execute("SELECT bid,role FROM branches WHERE epoch=?", (epoch,)) if role in ("MIRROR", "SHADOW")]
            deliveries = [db.execute("SELECT status,latency FROM deliveries WHERE rid=?", (rid,)).fetchone() for rid in expected_records]
            if is_complete and len(expected_records) == 1 + config["mirror_count"] + config["shadow_count"] and all(item and item[0] == "PERSISTED" for item in deliveries):
                durably_complete += 1
                if all(item[1] is not None for item in deliveries):
                    store.add("durable_complete_availability_ms", epoch, max(item[1] for item in deliveries))
            accepted_mirror = record.get("accepted_mirrors", record.get("mirror_accepted", record.get("mirror_completed")))
            accepted_alt = record.get("accepted_alternatives", record.get("completed_k"))
            if accepted_mirror is None:
                # Required terminal history survives optional CFR loss; no claim
                # of exact per-branch comparability beyond finalized classification.
                accepted_mirror = is_complete or state == "MIRROR_COMPLETE"
            if accepted_alt is None:
                accepted_alt = config["shadow_count"] if is_complete else 0
            has_any = is_complete or state in ("PARTIAL_ALTERNATIVES", "MIRROR_COMPLETE")
            complete += is_complete
            partial += has_any and not is_complete
            production_only += not has_any
            mirror += bool(accepted_mirror)
            alternatives += accepted_alt
            admitted += record.get("admitted_k", 0) or 0
            completed += record.get("completed_k", accepted_alt) or 0
            store.add("evidence_age_ms", epoch, record.get("evidence_age_ms", record.get("comparison_completion_ms")))
        cadence = store.distribution("production_interval_ms")
        cadence["missed_intervals_above_44ms"] = db.execute(
            "SELECT count(*) FROM samples WHERE name='production_interval_ms' AND value>44").fetchone()[0]
        evidence = {"scheduled_measured_epochs": denominator, "finalized_epochs": finalized,
                    "unknown_or_missing_epochs": denominator - max(0, production_epochs - warmup) + unknown,
                    "complete_epochs": complete, "partial_epochs": partial,
                    "production_only_epochs": production_only, "persisted_cfr_epochs": persisted,
                    "durably_complete_epochs": durably_complete,
                    "durably_complete_fraction": durably_complete / denominator if config["shadow_count"] else None,
                    "unavailable_cfr_epochs": denominator - persisted,
                    "complete_fraction": complete / denominator if config["shadow_count"] else None,
                    "partial_fraction": partial / denominator if config["shadow_count"] else None,
                    "persisted_cfr_fraction": persisted / denominator,
                    "mirror_available_epochs": mirror, "mirror_availability_fraction": mirror / denominator if config["mirror_count"] else None,
                    "alternative_completions": alternatives, "requested_alternatives": denominator * config["shadow_count"],
                    "admitted_alternatives": admitted, "completed_alternatives": completed,
                    "terminal_counts": dict(statuses), "comparison_delivery_counts_measured": dict(delivery_counts),
                    "branch_completion_ms": store.distribution("branch_completion_ms"),
                    "comparison_age_ms": store.distribution("evidence_age_ms"),
                    "durable_availability_ms": store.distribution("durable_availability_ms"),
                    "durable_complete_availability_ms": store.distribution("durable_complete_availability_ms"),
                    "persistence_dispositions_all_epochs": manifest.get("evidence_persistence", {})}
        result = {"run_id": manifest["experiment_id"], "status": manifest["status"],
                  "factors": factors or {}, "config_hash": manifest["config_hash"],
                  "scheduled_epochs": duration, "production_epochs": production_epochs,
                  "missing_production_epochs": duration - production_epochs,
                  "warmup_epochs": warmup, "cadence_ms": cadence,
                  "decision_latency_ms": store.distribution("production_decision_ms"), "evidence": evidence,
                  "resource_distributions": {field: store.distribution(field) for field in resource_fields[3:]},
                  "resource_high_water_all_epochs": resource_maxima,
                  "memory_trends": {field: memory_trend(store, field, warmup, duration, bound, quartile)
                    for field, bound, quartile in (("coordinator_rss_bytes", 104.8576, 1048576),
                                                   ("coordinator_python_current_bytes", 26.2144, 262144))},
                  "archive_bytes": sum(p.stat().st_size for p in run_path.iterdir() if p.is_file()),
                  "run_manifest_sha256": file_hash(run_path / "manifest.json")}
        summary_path = run_path / "summary.json"
        if summary_path.exists():
            summary = strict_json(summary_path.read_bytes())
            result["production_semantic_sha256"] = summary.get("production_semantic_sha256")
            result["workload_sha256"] = summary.get("workload_sha256")
            result["unauthorized_mutations"] = summary.get("unauthorized_production_mutations_from_shadow")
            result["offline_metrics"] = {key: value for key, value in summary.items() if key.startswith("offline_")}
        return result
    finally:
        store.close()


def write_figure(rows, output):
    """Deterministic SVG compares measured cadence and original-set coverage."""
    height = 65 + 18 * len(rows)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="{height}" viewBox="0 0 1050 {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="sans-serif" font-size="11" fill="#17212b">',
             '<text x="10" y="20">Run identity</text><text x="415" y="20">Cadence p99 (ms, scale 0–200)</text>',
             '<text x="760" y="20">Complete original-set evidence (0–100%)</text>']
    from html import escape
    for index, row in enumerate(rows):
        y = 45 + index * 18
        p99 = row.get("cadence_ms", {}).get("p99")
        coverage = row.get("evidence", {}).get("complete_fraction")
        parts.append(f'<text x="10" y="{y}">{escape(row["run_id"])}</text>')
        if p99 is not None:
            parts.append(f'<rect x="415" y="{y-9}" width="{min(200,p99)*1.3:.3f}" height="8" fill="#376b9c"/><text x="690" y="{y}">{p99:.3f}</text>')
        if coverage is not None:
            parts.append(f'<rect x="760" y="{y-9}" width="{coverage*210:.3f}" height="8" fill="#34784d"/><text x="980" y="{y}">{coverage:.3f}</text>')
    parts.append('</g></svg>')
    Path(output).write_text("".join(parts), encoding="utf-8", newline="\n")


def analyze_series(series, output):
    series, output = Path(series), Path(output)
    if output.resolve() == series.resolve() or series.resolve() in output.resolve().parents:
        raise ValueError("derived outputs must be outside immutable series")
    prereg = strict_json((series / "preregistration.json").read_bytes())
    rows = []
    for registered in prereg["registry"]:
        path = series / "runs" / registered["run_id"]
        if (path / "manifest.json").exists():
            rows.append(analyze_run(path, registered))
        else:
            rows.append({"run_id": registered["run_id"], "status": "NOT_ATTEMPTED", "factors": registered})
    output.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "preregistration_sha256": file_hash(series / "preregistration.json"),
               "analysis_script_sha256": file_hash(__file__), "quantile_method": "linear interpolation rank (n-1)*p, external scalar sort",
               "memory_method": "frozen second half OLS and every-tenth Theil-Sen; bytes/epoch",
               "runs": rows}
    (output / "cycle6_runs.json").write_bytes(canonical(payload))
    with (output / "cycle6_runs.csv").open("w", encoding="utf-8", newline="") as stream:
        columns = ["run_id", "status", "p50_ms", "p90_ms", "p95_ms", "p99_ms", "max_ms", "misses_above_44ms", "complete_fraction", "partial_fraction", "persisted_cfr_fraction"]
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            cadence, evidence = row.get("cadence_ms", {}), row.get("evidence", {})
            value = {"run_id": row["run_id"], "status": row["status"],
                     "misses_above_44ms": cadence.get("missed_intervals_above_44ms")}
            value.update({key + "_ms": cadence.get(key) for key in ("p50", "p90", "p95", "p99", "max")})
            value.update({key: evidence.get(key) for key in ("complete_fraction", "partial_fraction", "persisted_cfr_fraction")})
            writer.writerow(value)
    write_figure(rows, output / "cycle6_cadence_coverage.svg")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("series")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = analyze_series(args.series, args.output)
    print(json.dumps({"runs": len(report["runs"]), "output": args.output}))
