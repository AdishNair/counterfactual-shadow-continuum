"""Production commits first; bounded evidence advances independently afterward."""
from dataclasses import asdict
import hashlib
import time
import tracemalloc
import json
from collections import deque

from .branches import BranchManager, MultiBranchScheduler, outcome
from .compare import OutcomeComparisonEngine
from .contracts import State, StateCaptureEngine, canonical
from .pending import PendingShadowLedger
from .safety import ActuatorGateway, TokenIssuer
from .store import KnowledgeStore
from .sync import InputSynchronizationLayer
from .world import ProductionWorld, workload
from .os_metrics import process_metrics


def _stream_summary(cfr_path, resource_path, warmup):
    """Reduce JSONL without retaining full records or resource histories."""
    from .runner import distribution
    series = {key: [] for key in ("u_real", "epsilon", "regret_raw", "regret_discounted")}
    timing_keys = ("capture_ms", "production_decision_ms", "branch_creation_ms", "barrier_ms",
                   "comparison_ms", "reset_ms", "epoch_ms", "coordinator_cpu_ms",
                   "worker_cpu_ms", "payload_bytes", "coordinator_python_peak_bytes")
    timing = {key: [] for key in timing_keys}
    epochs = complete = excluded = throughput = waiting = beaten = alternatives = 0
    if cfr_path.exists():
        with cfr_path.open(encoding="utf-8") as stream:
            for line in stream:
                record = json.loads(line)
                if record.get("epoch", -1) < warmup:
                    continue
                epochs += 1
                for key in series:
                    series[key].append(record.get(key))
                if record.get("regret_discounted") is not None:
                    alternatives += 1
                    beaten += record["regret_discounted"] > 0
                complete += record.get("record_status") == "COMPLETE"
                excluded += len(record.get("missing", ()))
                production = record.get("branches", [{}])[0].get("metrics", {})
                throughput += production.get("throughput", 0)
                waiting += production.get("waiting_vehicle_ticks", 0)
    with resource_path.open(encoding="utf-8") as stream:
        for line in stream:
            resource = json.loads(line)
            if resource.get("epoch", -1) < warmup:
                continue
            for key in timing_keys:
                timing[key].append(resource.get(key))
    return {"epochs_measured": epochs, "production_utility": distribution(series["u_real"]),
            "fidelity_gap": distribution(series["epsilon"]),
            "regret_raw": distribution(series["regret_raw"]),
            "regret_discounted": distribution(series["regret_discounted"]),
            "beaten_rate": beaten / alternatives if alternatives else None,
            "complete_fraction": complete / epochs if epochs else None,
            "excluded_branches": excluded, "throughput": throughput,
            "waiting_vehicle_ticks": waiting,
            "timing": {key: distribution(values) for key, values in timing.items()}}


