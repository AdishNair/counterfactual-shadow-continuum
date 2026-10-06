"""Frozen local async driver, raw-artifact reduction, replay and provenance verifier."""
import argparse
import csv
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shutil
import statistics
import subprocess
import sys

from csc.contracts import Config, canonical, digest
from csc.runner import distribution, run, summarize
from experiments.replay import replay, read_lines, sha256_file

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [f"csc/{n}.py" for n in ("__init__", "contracts", "branches", "world", "safety", "sync", "compare", "store", "runner", "pending", "async_runner", "worker")]
SOURCES += ["experiments/cycle4_async.py", "experiments/replay.py", "tests/test_async.py", "research/evidence/cycle4/cycle4_async_protocol.md"]
SOURCES += ["experiments/cycle4_async_invariants.py"]
CONDITIONS = ("normal", "moderate", "severe", "timeout", "crash", "saturation")
MODES = ("k0", "sync1", "sync2", "async1", "async2")


def configuration(seed, mode, condition):
    k = 0 if mode == "k0" else int(mode[-1])
    delay = {"moderate": .04, "severe": .12, "saturation": .12, "occupancy": .12}.get(condition, 0)
    return Config(experiment_name="cycle4-async", random_seed=seed, duration_epochs=12, warmup_epochs=2,
                  horizon_ticks=6, shadow_count=k, mirror_count=int(k > 0), max_shadow_slots=3,
                  execution_mode="asynchronous" if mode.startswith("async") else "synchronous",
                  production_period_s=.04, shadow_timeout_s=.6, shadow_result_deadline_s=.3,
                  max_pending_shadow_tasks=3 if condition in ("saturation", "occupancy") else 12,
                  shadow_injected_delay_s=delay, failure_epoch=4,
                  failure_scenario=condition if condition in ("timeout", "crash") else "none",
                  shadow_load=condition if condition in ("cpu", "memory") else "normal")


def expected_registry():
    primary = [dict(kind="primary", seed=s, mode=m, condition=c) for s in range(901, 906) for m in MODES for c in CONDITIONS]
    random.Random(4901).shuffle(primary)
    micro = [dict(kind="micro", seed=s, mode="async2", condition=c) for s in range(906, 909) for c in ("normal", "cpu", "memory", "occupancy")]
    random.Random(4902).shuffle(micro)
    for index, row in enumerate(primary + micro):
        row["run_id"] = f"{row['kind']}-{row['seed']}-{row['mode']}-{row['condition']}"
        row["order"] = index
    return primary + micro


def execute(series):
    series = Path(series)
    series.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for name in SOURCES:
        target = series / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
        hashes[name] = sha256_file(target)
    registry = expected_registry()
    metadata = dict(protocol_sha256=hashes["research/evidence/cycle4/cycle4_async_protocol.md"], source_hashes=hashes,
                    runtime=dict(python=platform.python_version(), platform=platform.platform(), dependencies="standard library; matplotlib optional derived plotting"),
                    analysis_script_sha256=hashes["experiments/cycle4_async.py"], seed_blocks=[901, 905, 906, 908],
                    selector_version="NOT_APPLICABLE_SYSTEMS_TRACK", registry=registry,
                    started_utc=datetime.now(timezone.utc).isoformat())
    (series / "preregistration.json").write_bytes(canonical(metadata))
    for index, row in enumerate(registry):
        for name in SOURCES:
            if sha256_file(ROOT / name) != hashes[name]:
                raise RuntimeError("source changed after freeze: " + name)
        config = configuration(row["seed"], row["mode"], row["condition"])
        run(config, series / "runs", row["run_id"])
        print(f"{index + 1}/{len(registry)} {row['run_id']}", flush=True)
    # Evidence is all terminal before reduction, preventing summary/worker races.
    report = analyze(series)
    (series / "analysis.json").write_bytes(canonical(report))
    metadata["ended_utc"] = datetime.now(timezone.utc).isoformat()
    metadata["artifact_hashes"] = {str(p.relative_to(series)).replace('\\', '/'): sha256_file(p) for p in sorted(series.rglob('*')) if p.is_file() and p.name != "series_manifest.json"}
    (series / "series_manifest.json").write_bytes(canonical(metadata))
    return report


