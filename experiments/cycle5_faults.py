"""Deterministic local fault campaign; real-process cases remain distinct from ledger tests."""
import argparse
from concurrent.futures import Future
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import threading
import uuid
from unittest.mock import patch

from csc.branches import BranchManager, MultiBranchScheduler, execute_shadow, outcome
from csc.compare import OutcomeComparisonEngine
from csc.contracts import Config, State, StateCaptureEngine, canonical, digest
from csc.pending import PendingShadowLedger
from csc.runner import run
from csc.store import KnowledgeStore
from csc.sync import InputSynchronizationLayer
from csc.warm import WarmProcess
from csc.world import ProductionWorld, workload
from experiments.replay import replay


BASE = Config(experiment_name="cycle5-fault", random_seed=15001, duration_epochs=12,
              warmup_epochs=0, horizon_ticks=2, shadow_count=1, mirror_count=1,
              execution_mode="asynchronous", worker_mode="warm", max_shadow_slots=1,
              production_period_s=.02, shadow_result_deadline_s=.3, shadow_timeout_s=1,
              retention_completed_epochs=4)


class MemoryStore:
    def __init__(self):
        self.entries = []

    def append(self, name, value):
        # Copy to avoid later mutation masquerading as a durable archive.
        self.entries.append((name, json.loads(canonical(value))))


class DeferredManager:
    def __init__(self):
        self.futures, self.requests, self.ledger = [], [], {}

    def launch(self, branches, anchor, events):
        output = []
        for branch in branches:
            future = Future()
            self.futures.append(future)
            self.requests.append({"anchor": anchor.envelope(), "branch": asdict(branch),
                                  "events": [asdict(e) for e in events]})
            self.ledger[branch.branch_id] = "BOUND"
            output.append((branch, future))
        return output

    def close(self):
        for future in self.futures:
            future.cancel()


class LedgerFixture:
    def __init__(self, config=BASE):
        self.config = config
        self.store, self.manager, self.now = MemoryStore(), DeferredManager(), [10.]
        self.workload_digest = hashlib.sha256()
        self.ledger = PendingShadowLedger(config, self.manager, OutcomeComparisonEngine(config),
                                          self.store, lambda: self.now[0])

    def package(self, epoch=0, identity="fault"):
        state = State(rng_seed=self.config.random_seed,
                      input_sequence_watermark=epoch * self.config.horizon_ticks - 1)
        anchor = StateCaptureEngine().capture(state, identity, epoch)
        branches = MultiBranchScheduler().plan(anchor, self.config, identity, epoch, "NS_GREEN")
        events = list(workload(self.config, identity))[epoch * self.config.horizon_ticks:
                                                     (epoch + 1) * self.config.horizon_ticks]
        self.store.append("fixture_inputs", [asdict(event) for event in events])
        for event in events:
            raw_event = asdict(event)
            raw_event.pop("experiment_id")
            self.workload_digest.update(canonical(raw_event))
        capability = object()
        world = ProductionWorld(state, capability, self.config)
        world.apply_plan("NS_GREEN", capability, "fixture")
        delivered, sync = InputSynchronizationLayer().deliver(events, branches[0])
        trace = [world.step(event, tick) for tick, event in enumerate(delivered)]
        production = outcome(branches[0], anchor, world.snapshot_state(), trace, sync, {})
        self.ledger.commit(anchor, branches, events, production)
        return self.ledger.pending.get(epoch), branches

    def result(self, index):
        return execute_shadow({**self.manager.requests[index], "config": asdict(self.config)})

    def records(self):
        return [value for name, value in self.store.entries if name == "cfr.jsonl"]


