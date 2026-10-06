"""Independent frozen Gate A grid, stream integrity, bounded replay/reduction.

Verification never edits the measured series. Failed and unattempted identities
remain visible. Replay executes archived code rather than the evolving worktree.
"""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys

from experiments.cycle6_analyze import ScalarStore, canonical, file_hash, json_lines, strict_json


def frozen_registry():
    rows = []
    for seed in (26001, 26002, 26003):
        block = []
        for mode in ("k0", "warm1", "warm2"):
            conditions = ("normal", "cpu", "memory", "storage") if mode == "k0" else (
                "normal", "delay120", "delay400", "capacity1", "cpu", "memory", "storage")
            for condition in conditions:
                block.append({"kind": "factorial", "seed": seed, "mode": mode,
                    "condition": condition, "load": condition if condition in ("cpu", "memory", "storage") else "normal",
                    "delay_s": .12 if condition == "delay120" else .4 if condition == "delay400" else 0., "fault": "control"})
        random.Random(626001 + seed).shuffle(block)
        rows.extend(block)
    for seed in (26101, 26102, 26103):
        for case in ("control", "preappend", "temporary", "sustained", "torn"):
            rows.append({"kind": "storage_fault", "seed": seed, "mode": "warm2", "condition": case,
                         "load": "normal", "delay_s": 0., "fault": case})
    rows.append({"kind": "continuous", "seed": 26201, "mode": "warm2", "condition": "normal",
                 "load": "normal", "delay_s": 0., "fault": "control"})
    for index, row in enumerate(rows):
        row.update(order=index, run_id=f"{row['kind']}-{row['seed']}-{row['mode']}-{row['condition']}")
    return rows