def reduce_run(path, row):
    manifest = json.loads((path / "manifest.json").read_text())
    config = Config(**manifest["config"])
    resources = list(read_lines(path / "resource_metrics.jsonl"))[config.warmup_epochs:]
    records = list(read_lines(path / "cfr.jsonl"))[config.warmup_epochs:]
    branches = [b for r in records for b in r["branches"] if b["role"] != "PRODUCTION"]
    lifecycle = list(read_lines(path / "lifecycle.jsonl")) if (path / "lifecycle.jsonl").exists() else []
    if config.execution_mode == "asynchronous":
        worker_runtimes = [e["worker_runtime"] for e in lifecycle if e.get("epoch", -1) >= config.warmup_epochs and e.get("status") in ("COMPLETED", "FAILED", "TIMED_OUT", "LATE") and "worker_runtime" in e]
    else:
        worker_runtimes = [b.get("runtime", {}) for b in branches]
    intervals = [r["production_interval_ms"] for r in resources if r.get("production_interval_ms") is not None]
    complete = sum(r["record_status"] == "COMPLETE" and len(r["branches"]) > 1 for r in records)
    partial = sum(r["record_status"] == "PARTIAL" for r in records)
    result = dict(**row, production_interval_ms=distribution(intervals),
                  production_decision_ms=distribution([r["production_decision_ms"] for r in resources]),
                  epoch_execution_ms=distribution([r["epoch_ms"] for r in resources]),
                  comparison_completion_ms=distribution([r.get("comparison_completion_ms") for r in records] if config.execution_mode == "asynchronous" else [r["branch_creation_ms"] + r["barrier_ms"] + r["comparison_ms"] for r in resources]),
                  branch_completion_ms=distribution([e.get("branch_completion_ms") for e in lifecycle if e.get("epoch", -1) >= config.warmup_epochs and e.get("status") in ("COMPLETED", "FAILED", "TIMED_OUT", "LATE")] if config.execution_mode == "asynchronous" else [runtime.get("dispatch_roundtrip_ms") for runtime in worker_runtimes]),
                  complete_fraction=complete / len(records), partial_fraction=partial / len(records),
                  production_only_fraction=sum(r["record_status"] == "PRODUCTION_ONLY" for r in records) / len(records),
                  branch_status_counts=dict(Counter(b["status"] for b in branches)),
                  late_target_intervals=sum(i > config.production_period_s * 1000 for i in intervals),
                  missed_epoch_count=config.duration_epochs - len(list(read_lines(path / "cfr.jsonl"))),
                  coordinator_cpu_ms=distribution([r["coordinator_cpu_ms"] for r in resources]),
                  worker_cpu_ms=distribution([runtime.get("cpu_ms") for runtime in worker_runtimes]),
                  coordinator_python_peak_bytes=max(r["coordinator_python_peak_bytes"] for r in resources),
                  worker_rss_available=any(runtime.get("peak_rss_bytes") is not None for runtime in worker_runtimes),
                  observed_worker_pids=len({runtime["pid"] for runtime in worker_runtimes if "pid" in runtime}),
                  serialized_bytes=sum(runtime.get("request_bytes", 0) + runtime.get("response_bytes", 0) for runtime in worker_runtimes),
                  max_active=max((r.get("active_shadow_tasks", 0) for r in resources), default=0),
                  max_queued=max((r.get("queued_shadow_tasks", 0) for r in resources), default=0),
                  max_running=max((r.get("running_shadow_tasks", 0) for r in resources), default=0),
                  saturation_events=sum(e["status"] == "DROPPED" for e in lifecycle) // max(1, config.shadow_count + config.mirror_count),
                  evidence_bookkeeping_ms=distribution([r.get("evidence_bookkeeping_ms") for r in resources]))
    summary = json.loads((path / "summary.json").read_text())
    result.update(production_hash=summary["production_semantic_sha256"], workload_hash=summary["workload_sha256"],
                  production_failures=0 if manifest["status"] == "COMPLETE" else 1,
                  unauthorized_mutations=summary["unauthorized_production_mutations_from_shadow"])
    return result


def analyze(series):
    series = Path(series)
    registry = json.loads((series / "preregistration.json").read_text())["registry"]
    runs = [reduce_run(series / "runs" / r["run_id"], r) for r in registry]
    groups = []
    for kind in ("primary", "micro"):
        for mode in MODES:
            for condition in CONDITIONS + ("cpu", "memory", "occupancy"):
                rows = [r for r in runs if (r["kind"], r["mode"], r["condition"]) == (kind, mode, condition)]
                if not rows:
                    continue
                normal = {r["seed"]: r for r in runs if (r["kind"], r["mode"], r["condition"]) == (kind, mode, "normal")}
                effects = [r["production_interval_ms"]["median"] - normal[r["seed"]]["production_interval_ms"]["median"] for r in rows]
                groups.append(dict(kind=kind, mode=mode, condition=condition, seeds=len(rows),
                    interval_ms=distribution([r["production_interval_ms"]["median"] for r in rows]),
                    decision_ms=distribution([r["production_decision_ms"]["median"] for r in rows]),
                    complete_fraction=distribution([r["complete_fraction"] for r in rows]),
                    partial_fraction=distribution([r["partial_fraction"] for r in rows]),
                    paired_interval_effect_ms=effects, paired_effect_median_ms=statistics.median(effects),
                    paired_effect_range_ms=[min(effects), max(effects)],
                    expired=sum(r["branch_status_counts"].get("EXPIRED", 0) for r in rows),
                    dropped=sum(r["branch_status_counts"].get("DROPPED", 0) for r in rows),
                    failures=sum(r["production_failures"] for r in rows)))
    return dict(runs=runs, groups=groups, experimental_unit="paired seed/run; epochs are repeated observations",
                quantiles="linear interpolation; per-run p95/p99 descriptive with ten measured epochs")