def synthetic_cases():
    rows, raw = [], {}

    def keep(name, fixture, production, evidence, recovery, **checks):
        rows.append({"case": name, "method": "deterministic ledger fixture; no OS process fault",
                     "production_impact": production, "evidence_impact": evidence,
                     "recovery_behavior": recovery, "checks": checks,
                     "passed": all(checks.values()), "lifecycle_counts": fixture.ledger.counts,
                     "config": asdict(fixture.config), "config_hash": digest(asdict(fixture.config)),
                     "seed": fixture.config.random_seed, "workload_sha256": fixture.workload_digest.hexdigest()})
        raw[name] = fixture.store.entries

    fixture = LedgerFixture()
    old, branches = fixture.package(identity="old")
    result = fixture.result(0)
    fixture.ledger.expire(old, "restart")
    fixture.ledger.finalize()
    fixture.manager.close()
    fixture.ledger.closed = True
    new = LedgerFixture()
    fresh, fresh_branches = new.package(identity="new")
    before = canonical(fresh["production"])
    for _ in range(2):
        new.ledger.accept(fresh, fresh_branches[1], result)
    keep("restart_queued_foreign_duplicate", new, "fixture production unchanged",
         "old queued work discarded; two foreign deliveries rejected", "new identity; no durable old-queue resume",
         old_queue_cancelled=all(f.cancelled() for f in fixture.manager.futures),
         both_rejected=new.ledger.counts["REJECTED"] == 2,
         production_unchanged=canonical(fresh["production"]) == before)
    raw["restart_old_identity"] = fixture.store.entries

    fixture = LedgerFixture(replace(BASE, duration_epochs=8, retention_completed_epochs=2))
    old, branches = fixture.package()
    result = fixture.result(0)
    for future in fixture.manager.futures:
        future.set_running_or_notify_cancel()
    fixture.now[0] += 1
    fixture.ledger.poll()
    for epoch in range(1, 6):
        package, _ = fixture.package(epoch)
        fixture.ledger.expire(package, "test_eviction")
        fixture.ledger.finalize()
    frozen = canonical(fixture.records())
    fixture.ledger.accept(old, branches[1], result)
    rejected_old_commit = False
    try:
        fixture.package(0)
    except ValueError:
        rejected_old_commit = True
    keep("result_after_retention_eviction", fixture, "fixture production comparisons unchanged",
         "late old result cannot resurrect archived comparison", "terminal package plus monotonic commit watermark",
         epoch_evicted=0 not in fixture.ledger.finalized,
         old_commit_rejected=rejected_old_commit,
         archived_records_unchanged=canonical(fixture.records()) == frozen,
         late_count=fixture.ledger.counts["LATE"] == 1,
         bounded_hot_cache=len(fixture.ledger.finalized) <= 2)

    fixture = LedgerFixture(replace(BASE, duration_epochs=100, max_pending_shadow_tasks=2))
    fixture.package()
    for future in fixture.manager.futures:
        future.set_running_or_notify_cancel()
    for epoch in range(1, 100):
        fixture.now[0] += 1
        fixture.package(epoch)
    fixture.now[0] += 1
    fixture.ledger.poll()
    keep("prolonged_saturation_100_epochs", fixture, "all 100 fixture production comparisons finalized",
         "198 later branches dropped; two running branches expired", "expired running futures retain permits",
         all_epochs=len(fixture.records()) == 100,
         two_active=len(fixture.ledger.active) == 2,
         dropped_count=fixture.ledger.counts["DROPPED"] == 198,
         bounded_cache=len(fixture.ledger.finished) <= BASE.retention_completed_epochs)

    fixture = LedgerFixture()
    fixture.package()
    fixture.manager.futures[0].set_result(fixture.result(0))
    fixture.manager.futures[1].set_exception(ConnectionError("one unavailable service slot"))
    fixture.ledger.poll()
    record = fixture.records()[0]
    keep("partially_unavailable_pool", fixture, "fixture production retained",
         "mirror accepted, alternative failed, regret unavailable", "remaining slot can serve; failed result terminal",
         partial_mirror=record["evidence_completeness"] == "MIRROR_COMPLETE",
         missing_regret=record["regret_raw"] is None,
         one_failure=fixture.ledger.counts["FAILED"] == 1)

    for kind in ("nan", "huge_integer", "oversized_body", "overlong_trace"):
        fixture = LedgerFixture(replace(BASE, max_result_bytes=8192))
        package, branches = fixture.package()
        result = fixture.result(0)
        if kind == "nan":
            result["metrics"]["mean_queue"] = float("nan")
        elif kind == "huge_integer":
            result["metrics"]["mean_queue"] = 10 ** 400
        elif kind == "oversized_body":
            result["padding"] = "x" * 8193
        else:
            result["trace"] = result["trace"] * 2
        before = canonical(package["production"])
        fixture.manager.futures[0].set_result(result)
        fixture.manager.futures[1].set_result(fixture.result(1))
        fixture.ledger.poll()
        keep(kind, fixture, "fixture production retained", "invalid estimate rejected; comparison incomplete",
             "terminal rejection; next epoch can commit", rejected=fixture.ledger.counts["REJECTED"] == 1,
             production_trace_unchanged=package["production"]["trace"] == json.loads(before)["trace"],
             incomplete=fixture.records()[0]["record_status"] == "PARTIAL")
    return rows, raw


