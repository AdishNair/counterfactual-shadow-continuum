"""End-to-end epoch harness, measurements and reproducible artifact generation."""
from dataclasses import asdict
import hashlib
import statistics
import time
import tracemalloc

from .branches import BranchManager, MultiBranchScheduler, outcome
from .compare import OutcomeComparisonEngine
from .contracts import State, StateCaptureEngine, canonical
from .safety import ActuatorGateway, TokenIssuer
from .store import KnowledgeStore
from .sync import InputSynchronizationLayer
from .world import ProductionWorld, workload


def distribution(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return {"n": 0, "median": None, "p95": None, "p99": None, "iqr": None}
    def q(p):
        index = (len(values) - 1) * p
        left = int(index)
        return values[left] + (values[min(left + 1, len(values) - 1)] - values[left]) * (index - left)
    return {"n": len(values), "median": statistics.median(values), "p95": q(.95), "p99": q(.99), "iqr": q(.75) - q(.25)}


def run(config, root="results", experiment_id=None):
    config.validate()
    if config.execution_mode == "asynchronous":
        from .async_runner import run_async
        return run_async(config, root, experiment_id)
    store = KnowledgeStore(root, config, experiment_id)
    eid = store.experiment_id
    capability, issuer = object(), TokenIssuer()
    world = ProductionWorld(State(rng_seed=config.random_seed), capability, config)
    gateway = ActuatorGateway(issuer, world, capability, eid)
    scheduler, capture, comparator = MultiBranchScheduler(), StateCaptureEngine(), OutcomeComparisonEngine(config)
    manager, sync = BranchManager(config), InputSynchronizationLayer()
    stream = iter(workload(config, eid))
    records, resources, production_digest, workload_digest = [], [], hashlib.sha256(), hashlib.sha256()
    unauthorized_mutations, authoritative_commands, virtual_count = 0, 0, 0
    tracemalloc.start()
    previous_start = None
    try:
        for epoch in range(config.duration_epochs):
            if config.production_period_s and epoch:
                time.sleep(max(0, config.production_period_s - (time.perf_counter() - started)))
            started, cpu_started = time.perf_counter(), time.process_time()
            production_interval_ms = None if previous_start is None else (started - previous_start) * 1000
            previous_start = started
            state = world.snapshot_state()
            t = time.perf_counter()
            anchor = capture.capture(state, eid, epoch)
            capture_ms = (time.perf_counter() - t) * 1000
            action = scheduler.decide(state, config, epoch)
            branches = scheduler.plan(anchor, config, eid, epoch, action)
            capture_skipped = len(anchor.payload) > config.capture_max_bytes or (config.failure_scenario == "capture" and epoch == config.failure_epoch)
            if capture_skipped:
                branches = branches[:1]
            production = branches[0]
            gateway.open_epoch(epoch, production.branch_id)
            gateway.actuate(issuer.issue(production, time.time() + 60), action)
            decision_ms = (time.perf_counter() - started) * 1000
            events = [next(stream) for _ in range(config.horizon_ticks)]
            for e in events:
                # Exclude experiment ID from paired-workload checksum.
                raw = asdict(e)
                raw.pop("experiment_id")
                workload_digest.update(canonical(raw))
                store.append("events.jsonl", asdict(e))
            store.append("anchors.jsonl", anchor.envelope())
            t = time.perf_counter()
            futures = manager.launch(branches[1:], anchor, events)
            branch_creation_ms = (time.perf_counter() - t) * 1000
            prod_cpu = time.process_time()
            delivered, sync_metrics = sync.deliver(events, production)
            trace = [world.step(e, tick) for tick, e in enumerate(delivered)]
            prod_result = outcome(production, anchor, world.snapshot_state(), trace, sync_metrics,
                                  {"decision_ms": decision_ms, "cpu_ms": (time.process_time() - prod_cpu) * 1000})
            production_digest.update(canonical({"action": action, "trace": trace, "state": asdict(world.snapshot_state())}))
            # Production has already actuated and evolved. The local harness waits
            # here for research accounting; it makes no real-time continuity claim.
            t = time.perf_counter()
            shadows = manager.collect(futures)
            barrier_ms = (time.perf_counter() - t) * 1000
            t = time.perf_counter()
            record = comparator.compare(anchor, branches, prod_result, shadows)
            compare_ms = (time.perf_counter() - t) * 1000
            if record is None:
                raise RuntimeError("no valid authoritative ground truth")
            records.append(record)
            store.append("cfr.jsonl", record)
            for result in record["branches"]:
                store.append("branch_metrics.jsonl", result)
                for entry in result.get("virtual_actuations", []):
                    virtual_count += 1
                    store.append("safety_events.jsonl", entry)
            for event in gateway.audit:
                store.append("safety_events.jsonl", event)
            gateway.audit.clear()
            for event in world.audit:
                authoritative_commands += 1
                expected_correlation = f"{eid}:{epoch}:{production.branch_id}"
                if event["correlation_id"] != expected_correlation or event["action"] != action:
                    unauthorized_mutations += 1
                store.append("environment_audit.jsonl", {"experiment_id": eid, "epoch": epoch, **event})
            world.audit.clear()
            t = time.perf_counter()
            for entry in manager.reap():
                store.append("lifecycle.jsonl", {"experiment_id": eid, "epoch": epoch, **entry})
            reset_ms = (time.perf_counter() - t) * 1000
            resource = {"experiment_id": eid, "epoch": epoch, "capture_ms": capture_ms,
                        "production_interval_ms": production_interval_ms,
                        "capture_skipped": capture_skipped, "anchor_bytes": len(anchor.payload),
                        "production_decision_ms": decision_ms, "branch_creation_ms": branch_creation_ms,
                        "barrier_ms": barrier_ms, "comparison_ms": compare_ms, "reset_ms": reset_ms,
                        "epoch_ms": (time.perf_counter() - started) * 1000,
                        "coordinator_cpu_ms": (time.process_time() - cpu_started) * 1000,
                        "worker_cpu_ms": sum(r.get("runtime", {}).get("cpu_ms", 0) for r in shadows),
                        "coordinator_python_peak_bytes": tracemalloc.get_traced_memory()[1],
                        "payload_bytes": sum(r.get("runtime", {}).get("request_bytes", 0) + r.get("runtime", {}).get("response_bytes", 0) for r in shadows),
                        "planned_shadow_workers": len(shadows)}
            resources.append(resource)
            store.append("resource_metrics.jsonl", resource)
            store.append("logs.jsonl", {"experiment_id": eid, "epoch": epoch, "component": "epoch_runtime",
                                        "snapshot_id": anchor.snapshot_id, "branch_id": production.branch_id,
                                        "sequence_number": production.end_sequence, "action": action,
                                        "result": record["record_status"]})
            # Raw trajectories live on disk; retain only summary inputs in memory.
            records[-1] = {key: record[key] for key in ("u_real", "epsilon", "regret_raw", "regret_discounted", "record_status", "missing")}
            records[-1]["branches"] = [{"metrics": prod_result["metrics"]}]
        measured, measured_resources = records[config.warmup_epochs:], resources[config.warmup_epochs:]
        summary = summarize(measured, measured_resources)
        summary.update(experiment_id=eid, epochs_total=config.duration_epochs, warmup_epochs=config.warmup_epochs,
                       production_semantic_sha256=production_digest.hexdigest(), workload_sha256=workload_digest.hexdigest(),
                       unauthorized_production_mutations_from_shadow=unauthorized_mutations,
                       authoritative_commands_observed=authoritative_commands,
                       safety_measurement_scope="gateway/world capability checks and isolated first-party worker execution; not OS containment",
                       rejected_world_mutation_attempts=world.denied_mutations)
        store.write_json("summary.json", summary)
        store.manifest["workload_sha256"] = workload_digest.hexdigest()
        lines = ["# TYPE csc_epoch_total counter", f"csc_epoch_total {config.duration_epochs}",
                 "# TYPE csc_realised_utility gauge", f"csc_realised_utility {records[-1]['u_real']}",
                 "# TYPE csc_virtual_actuation_total counter",
                 f"csc_virtual_actuation_total {virtual_count}"]
        for field in ("epsilon", "regret_raw", "regret_discounted"):
            if records[-1][field] is not None:
                lines.append(f"csc_{field} {records[-1][field]}")
        (store.path / "metrics.prom").write_text("\n".join(lines) + "\n", encoding="utf-8")
        store.close()
        return store.path, summary
    except BaseException as exc:
        store.close("FAILED", f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manager.close()
        tracemalloc.stop()


def summarize(records, resources):
    alternatives = [r for r in records if r["regret_discounted"] is not None]
    return {"epochs_measured": len(records), "production_utility": distribution([r["u_real"] for r in records]),
            "fidelity_gap": distribution([r["epsilon"] for r in records]),
            "regret_raw": distribution([r["regret_raw"] for r in records]),
            "regret_discounted": distribution([r["regret_discounted"] for r in records]),
            "beaten_rate": sum(r["regret_discounted"] > 0 for r in alternatives) / len(alternatives) if alternatives else None,
            "complete_fraction": (sum(r["record_status"] == "COMPLETE" for r in records) / len(records)
                                  if records else None),
            "excluded_branches": sum(len(r["missing"]) for r in records),
            "throughput": sum(r["branches"][0]["metrics"]["throughput"] for r in records),
            "waiting_vehicle_ticks": sum(r["branches"][0]["metrics"]["waiting_vehicle_ticks"] for r in records),
            "timing": {key: distribution([r[key] for r in resources]) for key in
                       ("capture_ms", "production_decision_ms", "branch_creation_ms", "barrier_ms", "comparison_ms", "reset_ms", "epoch_ms", "coordinator_cpu_ms", "worker_cpu_ms", "payload_bytes", "coordinator_python_peak_bytes")}}