def verify(series, output):
    series = Path(series).resolve()
    output = Path(output).resolve()
    archived_script = series / "source/experiments/cycle4_async.py"
    if Path(__file__).resolve() != archived_script:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(series / "source")
        proc = subprocess.run([sys.executable, "-m", "experiments.cycle4_async", "verify", str(series), "--output", str(output)],
                              cwd=series / "source", env=env, capture_output=True, text=True, check=True)
        return json.loads(output.read_text())
    meta = json.loads((series / "series_manifest.json").read_text())
    failures = []
    for name, hash_value in meta["artifact_hashes"].items():
        if sha256_file(series / name) != hash_value:
            failures.append("artifact_hash:" + name)
    if meta["registry"] != expected_registry():
        failures.append("registry")
    actual = {p.name for p in (series / "runs").iterdir()}
    if actual != {r["run_id"] for r in meta["registry"]}:
        failures.append("run_set")
    replayed = 0
    for row in meta["registry"]:
        path = series / "runs" / row["run_id"]
        manifest = json.loads((path / "manifest.json").read_text())
        if manifest["config"] != asdict(configuration(row["seed"], row["mode"], row["condition"])):
            failures.append("config:" + row["run_id"])
        if manifest["config_hash"] != digest(manifest["config"]):
            failures.append("config_hash:" + row["run_id"])
        result = replay(path, series / "source")
        replayed += result["branches_replayed"]
        records = list(read_lines(path / "cfr.jsonl"))
        summary = json.loads((path / "summary.json").read_text())
        resources = list(read_lines(path / "resource_metrics.jsonl"))
        recomputed_summary = summarize(records[2:], resources[2:])
        if any(summary.get(k) != v for k, v in recomputed_summary.items()):
            failures.append("run_summary_regeneration:" + row["run_id"])
        if row["mode"].startswith("async"):
            if any(r["active_shadow_tasks"] > manifest["config"]["max_pending_shadow_tasks"] or r["pending_epochs"] > 16 for r in resources):
                failures.append("capacity:" + row["run_id"])
        if [r["epoch"] for r in records] != list(range(12)):
            failures.append("epochs:" + row["run_id"])
        if row["mode"].startswith("async") and any(r["missing"] and r["regret_raw"] is not None for r in records):
            failures.append("incomplete_regret:" + row["run_id"])
        if manifest["status"] != "COMPLETE":
            failures.append("nonterminal:" + row["run_id"])
    regenerated = analyze(series)
    if regenerated != json.loads((series / "analysis.json").read_text()):
        failures.append("analysis_regeneration")
    for seed in range(901, 909):
        rows = [r for r in regenerated["runs"] if r["seed"] == seed]
        if len({r["production_hash"] for r in rows}) != 1 or len({r["workload_hash"] for r in rows}) != 1:
            failures.append("paired_trajectory:" + str(seed))
    verdict = dict(status="VERIFIED" if not failures else "FAILED", failures=failures, runs_verified=len(meta["registry"]),
                   branches_replayed=replayed, source_archive_hashes_verified=len(meta["source_hashes"]),
                   raw_summary_regeneration="MATCH" if "analysis_regeneration" not in failures else "FAIL",
                   replay_execution_source="ARCHIVED_SOURCE_BUNDLE", scope="Cycle 4 async only; no trust held-out access")
    Path(output).write_bytes(canonical(verdict))
    return verdict