def real_cases(directory, source_root):
    """Full authoritative runs with controlled transport faults; no stress exhaustion."""
    directory = Path(directory)
    rows = []
    _, baseline = run(replace(BASE, shadow_count=0, mirror_count=0, worker_mode="cold"), directory, "baseline")
    original = WarmProcess._receive

    for case in ("worker_dies_during_processing", "worker_dies_after_completion_before_ack"):
        injected = [False]
        timers = []

        def receive(worker, timeout):
            if worker.tasks == 0 and not injected[0]:
                # Constructor handshake calls _receive before any task. Only fault
                # an evaluation, recognized by successful READY already recorded.
                if hasattr(worker, "startup_ms"):
                    injected[0] = True
                    if case == "worker_dies_during_processing":
                        timer = threading.Timer(.04, worker.process.kill)
                        timers.append(timer)
                        timer.start()
                        return original(worker, timeout)
                    result = original(worker, timeout)
                    if result.get("status") != "REPORTED":
                        raise AssertionError("completed-before-ack hook did not receive a real result")
                    worker.process.kill()
                    raise ConnectionError("injected loss of result acknowledgment after real completion")
            return original(worker, timeout)

        config = replace(BASE, shadow_injected_delay_s=.12 if "during" in case else 0)
        with patch.object(WarmProcess, "_receive", receive):
            path, summary = run(config, directory, case)
        for timer in timers:
            timer.join()
        verification = replay(path, source_root)
        resources = [json.loads(line) for line in (path / "resource_metrics.jsonl").read_text().splitlines()]
        checks = {"fault_injected": injected[0],
                  "production_trajectory_equal": summary["production_semantic_sha256"] == baseline["production_semantic_sha256"],
                  "workload_equal": summary["workload_sha256"] == baseline["workload_sha256"],
                  "all_production_epochs": summary["epochs_total"] == BASE.duration_epochs,
                  "fault_loss_visible": summary["shadow_lifecycle_counts"]["FAILED"] + summary["shadow_lifecycle_counts"]["EXPIRED"] >= 1,
                  "worker_failure_visible": max(r.get("worker_failures", 0) for r in resources) >= 1,
                  "replacement_visible": max(r.get("worker_launches", 0) for r in resources) >= 2,
                  "replay_zero_mismatch": verification["trajectory_mismatches"] == 0}
        rows.append({"case": case, "method": "physical warm-process death during full local authoritative run",
                     "production_impact": "all production epochs retained; paired trajectory hash equal" if checks["production_trajectory_equal"] else "trajectory mismatch",
                     "evidence_impact": f"FAILED={summary['shadow_lifecycle_counts']['FAILED']}, EXPIRED={summary['shadow_lifecycle_counts']['EXPIRED']}, LATE={summary['shadow_lifecycle_counts']['LATE']}; incomplete comparisons retain missingness; late fault transport need not become pre-deadline FAILED",
                     "recovery_behavior": "worker discarded; later assignment launches replacement; no durable retry/ack protocol",
                     "checks": checks, "passed": all(checks.values()), "path": str(path),
                     "lifecycle_counts": summary["shadow_lifecycle_counts"], "replay": verification,
                     "production_interval_ms": summary.get("production_interval_ms"),
                     "config_hash": digest(asdict(config)), "seed": config.random_seed,
                     "workload_sha256": summary["workload_sha256"]})

    # A real worker's ordinary valid output is made oversized relative to a
    # deliberately small transport limit; this tests bounded read rejection.
    config = replace(BASE, duration_epochs=3, horizon_ticks=16, max_result_bytes=6000)
    path, summary = run(config, directory, "warm_transport_body_bound")
    verification = replay(path, source_root)
    _, bound_baseline = run(replace(config, shadow_count=0, mirror_count=0, worker_mode="cold"),
                            directory, "body_bound_baseline")
    # Verify the transport's own terminal result independent of the epoch's
    # short deadline: a late rejection is otherwise recorded as expiry.
    fixture = LedgerFixture(config)
    fixture.package()
    transport_request = {**fixture.manager.requests[0], "config": asdict(config)}
    request_bytes = len(canonical(transport_request))
    expected_response_bytes = len(canonical(execute_shadow(transport_request)))
    manager = BranchManager(config)
    try:
        transport = manager._execute(transport_request, 0)
        transport_discarded = manager.worker_failures == 1 and len(manager.workers) == 0
    finally:
        manager.close()
    checks = {"production_trajectory_equal": summary["production_semantic_sha256"] == bound_baseline["production_semantic_sha256"],
              "no_completed_branches": summary["shadow_lifecycle_counts"]["COMPLETED"] == 0,
              "request_below_bound": request_bytes < config.max_result_bytes,
              "response_above_bound": expected_response_bytes > config.max_result_bytes,
              "transport_rejection_visible": transport["status"] == "FAULTED" and "ValueError" in transport["failure_flags"],
              "transport_worker_discarded": transport_discarded,
              "replay_zero_mismatch": verification["trajectory_mismatches"] == 0}
    rows.append({"case": "warm_transport_body_bound", "method": "real full run plus isolated real-worker transport check at configured 6000-byte line bound",
                 "production_impact": "three production epochs retained; paired trajectory hash equal",
                 "evidence_impact": "no full-run branch accepted; direct oversized output rejected before JSON parsing; full-run failure/expiry counts retained",
                 "recovery_behavior": "direct rejected worker discarded; no enlargement of the 300ms epoch deadline",
                 "checks": checks, "passed": all(checks.values()), "path": str(path),
                 "isolated_transport_result": transport,
                 "request_bytes": request_bytes, "deterministic_expected_response_bytes": expected_response_bytes,
                 "lifecycle_counts": summary["shadow_lifecycle_counts"], "replay": verification,
                 "config_hash": digest(asdict(config)), "seed": config.random_seed,
                 "workload_sha256": summary["workload_sha256"]})

    original_append = KnowledgeStore.append
    failed = [False]

    def fail_storage(store, name, value):
        if name == "cfr.jsonl" and not failed[0]:
            failed[0] = True
            raise OSError("injected one-shot storage failure")
        return original_append(store, name, value)

    error = None
    config = replace(BASE, shadow_count=0, mirror_count=0, worker_mode="cold")
    with patch.object(KnowledgeStore, "append", fail_storage):
        try:
            run(config, directory, "storage_one_shot_failure")
        except OSError as exc:
            error = str(exc)
    path = directory / "storage_one_shot_failure"
    manifest = json.loads((path / "manifest.json").read_text())
    records = [json.loads(line) for line in (path / "cfr.jsonl").read_text().splitlines()]
    checks = {"fault_injected": failed[0], "failure_reported": error is not None,
              "manifest_failed": manifest["status"] == "FAILED", "production_truncated": len(records) < BASE.duration_epochs}
    rows.append({"case": "storage_temporarily_fails", "method": "one-shot injected coordinator cfr append OSError during full run",
                 "production_impact": f"authoritative run aborted after {len(records)} recorded production epochs; production cadence not preserved",
                 "evidence_impact": "partial run retained as FAILED; no successful full-run summary",
                 "recovery_behavior": "one-shot failure permits exception-path finalization; new immutable run needed; no storage failover",
                 "checks": checks, "passed": all(checks.values()), "path": str(path), "error": error,
                 "config_hash": digest(asdict(config)), "seed": config.random_seed,
                 "workload_sha256": digest([asdict(e) for e in workload(config, "storage_one_shot_failure")]),
                 "observed_production_epochs": len(records), "planned_epochs": BASE.duration_epochs})
    return rows