def run_async(config, root, experiment_id):
    store = KnowledgeStore(root, config, experiment_id)
    eid = store.experiment_id
    capability, issuer = object(), TokenIssuer()
    world = ProductionWorld(State(rng_seed=config.random_seed), capability, config)
    gateway = ActuatorGateway(issuer, world, capability, eid)
    scheduler, capture, sync = MultiBranchScheduler(), StateCaptureEngine(), InputSynchronizationLayer()
    initialization_started = time.perf_counter()
    try:
        manager = BranchManager(config)
    except BaseException as exc:
        store.close("FAILED", f"worker initialization: {type(exc).__name__}: {exc}")
        raise
    worker_pool_initialization_s = time.perf_counter() - initialization_started
    worker_ready_startup_ms = [w.startup_ms for w in getattr(manager, "workers", ())]
    ledger = PendingShadowLedger(config, manager, OutcomeComparisonEngine(config), store)
    store.append("logs.jsonl", {"event": "RUN_STARTED", "experiment_id": eid,
                                "monotonic_s": time.perf_counter()})
    stream = iter(workload(config, eid))
    resources, production_digest, workload_digest = deque(maxlen=config.retention_completed_epochs), hashlib.sha256(), hashlib.sha256()
    commands, unauthorized, previous_start = 0, 0, None
    process_metrics()  # Load OS instrumentation before timed production begins.
    tracemalloc.start()
    try:
        for epoch in range(config.duration_epochs):
            if config.production_period_s and previous_start is not None:
                time.sleep(max(0, config.production_period_s - (time.perf_counter() - previous_start)))
            started, cpu_started = time.perf_counter(), time.process_time()
            interval = None if previous_start is None else (started - previous_start) * 1000
            previous_start = started
            state = world.snapshot_state()
            t = time.perf_counter()
            anchor = capture.capture(state, eid, epoch)
            capture_ms = (time.perf_counter() - t) * 1000
            action = scheduler.decide(state, config, epoch)
            branches = scheduler.plan(anchor, config, eid, epoch, action)
            skipped = len(anchor.payload) > config.capture_max_bytes or (config.failure_scenario == "capture" and epoch == config.failure_epoch)
            if skipped:
                branches = branches[:1]
            production = branches[0]
            gateway.open_epoch(epoch, production.branch_id)
            gateway.actuate(issuer.issue(production, time.time() + 60), action)
            decision_ms = (time.perf_counter() - started) * 1000
            production_decision_monotonic_s = time.perf_counter()
            events = [next(stream) for _ in range(config.horizon_ticks)]
            for event in events:
                raw = asdict(event)
                raw.pop("experiment_id")
                workload_digest.update(canonical(raw))
                store.append("events.jsonl", asdict(event))
            store.append("anchors.jsonl", anchor.envelope())
            prod_cpu = time.process_time()
            delivered, sync_metrics = sync.deliver(events, production)
            trace = [world.step(event, tick) for tick, event in enumerate(delivered)]
            prod_result = outcome(production, anchor, world.snapshot_state(), trace, sync_metrics,
                                  {"decision_ms": decision_ms, "cpu_ms": (time.process_time() - prod_cpu) * 1000})
            production_digest.update(canonical({"action": action, "trace": trace, "state": asdict(world.snapshot_state())}))
            production_path_ms = (time.perf_counter() - started) * 1000
            production_completed_monotonic_s = time.perf_counter()
            production_path_cpu_ms = (time.process_time() - cpu_started) * 1000
            t = time.perf_counter()
            ledger.commit(anchor, branches, events, prod_result)
            ledger.poll()
            evidence_bookkeeping_ms = (time.perf_counter() - t) * 1000
            for event in gateway.audit:
                store.append("safety_events.jsonl", event)
            gateway.audit.clear()
            for event in world.audit:
                commands += 1
                if event["correlation_id"] != f"{eid}:{epoch}:{production.branch_id}" or event["action"] != action:
                    unauthorized += 1
                store.append("environment_audit.jsonl", {"experiment_id": eid, "epoch": epoch, **event})
            world.audit.clear()
            resource = {"experiment_id": eid, "epoch": epoch, "capture_ms": capture_ms, "capture_skipped": skipped,
                        "epoch_started_monotonic_s": started,
                        "production_decision_monotonic_s": production_decision_monotonic_s,
                        "production_completed_monotonic_s": production_completed_monotonic_s,
                        "anchor_bytes": len(anchor.payload), "production_decision_ms": decision_ms,
                        "production_interval_ms": interval, "production_path_ms": production_path_ms,
                        "production_path_cpu_ms": production_path_cpu_ms,
                        "evidence_bookkeeping_ms": evidence_bookkeeping_ms, "branch_creation_ms": evidence_bookkeeping_ms,
                        "barrier_ms": 0, "comparison_ms": 0, "reset_ms": 0,
                        "epoch_ms": (time.perf_counter() - started) * 1000,
                        "coordinator_cpu_ms": (time.process_time() - cpu_started) * 1000,
                        "worker_cpu_ms": None, "payload_bytes": None,
                        "coordinator_python_peak_bytes": tracemalloc.get_traced_memory()[1],
                        "coordinator_python_current_bytes": tracemalloc.get_traced_memory()[0],
                        "active_shadow_tasks": len(ledger.active), "pending_epochs": len(ledger.pending),
                        "queued_shadow_tasks": sum(not f.running() and not f.done() for _, _, f in ledger.active.values()),
                        "running_shadow_tasks": sum(f.running() for _, _, f in ledger.active.values())}
            os_sample = process_metrics()
            resource.update(coordinator_rss_bytes=os_sample["rss_bytes"], coordinator_handles=os_sample["handle_count"],
                            coordinator_process_cpu_s=os_sample["process_cpu_s"],
                            retained_completed_epochs=len(ledger.finished), duplicate_cache_size=len(ledger.finalized),
                            result_ledger_size=len(manager.ledger), resource_history_size=len(resources),
                            synchronization_hot_count=0, replay_metadata_hot_count=0,
                            artifact_storage_bytes=sum(p.stat().st_size for p in store.path.iterdir() if p.is_file()),
                            **ledger.last_admission)
            if hasattr(manager, "resource_state"):
                resource.update(manager.resource_state())
            if hasattr(store, "evidence_state"):
                resource.update(store.evidence_state())
            resources.append(resource)
            store.append("resource_metrics.jsonl", resource)
        production_finished = time.perf_counter()
        store.append("lifecycle.jsonl", {"status": "PRODUCTION_FINISHED", "monotonic_s": production_finished})
        ledger.shutdown()
        store.drain_evidence()
        shutdown_ms = (time.perf_counter() - production_finished) * 1000
        store.append("lifecycle.jsonl", {"status": "SHUTDOWN_COMPLETE", "shutdown_after_production_ms": shutdown_ms})
        summary_started = time.perf_counter()
        # Exact research summaries are an offline phase after production stops.
        # The continuous hot runtime never retains the full experiment history.
        summary = _stream_summary(store.path / "cfr.jsonl", store.path / "resource_metrics.jsonl",
                                  config.warmup_epochs)
        summary.update(experiment_id=eid, epochs_total=config.duration_epochs, warmup_epochs=config.warmup_epochs,
                       execution_mode="asynchronous", production_semantic_sha256=production_digest.hexdigest(),
                       worker_mode=config.worker_mode,
                       worker_pool_initialization_s=worker_pool_initialization_s,
                       worker_ready_startup_ms=worker_ready_startup_ms,
                       workload_sha256=workload_digest.hexdigest(), authoritative_commands_observed=commands,
                       unauthorized_production_mutations_from_shadow=unauthorized,
                       shadow_lifecycle_counts=ledger.counts, max_active_shadow_tasks=ledger.max_active,
                       shutdown_after_production_ms=shutdown_ms,
                       evidence_scope="local cooperative subprocesses; no resource isolation or real-time deadline")
        summary.update(offline_summary_ms=(time.perf_counter() - summary_started) * 1000,
                       offline_summary_rss_bytes=process_metrics()["rss_bytes"],
                       offline_summary_python_current_bytes=tracemalloc.get_traced_memory()[0],
                       offline_summary_python_peak_bytes=tracemalloc.get_traced_memory()[1])
        store.write_json("summary.json", summary)
        store.append("logs.jsonl", {"event": "RUN_COMPLETE", "experiment_id": eid,
                                    "epochs": config.duration_epochs,
                                    "monotonic_s": time.perf_counter()})
        store.manifest["outputs"].append("epoch_journal.jsonl")
        store.manifest["workload_sha256"] = workload_digest.hexdigest()
        store.close()
        return store.path, summary
    except BaseException as exc:
        try:
            store.append("logs.jsonl", {"event": "RUN_FAILED", "experiment_id": eid,
                                        "error_type": type(exc).__name__,
                                        "monotonic_s": time.perf_counter()})
        except BaseException:
            pass
        for package in list(ledger.pending.values()):
            ledger.expire(package, "coordinator_failure")
        ledger.finalize()
        store.close("FAILED", f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manager.close()
        tracemalloc.stop()