def figures(series, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    report = analyze(series)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for mode in MODES:
        groups = [next(g for g in report["groups"] if (g["kind"], g["mode"], g["condition"]) == ("primary", mode, c)) for c in ("normal", "moderate", "severe")]
        axes[0].plot([0, 40, 120], [g["interval_ms"]["median"] for g in groups], marker="o", label=mode)
        axes[1].plot([0, 40, 120], [g["complete_fraction"]["median"] for g in groups], marker="o", label=mode)
    axes[0].set_ylabel("Production start-to-start interval (ms)")
    axes[1].set_ylabel("Epochs with complete comparison (fraction)")
    for ax in axes:
        ax.set_xlabel("Injected shadow delay (ms)")
        ax.legend()
        ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(directory / "cycle4_async_cadence_completeness.png", dpi=200)
    plt.close(fig)
    (directory / "cycle4_async_figure_metadata.json").write_bytes(canonical(dict(source_artifact=str(Path(series) / "analysis.json"),
       metric_definition="median of five seed-run medians; complete fraction reduced within each run", units="ms / fraction",
       seed_count=5, aggregation="within-run first, then seed medians", script_sha256=sha256_file(__file__), matplotlib_version=matplotlib.__version__)))


def render(series, output):
    report = analyze(series)
    lines = ["# Cycle 4 deterministic local async tables", "", "**Status:** Derived from one preregistered immutable series.", "",
             f"Source: `{Path(series) / 'analysis.json'}`. Units: ms and fractions; five paired seed-runs per primary group, three in the microstudy.", "",
             "Within-run medians are reduced before seed medians. Interval is production start-to-start; K excludes mirrors. Ten measured epochs make p95/p99 descriptive only.", "",
             "| Track | Mode | Condition | Median cadence ms | Paired change vs normal ms [range] | Complete fraction | Partial fraction | Expired | Dropped |", "|---|---|---|---:|---|---:|---:|---:|---:|"]
    for group in report["groups"]:
        lo, hi = group["paired_effect_range_ms"]
        lines.append(f"| {group['kind']} | {group['mode']} | {group['condition']} | {group['interval_ms']['median']:.3f} | {group['paired_effect_median_ms']:.3f} [{lo:.3f}, {hi:.3f}] | {group['complete_fraction']['median']:.3f} | {group['partial_fraction']['median']:.3f} | {group['expired']} | {group['dropped']} |")
    lines += ["", "K0 complete comparison fraction is zero by definition because no shadow evidence is planned, not a production failure.", "",
              "All five/three paired effects are preserved in `analysis.json`; no timing equivalence threshold is inferred.", "",
              "Sync branch completion is worker dispatch roundtrip; async is commit-to-coordinator acceptance, including queueing/poll delay. Sync comparison completion is branch creation + barrier + comparison duration; async is commit-to-finalization. Origins differ and absolute cross-mode completion comparisons are descriptive.", "",
              "| Mode | Condition | Decision ms | Run p95 interval ms (median across seeds) | Comparison ms | Branch ms | Coordinator CPU ms | Worker CPU ms | Serialized bytes | Max active | Max queued |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for group in report["groups"]:
        rows = [r for r in report["runs"] if (r["kind"], r["mode"], r["condition"]) == (group["kind"], group["mode"], group["condition"])]
        def med(field, sub="median"):
            values = [r[field][sub] for r in rows if r[field][sub] is not None]
            return f"{statistics.median(values):.3f}" if values else "unavailable"
        lines.append(f"| {group['mode']} | {group['condition']} | {med('production_decision_ms')} | {med('production_interval_ms', 'p95')} | {med('comparison_completion_ms')} | {med('branch_completion_ms')} | {med('coordinator_cpu_ms')} | {med('worker_cpu_ms')} | {statistics.median(r['serialized_bytes'] for r in rows):.0f} | {max(r['max_active'] for r in rows)} | {max(r['max_queued'] for r in rows)} |")
    lines += ["", "CPU zeros can reflect Windows process-time quantization; they do not show zero cost. Worker RSS is unavailable on this host; tracemalloc measures Python allocation, not process RSS. PID counts under-report timed-out/crashed workers.", "",
              "Production decision excludes evidence bookkeeping; cadence includes coordinator storage, comparison, polling and host scheduling. Local results do not establish resource non-interference, real-time safety, K3s containment or durable distributed restart."]
    Path(output).write_text("\n".join(lines) + "\n", encoding="utf-8")
    fields = ["kind", "seed", "mode", "condition", "median_cadence_ms", "p95_cadence_ms", "p99_cadence_ms", "complete_fraction", "partial_fraction", "late_target_intervals", "production_failures", "max_active", "max_queued"]
    with Path(output).with_suffix(".csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for r in report["runs"]:
            values = {k: r[k] for k in fields if k in r}
            values.update(median_cadence_ms=r["production_interval_ms"]["median"], p95_cadence_ms=r["production_interval_ms"]["p95"], p99_cadence_ms=r["production_interval_ms"]["p99"])
            writer.writerow(values)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("execute", "verify", "analyze", "figures", "render"))
    parser.add_argument("series")
    parser.add_argument("--output", default="research/tables/cycle4_async_verification.json")
    args = parser.parse_args()
    if args.command == "execute":
        execute(args.series)
    elif args.command == "verify":
        print(json.dumps(verify(args.series, args.output), indent=2))
    elif args.command == "figures":
        figures(args.series, args.output)
    elif args.command == "render":
        render(args.series, args.output)
    else:
        Path(args.output).write_bytes(canonical(analyze(args.series)))