def campaign(root="results/cycle5-validation", real=True):
    path = Path(root) / ("faults-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    path.mkdir(parents=True, exist_ok=False)
    repository = Path(__file__).resolve().parent.parent
    sources = list((repository / "csc").glob("*.py")) + [Path(__file__).resolve(),
              repository / "experiments/replay.py", repository / "tests/test_cycle5_faults.py"]
    source_hashes = {}
    archive = path / "source"
    for source in sources:
        relative = source.relative_to(repository)
        target = archive / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        source_hashes[str(relative).replace("\\", "/")] = hashlib.sha256(source.read_bytes()).hexdigest()
    plan = {"status": "PREREGISTERED_LOCAL_FAULT_VALIDATION", "config": asdict(BASE),
            "config_hash": digest(asdict(BASE)), "seed": BASE.random_seed,
            "synthetic_epoch_count": 100, "full_run_epochs": BASE.duration_epochs, "real_cases_enabled": real,
            "source_hashes": source_hashes, "environment": {"python": platform.python_version(),
            "platform": platform.platform(), "cpu_count": os.cpu_count()},
            "cases": ["restart_queued_foreign_duplicate", "result_after_retention_eviction",
            "prolonged_saturation_100_epochs", "partially_unavailable_pool", "nan", "huge_integer",
            "oversized_body", "overlong_trace", "worker_dies_during_processing",
            "worker_dies_after_completion_before_ack", "warm_transport_body_bound", "storage_temporarily_fails"],
            "limitations": ["local first-party process faults; not hostile isolation",
            "ack-loss case deliberately discards a real received result; no persistent ack transaction",
            "synthetic ledger cases do not measure OS scheduling or cadence"]}
    (path / "protocol.json").write_bytes(canonical(plan))
    rows, raw = synthetic_cases()
    (path / "synthetic_raw.json").write_bytes(canonical(raw))
    collection_error = None
    if real:
        try:
            rows.extend(real_cases(path / "runs", archive))
        except Exception as exc:
            collection_error = f"{type(exc).__name__}: {exc}"
    source_stable = all(hashlib.sha256((repository / relative).read_bytes()).hexdigest() == expected
                        for relative, expected in source_hashes.items())
    result = {"status": "LOCALLY_TESTED", "passed": all(row["passed"] for row in rows) and source_stable and collection_error is None,
              "source_stable": source_stable, "cases": rows,
              "case_count": len(rows), "synthetic_workload_sha256": digest(raw),
              "analysis_script_sha256": source_hashes["experiments/cycle5_faults.py"],
              "collection_error": collection_error}
    (path / "fault_results.json").write_bytes(canonical(result))
    manifest = {**plan, "status": "COMPLETE" if result["passed"] else "FAILED",
                "artifact_hashes": {str(p.relative_to(path)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sorted(path.rglob("*")) if p.is_file()}}
    (path / "manifest.json").write_bytes(canonical(manifest))
    return path, result


def render_report(path, result, target="research/evidence/cycle5/cycle5_failure_recovery.md"):
    """Generate findings directly from campaign classifications, including negatives."""
    lines = ["# Cycle 5 failure and recovery", "",
             "**Status:** Locally tested first-party process and deterministic ledger fault validation, 2026-10-06.", "",
             "## Question, evidence and method", "",
             "Do explicit worker, delivery, retention, schema, storage and capacity faults preserve authoritative production, and what evidence is lost?",
             f"Evidence: `{path.as_posix()}/fault_results.json`, its pre-execution `protocol.json`, immutable source archive, raw synthetic ledger records and full-run manifests.",
             "`experiments/cycle5_faults.py` generates every classification below. Each synthetic assertion uses a fake clock/deferred future; physical worker cases execute full authoritative local runs, compare paired trajectory/workload hashes and replay accepted trajectories.", "",
             f"Campaign checks passed: **{result['passed']}**; cases: **{len(result['cases'])}**; source stable during collection: **{result['source_stable']}**. A passing check means the declared fault behavior was observed, not that availability survived every fault.", "",
             "## Preserved earlier validation attempts", ""]
    for earlier in sorted(path.parent.glob("faults-*")):
        if earlier == path or not (earlier / "fault_results.json").is_file():
            continue
        previous = json.loads((earlier / "fault_results.json").read_text())
        failures = [row["case"] for row in previous["cases"] if not row["passed"]]
        lines.append(f"- `{earlier.as_posix()}`: passed={previous['passed']}, source_stable={previous['source_stable']}, failed checks={failures}.")
    lines.extend(["", "Earlier runs retain their own source identities. A failed initial body-bound assertion expected pre-deadline FAILED delivery but observed EXPIRED/late delivery; the subsequent validation separates direct transport rejection from full-run deadline outcomes without extending the epoch deadline. Later worker loop-local cleanup produces a separate source variant and requires fresh validation, not alteration of archived evidence.", "",
             "## Findings", "",
             "| Fault | Method | Production impact | Evidence impact | Recovery | Checks |",
             "|---|---|---|---|---|---|"])
    for row in result["cases"]:
        values = [row["case"], row["method"], row["production_impact"], row["evidence_impact"],
                  row["recovery_behavior"], str(row["passed"])]
        lines.append("| " + " | ".join(value.replace("|", "/") for value in values) + " |")
    lines.extend(["", "**Negative availability finding:** A one-shot CFR storage write failure aborts the authoritative run; it is not isolated to evidence. The partial immutable run is marked FAILED when subsequent cleanup writes succeed. This is a production impact and must not be hidden in aggregated shadow-fault robustness.", "",
                  "## Limitations and open questions", "",
                  "The after-completion fault deliberately kills the worker and discards a real result between receipt and coordinator acceptance. It verifies visible loss/replacement, not a durable acknowledgment protocol or recovery of an unacknowledged completed result. Restart starts a fresh run identity and discards old queued work; it does not restore an old coordinator. Eviction rejection retains the active package's terminal state and a monotonic commit watermark; there is no network endpoint that accepts arbitrary old package objects.", "",
                  "Ledger fixture production checks establish immutability/finalization only; they do not measure OS scheduling, cadence or resource isolation. Physical worker death is tested in this cooperative local implementation, not hostile code. The actual warm line reader applies a byte bound before JSON parsing; the cold path captures subprocess output before checking size, and HTTP response parsing is not transport-body bounded. Oversized valid-identity synthetic output therefore tests coordinator rejection rather than universal transport memory safety.", "",
                  "The storage case is one transient failed append, not torn writes, disk exhaustion or persistent I/O failure. Persistent failures during exception cleanup can prevent a FAILED manifest update. JSONL flush is not fsync; atomic JSON replacement is not a multi-artifact transaction. All accepted full-run branches are replay checked; failed/incomplete branches have no invented outcomes.", "",
                  "## Next actions", "",
                  "Separate required production durability from speculative evidence persistence before claiming graceful degradation under storage outages. Define explicit fail-open/fail-closed requirements, bounded evidence spool/drop behavior and interrupted-run recovery. Bound cold/HTTP transport reads if those backends enter sustained or untrusted-output studies. Preserve trust Decision D and learning BLOCKED; no policy learning or second domain follows from these fault checks.", ""])
    Path(target).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="results/cycle5-validation")
    parser.add_argument("--synthetic-only", action="store_true")
    args = parser.parse_args()
    path, result = campaign(args.root, not args.synthetic_only)
    if result["passed"] and not args.synthetic_only:
        render_report(path, result)
    print(json.dumps({"path": str(path), "passed": result["passed"], "case_count": result["case_count"],
                      "source_stable": result["source_stable"],
                      "collection_error": result["collection_error"],
                      "failed_cases": [r["case"] for r in result["cases"] if not r["passed"]]}, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