def safe_path(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if root not in path.parents or not path.is_file():
        raise ValueError(f"unsafe or missing artifact: {relative}")
    return path


def verify_registry(meta):
    rows = meta["registry"]
    if meta.get("smoke") is True:
        ids = [row.get("run_id") for row in rows]
        expected = ["smoke-normal", "smoke-storage", "smoke-torn"]
        if ids != expected or len(ids) != len(set(ids)):
            raise ValueError("disposable smoke registry mismatch")
        if hashlib.sha256(canonical(rows)).hexdigest() != meta["registry_sha256"]:
            raise ValueError("smoke registry hash mismatch")
        if set(meta.get("configs", {})) != set(expected) or set(meta.get("config_hashes", {})) != set(expected):
            raise ValueError("smoke configuration identity mismatch")
        for run_id in expected:
            config = meta["configs"][run_id]
            if (hashlib.sha256(canonical(config)).hexdigest() != meta["config_hashes"][run_id] or
                    config.get("duration_epochs") != 8 or config.get("warmup_epochs") != 1 or
                    config.get("experiment_name") != "cycle6-disposable-smoke"):
                raise ValueError("smoke configuration mismatch: " + run_id)
        return {"registered_runs": 3, "factor_counts": {"smoke": 3},
                "fresh_seeds": sorted(set(row["seed"] for row in rows)),
                "registry_identity": "VERIFIED_NON_EVIDENTIARY_SMOKE"}
    if rows != frozen_registry():
        raise ValueError("registry is not the exact preregistered 70-run ordered factorial/fault/continuous grid")
    ids = [row["run_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate run identity")
    if hashlib.sha256(canonical(rows)).hexdigest() != meta["registry_sha256"]:
        raise ValueError("registry hash mismatch")
    if set(meta["configs"]) != set(ids) or set(meta["config_hashes"]) != set(ids):
        raise ValueError("missing or extra configuration identity")
    for row in rows:
        config = meta["configs"][row["run_id"]]
        if hashlib.sha256(canonical(config)).hexdigest() != meta["config_hashes"][row["run_id"]]:
            raise ValueError("configuration hash mismatch")
        duration, warmup = ((10000, 500) if row["kind"] == "continuous" else
                            (200, 20) if row["kind"] == "storage_fault" else (500, 50))
        k = 0 if row["mode"] == "k0" else int(row["mode"][-1])
        expected = dict(experiment_name="cycle6-gate-a", random_seed=row["seed"], duration_epochs=duration,
                        warmup_epochs=warmup, horizon_ticks=6, shadow_count=k, mirror_count=int(k > 0),
                        execution_mode="asynchronous", production_period_s=.04, shadow_timeout_s=2.,
                        shadow_result_deadline_s=.3, max_shadow_slots=1 if row["condition"] == "capacity1" else 3,
                        max_pending_shadow_tasks=1 if row["condition"] == "capacity1" else 12,
                        max_pending_epochs=16, max_pending_shadow_bytes=16777216,
                        shadow_injected_delay_s=row["delay_s"], worker_mode="warm" if k else "cold", worker_max_tasks=100,
                        worker_max_lifetime_s=60., retention_completed_epochs=64,
                        evidence_spool_max_items=256, evidence_spool_max_bytes=16777216,
                        evidence_spool_max_attempts=3, evidence_spool_drain_s=1., learning_enabled=False,
                        failure_scenario="none", shadow_load="normal", backend="local")
        for key, value in expected.items():
            if config.get(key) != value:
                raise ValueError(f"factor/config mismatch {row['run_id']}:{key}")
    return {"registered_runs": len(rows), "factor_counts": dict(Counter(row["kind"] for row in rows)),
            "fresh_seeds": sorted(set(row["seed"] for row in rows)), "registry_identity": "VERIFIED"}


def verify_bounds(record, config):
    """Check directly measured item/byte occupancy and high-water values."""
    pairs = (("physical_queue_depth", "max_pending_shadow_tasks"),
             ("physical_inflight_tasks", "max_pending_shadow_tasks"),
             ("physical_high_water_queue_depth", "max_pending_shadow_tasks"),
             ("physical_high_water_inflight_tasks", "max_pending_shadow_tasks"),
             ("physical_queue_bytes", "max_pending_shadow_bytes"),
             ("physical_inflight_bytes", "max_pending_shadow_bytes"),
             ("physical_high_water_queue_bytes", "max_pending_shadow_bytes"),
             ("physical_high_water_inflight_bytes", "max_pending_shadow_bytes"),
             ("evidence_spool_items", "evidence_spool_max_items"),
             ("evidence_spool_high_water_items", "evidence_spool_max_items"),
             ("evidence_spool_bytes", "evidence_spool_max_bytes"),
             ("evidence_spool_high_water_bytes", "evidence_spool_max_bytes"),
             ("pending_epochs", "max_pending_epochs"),
             ("retained_completed_epochs", "retention_completed_epochs"),
             ("duplicate_cache_size", "retention_completed_epochs"))
    for metric, limit in pairs:
        value = record.get(metric)
        if type(value) is not int or not 0 <= value <= config[limit]:
            raise ValueError(f"missing/invalid/exceeded measured bound: {metric}")
    if record["physical_task_capacity"] != config["max_pending_shadow_tasks"] or record["physical_byte_capacity"] != config["max_pending_shadow_bytes"]:
        raise ValueError("reported physical capacity disagrees with config")
    if record["physical_queue_bytes"] + record["physical_running_bytes"] != record["physical_inflight_bytes"]:
        raise ValueError("physical byte accounting inconsistent")
    if record["physical_queue_depth"] + record["physical_running_tasks"] != record["physical_inflight_tasks"]:
        raise ValueError("physical item accounting inconsistent")


def ordered_coverage(path, duration, *, required_complete=True, expected_status=None):
    expected = 0
    for row in json_lines(path):
        if type(row.get("epoch")) is not int or row["epoch"] != expected or expected >= duration:
            raise ValueError(f"missing/duplicate/out-of-order epoch in {Path(path).name}")
        if expected_status and row.get("status") != expected_status:
            raise ValueError("invalid production commit status")
        expected += 1
    if required_complete and expected != duration:
        raise ValueError(f"missing production epochs: {duration-expected}")
    return expected


def regenerated_summary(path, warmup):
    """Independent legacy summary semantics; missing CFR denominator is explicit elsewhere."""
    store = ScalarStore()
    timing = ("capture_ms", "production_decision_ms", "branch_creation_ms", "barrier_ms", "comparison_ms",
              "reset_ms", "epoch_ms", "coordinator_cpu_ms", "worker_cpu_ms", "payload_bytes", "coordinator_python_peak_bytes")
    epochs = complete = excluded = throughput = waiting = beaten = alternatives = 0
    def legacy(name):
        d = store.distribution(name)
        return {"n": d["n"], "median": d["p50"], "p95": d["p95"], "p99": d["p99"],
                "iqr": store.quantile(name, .75) - store.quantile(name, .25) if d["n"] else None}
    try:
        for record in json_lines(Path(path) / "cfr.jsonl", optional=True):
            epoch = record["epoch"]
            if epoch < warmup:
                continue
            epochs += 1
            complete += record["record_status"] == "COMPLETE"
            excluded += len(record["missing"])
            for field in ("u_real", "epsilon", "regret_raw", "regret_discounted"):
                store.add(field, epoch, record.get(field))
            if record.get("regret_discounted") is not None:
                alternatives += 1
                beaten += record["regret_discounted"] > 0
            production = record["branches"][0]["metrics"]
            throughput += production["throughput"]
            waiting += production["waiting_vehicle_ticks"]
        for record in json_lines(Path(path) / "resource_metrics.jsonl"):
            if record["epoch"] >= warmup:
                for field in timing:
                    store.add(field, record["epoch"], record.get(field))
        return {"epochs_measured": epochs, "production_utility": legacy("u_real"), "fidelity_gap": legacy("epsilon"),
                "regret_raw": legacy("regret_raw"), "regret_discounted": legacy("regret_discounted"),
                "beaten_rate": beaten / alternatives if alternatives else None,
                "complete_fraction": complete / epochs if epochs else None,
                "excluded_branches": excluded, "throughput": throughput, "waiting_vehicle_ticks": waiting,
                "timing": {field: legacy(field) for field in timing}}
    finally:
        store.close()


def assert_equal(actual, expected, location="summary"):
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise ValueError(location + ": wrong type")
        for key, value in expected.items():
            if key not in actual:
                raise ValueError(location + ": missing " + key)
            assert_equal(actual[key], value, location + "." + key)
    elif type(expected) is float:
        if type(actual) not in (int, float) or not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-9):
            raise ValueError(location + ": numeric mismatch")
    elif actual != expected:
        raise ValueError(location + ": mismatch")


def replay_run(run_path, source_root):
    """Disk-index input windows; replay one outcome at a time with archived code."""
    from csc.branches import execute_shadow
    from csc.contracts import Anchor, Config, Event
    from csc.world import ProductionWorld
    import csc
    if Path(csc.__file__).resolve().parent.parent != Path(source_root).resolve():
        raise ValueError("replay must execute the archived CSC source, not worktree imports")
    path = Path(run_path)
    manifest = strict_json((path / "manifest.json").read_bytes())
    config = Config(**manifest["config"])
    store = ScalarStore()
    db = store.db
    db.execute("CREATE TABLE inputs(epoch INTEGER PRIMARY KEY,anchor TEXT,events TEXT,production TEXT)")
    db.execute("CREATE TABLE replayed(bid TEXT PRIMARY KEY,identity TEXT)")
    checked = 0
    production_digest, workload_digest = hashlib.sha256(), hashlib.sha256()
    try:
        anchors = iter(json_lines(path / "anchors.jsonl"))
        event_groups = iter(itertools.groupby(json_lines(path / "events.jsonl"), key=lambda e: e["epoch"]))
        for commit in json_lines(path / "epoch_journal.jsonl"):
            envelope = next(anchors)
            epoch, event_iterator = next(event_groups)
            events = list(event_iterator)
            anchor = Anchor.from_envelope(envelope)
            if epoch != commit["epoch"] or anchor.snapshot_id != commit["anchor_hash"] or len(events) != config.horizon_ticks:
                raise ValueError("anchor/window/production identity mismatch")
            for event in events:
                raw = dict(event)
                raw.pop("experiment_id")
                workload_digest.update(canonical(raw))
            branch = commit["production"]
            capability = object()
            world = ProductionWorld(anchor.hydrate(), capability, config)
            world.apply_plan(branch["action"], capability, "replay-only")
            trace = [world.step(Event(**event), tick) for tick, event in enumerate(events)]
            if trace != branch["trace"] or asdict(world.snapshot_state()) != branch["final_state"]:
                raise ValueError("authoritative production replay mismatch")
            production_digest.update(canonical({"action": branch["action"], "trace": trace, "state": asdict(world.snapshot_state())}))
            db.execute("INSERT INTO inputs VALUES(?,?,?,?)", (epoch, json.dumps(envelope), json.dumps(events), json.dumps(branch)))
            checked += 1
        if next(anchors, None) is not None or next(event_groups, None) is not None:
            raise ValueError("extra anchor/event epochs")
        shadow_config = dict(manifest["config"], shadow_injected_delay_s=0.)
        def branch_check(branch):
            nonlocal checked
            if branch["role"] == "PRODUCTION":
                raw = db.execute("SELECT production FROM inputs WHERE epoch=?", (branch["epoch"],)).fetchone()
                if raw is None:
                    raise ValueError("outcome missing production commit")
                expected = json.loads(raw[0])
                for field in ("trace", "final_state", "synchronization", "action", "branch_id"):
                    if expected[field] != branch[field]:
                        raise ValueError("optional production evidence changed committed authority")
                return
            if branch["status"] != "REPORTED" or not branch.get("synchronization", {}).get("comparable"):
                return
            identity = hashlib.sha256(canonical({field: branch[field] for field in ("trace", "final_state", "action", "role", "epoch")})).hexdigest()
            prior = db.execute("SELECT identity FROM replayed WHERE bid=?", (branch["branch_id"],)).fetchone()
            if prior:
                if prior[0] != identity:
                    raise ValueError("duplicate branch outcome disagrees")
                return
            raw = db.execute("SELECT anchor,events FROM inputs WHERE epoch=?", (branch["epoch"],)).fetchone()
            if raw is None:
                raise ValueError("outcome references unknown epoch")
            request = {"anchor": json.loads(raw[0]), "events": json.loads(raw[1]), "config": shadow_config,
                       "branch": {key: branch[key] for key in ("branch_id", "experiment_id", "epoch", "role", "action", "parent_snapshot_id", "start_sequence", "end_sequence")}}
            outcome = execute_shadow(request)
            if outcome["trace"] != branch["trace"] or outcome["final_state"] != branch["final_state"]:
                raise ValueError("counterfactual replay mismatch")
            db.execute("INSERT INTO replayed VALUES(?,?)", (branch["branch_id"], identity))
            checked += 1
        for record in json_lines(path / "cfr.jsonl", optional=True):
            for branch in record["branches"]:
                branch_check(branch)
        for branch in json_lines(path / "branch_metrics.jsonl", optional=True):
            branch_check(branch)
        summary = strict_json((path / "summary.json").read_bytes())
        if summary["production_semantic_sha256"] != production_digest.hexdigest() or summary["workload_sha256"] != workload_digest.hexdigest():
            raise ValueError("replayed production/workload hash mismatch")
        return {"branches_replayed": checked, "trajectory_mismatches": 0, "production_hash": production_digest.hexdigest(), "workload_hash": workload_digest.hexdigest()}
    finally:
        store.close()


def verify_run(path, expected_config, config_hash, source_hashes, complete=True):
    path = Path(path)
    manifest = strict_json((path / "manifest.json").read_bytes())
    if manifest["config"] != expected_config or manifest["config_hash"] != config_hash:
        raise ValueError("run frozen config mismatch")
    if hashlib.sha256(canonical(manifest["config"])).hexdigest() != config_hash:
        raise ValueError("run config self-hash mismatch")
    if not manifest.get("source_hashes"):
        raise ValueError("missing runtime source identity")
    mandatory_runtime = ("__init__", "contracts", "branches", "world", "safety", "sync", "compare", "store", "runner", "pending", "async_runner", "worker", "warm", "os_metrics", "executor")
    if set(manifest["source_hashes"]) != {f"csc/{name}.py" for name in mandatory_runtime}:
        raise ValueError("runtime source dependency closure incomplete or changed")
    for name, digest in manifest["source_hashes"].items():
        if source_hashes.get(name) != digest:
            raise ValueError("run/archive source mismatch: " + name)
    artifact_names = {p.name for p in path.iterdir() if p.is_file() and p.name != "manifest.json"}
    if set(manifest.get("artifact_hashes", {})) != artifact_names:
        raise ValueError("unhashed/missing run artifact")
    for name, digest in manifest["artifact_hashes"].items():
        if file_hash(safe_path(path, name)) != digest:
            raise ValueError("artifact hash mismatch: " + name)
    if complete and manifest["status"] != "COMPLETE":
        raise ValueError("campaign and native completion status disagree")
    duration = expected_config["duration_epochs"]
    if complete:
        for name in ("anchors.jsonl", "events.jsonl", "epoch_journal.jsonl", "resource_metrics.jsonl", "lifecycle.jsonl", "safety_events.jsonl", "environment_audit.jsonl", "logs.jsonl", "summary.json"):
            if not (path / name).is_file():
                raise ValueError("required production/control artifact missing: " + name)
    covered = ordered_coverage(path / "epoch_journal.jsonl", duration,
                               required_complete=complete, expected_status="PRODUCTION_COMMITTED")
    ordered_coverage(path / "resource_metrics.jsonl", duration, required_complete=complete)
    for resource in json_lines(path / "resource_metrics.jsonl"):
        verify_bounds(resource, expected_config)
    # Validate every stream even when it does not enter summary/replay.
    counts = {p.name: sum(1 for _ in json_lines(p)) for p in sorted(path.glob("*.jsonl"))}
    persistence = manifest.get("evidence_persistence", {})
    for key, limit in (("evidence_spool_high_water_items", "evidence_spool_max_items"), ("evidence_spool_high_water_bytes", "evidence_spool_max_bytes")):
        if persistence.get(key, 0) > expected_config[limit]:
            raise ValueError("manifest spool high-water bound exceeded")
    summary_path = path / "summary.json"
    summary = strict_json(summary_path.read_bytes()) if summary_path.exists() else {}
    if summary.get("unauthorized_production_mutations_from_shadow", 0) != 0:
        raise ValueError("unauthorized production mutation")
    if complete:
        verify_authority_and_evidence(path, expected_config)
        assert_equal(summary, regenerated_summary(path, expected_config["warmup_epochs"]))
        if summary.get("authoritative_commands_observed") != duration:
            raise ValueError("authoritative command coverage mismatch")
    return {"run_id": manifest["experiment_id"], "status": manifest["status"], "production_epochs": covered,
            "jsonl_counts": counts, "summary_regeneration": "VERIFIED" if complete else "NOT_REQUIRED_FOR_FAILED_ATTEMPT",
            "production_hash": summary.get("production_semantic_sha256"), "workload_hash": summary.get("workload_sha256")}


def verify_authority_and_evidence(path, config):
    """Audit authoritative commands and finalized availability independently."""
    path = Path(path)
    store = ScalarStore()
    db = store.db
    db.execute("CREATE TABLE commits(epoch INTEGER PRIMARY KEY, bid TEXT, action TEXT, final TEXT)")
    db.execute("CREATE TABLE delivery(rid TEXT PRIMARY KEY,status TEXT,stream TEXT)")
    try:
        for row in json_lines(path / "epoch_journal.jsonl"):
            branch = row["production"]
            if row["input_hash"] != branch["synchronization"]["input_hash"] or branch["role"] != "PRODUCTION" or branch["provenance"] != "REALISED":
                raise ValueError("committed production identity invalid")
            planned = row["branches"]
            mirrors = [b for b in planned if b["role"] == "MIRROR"]
            alternatives = [b for b in planned if b["role"] == "SHADOW"]
            if len(mirrors) != config["mirror_count"] or len(alternatives) != config["shadow_count"] or len({b["action"] for b in alternatives}) != config["shadow_count"]:
                raise ValueError("original requested branch set disagrees with frozen K")
            if any(b["action"] == branch["action"] for b in alternatives) or any(b["action"] != branch["action"] for b in mirrors):
                raise ValueError("mirror/alternative action identities invalid")
            db.execute("INSERT INTO commits(epoch,bid,action) VALUES(?,?,?)", (row["epoch"], branch["branch_id"], branch["action"]))
        commands = 0
        for row in json_lines(path / "environment_audit.jsonl"):
            expected = db.execute("SELECT bid,action FROM commits WHERE epoch=?", (row["epoch"],)).fetchone()
            if row["epoch"] != commands or expected is None or row["action"] != expected[1] or row["correlation_id"] != f"{row['experiment_id']}:{row['epoch']}:{expected[0]}":
                raise ValueError("unauthorized/missing/duplicate authoritative mutation")
            commands += 1
        if commands != config["duration_epochs"]:
            raise ValueError("authoritative audit coverage mismatch")
        finalized = 0
        for row in json_lines(path / "lifecycle.jsonl"):
            if row.get("status") != "FINALIZED":
                continue
            epoch = row["epoch"]
            expected = db.execute("SELECT final FROM commits WHERE epoch=?", (epoch,)).fetchone()
            if expected is None or expected[0] is not None:
                raise ValueError("duplicate/unknown finalized epoch")
            k, admitted, completed = row["requested_k"], row["admitted_k"], row["completed_k"]
            if any(type(value) is not int for value in (k, admitted, completed)) or k != config["shadow_count"] or not 0 <= completed <= admitted <= k:
                raise ValueError("requested/admitted/completed K accounting invalid")
            if row["evidence_completeness"] == "COMPLETE_COMPARISON" and (not row["mirror_accepted"] or completed != k or row["missing_count"] != 0):
                raise ValueError("complete evidence hides original-set incompleteness")
            db.execute("UPDATE commits SET final=? WHERE epoch=?", (json.dumps(row), epoch))
            finalized += 1
        if finalized != config["duration_epochs"]:
            raise ValueError("missing finalized availability accounting")
        for row in json_lines(path / "evidence_delivery.jsonl", optional=True):
            if row["status"] not in ("PERSISTED", "FAILED", "UNAVAILABLE") or type(row["attempts"]) is not int or not 0 <= row["attempts"] <= config["evidence_spool_max_attempts"]:
                raise ValueError("invalid persistence terminal/attempt accounting")
            db.execute("INSERT INTO delivery VALUES(?,?,?)", (row["record_id"], row["status"], row["stream"]))
        for row in json_lines(path / "cfr.jsonl", optional=True):
            raw = db.execute("SELECT final FROM commits WHERE epoch=?", (row["epoch"],)).fetchone()
            if raw is None or raw[0] is None:
                raise ValueError("CFR references unknown/unfinalized epoch")
            final = json.loads(raw[0])
            for key in ("requested_k", "admitted_k", "completed_k", "evidence_completeness"):
                if row[key] != final[key]:
                    raise ValueError("CFR/finalized availability mismatch")
            rid = f"epoch:{row['epoch']}:comparison"
            delivered = db.execute("SELECT status,stream FROM delivery WHERE rid=?", (rid,)).fetchone()
            if delivered != ("PERSISTED", "cfr.jsonl"):
                raise ValueError("persisted CFR lacks delivery confirmation")
        for row in json_lines(path / "branch_metrics.jsonl", optional=True):
            rid = f"epoch:{row['epoch']}:branch:{row['branch_id']}"
            delivered = db.execute("SELECT status,stream FROM delivery WHERE rid=?", (rid,)).fetchone()
            if delivered != ("PERSISTED", "branch_metrics.jsonl"):
                raise ValueError("persisted branch lacks delivery confirmation")
    finally:
        store.close()


def verify_series(series, replay=False):
    series = Path(series).resolve()
    meta = strict_json((series / "preregistration.json").read_bytes())
    result = verify_registry(meta)
    source_hashes = meta["source_hashes"]
    if hashlib.sha256(canonical(source_hashes)).hexdigest() != meta["source_identity_sha256"]:
        raise ValueError("closure identity mismatch")
    for name, digest in source_hashes.items():
        if file_hash(safe_path(series / "source", name)) != digest:
            raise ValueError("closure file mismatch: " + name)
    for required in ("experiments/cycle6_campaign.py", "experiments/cycle6_analyze.py", "experiments/cycle6_verify.py", "experiments/cycle6_pressure.py", "experiments/cycle6_faults.py", "research/cycle6/PROTOCOL.md", "research/cycle6/PREFLIGHT_REVIEW.md", "Dockerfile", "gates/readiness/manifest.json"):
        if required not in source_hashes:
            raise ValueError("required closure member missing: " + required)
    if meta["protocol_sha256"] != source_hashes["research/cycle6/PROTOCOL.md"]:
        raise ValueError("protocol identity mismatch")
    gate = strict_json((series / "source/gates/readiness/manifest.json").read_bytes())
    if gate.get("gate_passed") is not True or gate.get("exit_code") != 0:
        raise ValueError("archived correctness gate failed")
    if file_hash(series / "source/gates/readiness/manifest.json") != meta["correctness_gate_manifest_sha256"]:
        raise ValueError("gate manifest identity mismatch")
    for name, digest in gate["source_hashes"].items():
        if name.startswith("csc/") and source_hashes.get(name) != digest:
            raise ValueError("readiness gate does not cover collected runtime")
    statuses = strict_json((series / "execution_status.json").read_bytes())
    ids = [r["run_id"] for r in meta["registry"]]
    if [s["run_id"] for s in statuses] != ids:
        raise ValueError("execution identity duplicate/missing/order mismatch")
    extra_dirs = {p.name for p in (series / "runs").iterdir() if p.is_dir()} - set(ids) if (series / "runs").exists() else set()
    if extra_dirs:
        raise ValueError("unregistered/replacement run directories: " + repr(sorted(extra_dirs)))
    series_manifest = strict_json((series / "series_manifest.json").read_bytes())
    artifact_hashes = series_manifest["artifact_hashes"]
    actual_files = {p.relative_to(series).as_posix() for p in series.rglob("*") if p.is_file() and p.name != "series_manifest.json" and "__pycache__" not in p.parts}
    if set(artifact_hashes) != actual_files:
        raise ValueError("unhashed/missing series artifact")
    for name, digest in artifact_hashes.items():
        if file_hash(safe_path(series, name)) != digest:
            raise ValueError("series artifact hash mismatch: " + name)
    checks, paired = [], {}
    for row, execution in zip(meta["registry"], statuses):
        run_id, status = row["run_id"], execution["status"]
        path = series / "runs" / run_id
        if status not in ("COMPLETE", "FAILED", "NOT_ATTEMPTED"):
            raise ValueError("unfinished/invalid scheduled status")
        if status == "NOT_ATTEMPTED":
            if path.exists():
                raise ValueError("unattempted identity has run artifacts")
            checks.append({"run_id": run_id, "status": status})
            continue
        if status == "FAILED" and not path.exists():
            # Pre-child launch failure still retains launcher error/stdout/status.
            if not execution.get("error"):
                raise ValueError("failed attempt has neither artifact directory nor failure evidence")
            checks.append({"run_id": run_id, "status": status, "failure_evidence": "launcher status retained"})
            continue
        check = verify_run(path, meta["configs"][run_id], meta["config_hashes"][run_id], source_hashes, status == "COMPLETE")
        if status == "COMPLETE":
            cleanup = strict_json((series / "run_control" / run_id / "cleanup.json").read_bytes())
            if cleanup.get("cleanup_confirmed") is not True or execution.get("return_code") != 0:
                raise ValueError("completed run ownership/exit unconfirmed")
            pair = (check["production_hash"], check["workload_hash"])
            if None in pair or (row["seed"] in paired and paired[row["seed"]] != pair):
                raise ValueError("paired seed production/workload identity mismatch")
            paired[row["seed"]] = pair
            if replay:
                env = dict(os.environ, PYTHONPATH=str(series / "source"), PYTHONDONTWRITEBYTECODE="1")
                process = subprocess.run([sys.executable, "-m", "experiments.cycle6_verify", "--replay-run", str(path), "--source-root", str(series / "source")],
                                         cwd=series / "source", env=env, capture_output=True, text=True, timeout=300)
                if process.returncode:
                    raise ValueError("archived replay failed: " + process.stderr[-2000:])
                check["replay"] = strict_json(process.stdout)
        checks.append(check)
    result.update(status="VERIFIED", attempt_counts=dict(Counter(s["status"] for s in statuses)),
                  checks=checks, failed_attempts_preserved=True, paired_seed_count=len(paired),
                  replay_status="VERIFIED_FOR_COMPLETE_RUNS" if replay else "NOT_EXECUTED",
                  source_identity_sha256=meta["source_identity_sha256"], verifier_sha256=file_hash(__file__))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("series", nargs="?")
    parser.add_argument("--output")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--replay-run")
    parser.add_argument("--source-root")
    args = parser.parse_args()
    if args.replay_run:
        print(json.dumps(replay_run(args.replay_run, args.source_root)))
    else:
        if not args.series or not args.output:
            parser.error("series and --output are required")
        target = Path(args.output).resolve()
        if target == Path(args.series).resolve() or Path(args.series).resolve() in target.parents:
            raise ValueError("verification output must be outside immutable series")
        result = verify_series(args.series, args.replay)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(canonical(result))
        print(json.dumps({key: result[key] for key in ("status", "registered_runs", "attempt_counts", "replay_status")}))
