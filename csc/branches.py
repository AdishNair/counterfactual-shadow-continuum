"""Scheduling, branch execution and bounded process lifecycle."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request
import queue
import threading
from collections import deque
import math

from .contracts import ACTIONS, Anchor, Branch, Config, Event, canonical
from .safety import VirtualActuator
from .sync import InputSynchronizationLayer
from .world import ShadowWorldModel, domain_metrics
from .executor import BoundedExecutor, ExecutorCapacityError
from concurrent.futures import Future


class MultiBranchScheduler:
    def decide(self, state, config, epoch):
        if config.production_policy == "fixed":
            return "BALANCED"
        ns, ew = state.queue_ns, state.queue_ew
        if config.production_policy == "predictive":
            ns += config.horizon_ticks * state.recent_arrivals[0]
            ew += config.horizon_ticks * state.recent_arrivals[1]
        return "NS_GREEN" if ns >= ew else "EW_GREEN"

    def plan(self, anchor, config, experiment_id, epoch, production_action):
        state = anchor.hydrate()
        start = state.input_sequence_watermark + 1
        roles = [("PRODUCTION", production_action)]
        slots = config.max_shadow_slots if config.execution_mode == "synchronous" else config.mirror_count + config.shadow_count
        if config.failure_scenario == "resource_budget" and epoch == config.failure_epoch:
            slots = 0
        if config.shadow_count or config.mirror_count:
            for _ in range(min(config.mirror_count, slots)):
                roles.append(("MIRROR", production_action))
            alternatives = [a for a in ACTIONS if a != production_action]
            for action in alternatives[:min(config.shadow_count, max(0, slots - len(roles) + 1))]:
                roles.append(("SHADOW", action))
        return [Branch(f"J1-{epoch}-{role}-{i}", experiment_id, epoch, role, action,
                       anchor.snapshot_id, start, start + config.horizon_ticks - 1)
                for i, (role, action) in enumerate(roles)]


def outcome(branch, anchor, state, trace, sync, runtime, status="REPORTED", failure_flags=None, vab=None):
    return {**asdict(branch), "schema_version": 1,
            "provenance": "REALISED" if branch.role == "PRODUCTION" else "ESTIMATED",
            "observation_window": [branch.start_sequence, branch.end_sequence],
            "anchor_hash": anchor.snapshot_id, "initial_state_hash": anchor.snapshot_id,
            "final_state": asdict(state), "trace": trace, "metrics": domain_metrics(trace),
            "runtime": runtime, "synchronization": sync, "status": status,
            "failure_flags": failure_flags or [], "virtual_actuations": vab or []}


def execute_shadow(request):
    """Wire entrypoint: no production handle, signing key, or mutation capability."""
    started, cpu_started = time.perf_counter(), time.process_time()
    anchor = Anchor.from_envelope(request["anchor"])
    branch = Branch(**request["branch"])
    if branch.role == "PRODUCTION":
        raise PermissionError("shadow runtime refuses production identity")
    if branch.parent_snapshot_id != anchor.snapshot_id:
        raise ValueError("branch anchor mismatch")
    metadata = json.loads(anchor.payload)
    if metadata["experiment_id"] != branch.experiment_id or metadata["epoch"] != branch.epoch:
        raise ValueError("anchor identity mismatch")
    config = Config(**request["config"]).validate()
    state = anchor.hydrate()
    if branch.start_sequence != state.input_sequence_watermark + 1 or branch.end_sequence - branch.start_sequence + 1 != config.horizon_ticks:
        raise ValueError("anchor/window mismatch")
    hydrate_ms = (time.perf_counter() - started) * 1000
    if config.shadow_injected_delay_s:
        time.sleep(config.shadow_injected_delay_s)
    if config.shadow_load == "cpu":
        # Fixed work, independently timed: deliberately cooperative local load.
        checksum = sum((i * i) % 104729 for i in range(1000000))
    if config.shadow_load == "memory":
        memory_load = bytearray(16 * 1024 * 1024)
        for i in range(0, len(memory_load), 4096):
            memory_load[i] = 1
    fault = request.get("fault", "none")
    if fault == "crash":
        raise RuntimeError("injected branch crash")
    if fault == "timeout":
        time.sleep(config.shadow_timeout_s * 3)
    events = [Event(**e) for e in request["events"]]
    delivered, sync = InputSynchronizationLayer().deliver(events, branch, config.synchronization_enabled,
                                                         fault, config.shadow_delay_s)
    world, actuator, trace = ShadowWorldModel(state, config), VirtualActuator(branch, config.horizon_ticks), []
    for tick, event in enumerate(delivered):
        if fault == "model_error" and tick == 1:
            raise RuntimeError("injected model failure")
        if len(trace) >= config.horizon_ticks:
            break
        actuator.actuate(branch.action, event.sequence_number)
        trace.append(world.step(event, branch.action, tick))
    status = "REPORTED" if sync["comparable"] else "DEGRADED"
    rss = None
    try:
        import resource
        raw_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss = raw_rss if sys.platform == "darwin" else raw_rss * 1024
    except ImportError:
        pass
    runtime = {"hydrate_ms": hydrate_ms, "execution_ms": (time.perf_counter() - started) * 1000,
               "worker_started_monotonic_s": started, "model_completed_monotonic_s": time.perf_counter(),
               "cpu_ms": (time.process_time() - cpu_started) * 1000, "peak_rss_bytes": rss,
               "inputs_consumed": len(trace), "pid": os.getpid()}
    from .os_metrics import process_metrics
    runtime.update(process_metrics())
    if request.get("_dispatch_monotonic_s") is not None:
        runtime["process_launch_to_entry_ms"] = (started - request["_dispatch_monotonic_s"]) * 1000
    return outcome(branch, anchor, world.state, trace, sync, runtime, status,
                   [] if sync["comparable"] else ["incomparable_inputs"], actuator.entries)


class BranchManager:
    def __init__(self, config):
        self.config = config
        self.pool = BoundedExecutor(max(1, config.max_shadow_slots), config.max_pending_shadow_tasks,
                                    config.max_pending_shadow_bytes)
        self.ledger = {}
        self.worker_lock = threading.Lock()
        self.workers = set()
        self.cold_processes = set()
        self.cold_constructing = 0
        self.available_workers = queue.Queue()
        self.lease_condition = threading.Condition()
        self.worker_launches = 0
        self.worker_recycles = 0
        self.worker_failures = 0
        self.closing = threading.Event()
        self.quarantined_workers = set()
        self.constructing_workers = 0
        self.cleanup_errors = deque(maxlen=config.retention_completed_epochs)
        if config.worker_mode == "warm" and config.max_shadow_slots:
            try:
                for _ in range(config.max_shadow_slots):
                    self._return_worker(self._new_worker())
            except BaseException:
                self.close()
                raise

    def _new_worker(self):
        from .warm import WarmProcess
        with self.worker_lock:
            if self.closing.is_set() or len(self.workers) + self.constructing_workers >= self.config.max_shadow_slots:
                raise RuntimeError("worker pool closing or unresolved capacity")
            self.constructing_workers += 1
        holder = []
        def owned(worker):
            holder.append(worker)
            with self.worker_lock:
                self.workers.add(worker)
                self.worker_launches += 1
            if self.closing.is_set():
                worker.abort()
                raise RuntimeError("worker created during shutdown")
        try:
            worker = WarmProcess(self.config, on_spawn=owned)
            if self.closing.is_set():
                self._discard_worker(worker)
                raise RuntimeError("worker pool closing")
            return worker
        except BaseException:
            for worker in holder:
                try:
                    self._discard_worker(worker)
                except BaseException as exc:
                    self.cleanup_errors.append(type(exc).__name__)
            raise
        finally:
            with self.worker_lock:
                self.constructing_workers -= 1

    def _discard_worker(self, worker):
        # Removal from reusable circulation is independent of cleanup success.
        with self.worker_lock:
            self.quarantined_workers.add(worker)
        worker.close()
        with self.worker_lock:
            self.workers.discard(worker)
            self.quarantined_workers.discard(worker)

    def _acquire_worker(self):
        """Acquire a reusable-worker lease, waking promptly when closure begins."""
        deadline = time.monotonic() + self.config.shadow_timeout_s
        with self.lease_condition:
            while True:
                if self.closing.is_set():
                    raise RuntimeError("worker pool closing")
                try:
                    return self.available_workers.get_nowait()
                except queue.Empty:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("warm worker lease timeout")
                    self.lease_condition.wait(remaining)

    def _return_worker(self, worker):
        """Publish a lease token only while the manager is open."""
        with self.lease_condition:
            if self.closing.is_set():
                return False
            self.available_workers.put_nowait(worker)
            self.lease_condition.notify()
            return True

    def resource_state(self):
        from .os_metrics import process_metrics
        with self.worker_lock:
            workers = list(self.workers)
            cold_processes = list(self.cold_processes)
        samples = [process_metrics(w.process.pid) for w in workers] + [process_metrics(p.pid) for p in cold_processes]
        return {"worker_count": len(workers) + len(cold_processes), "worker_launches": self.worker_launches,
                "worker_recycles": self.worker_recycles, "worker_failures": self.worker_failures,
                "worker_lifecycle_hot_count": len(workers) + len(cold_processes),
                "worker_rss_bytes": sum(s["rss_bytes"] for s in samples) if samples and all(s["rss_bytes"] is not None for s in samples) else None,
                "worker_handles": sum(s["handle_count"] for s in samples) if samples and all(s["handle_count"] is not None for s in samples) else None,
                "worker_os_samples_available": sum(s["rss_bytes"] is not None for s in samples),
                "quarantined_workers": len(self.quarantined_workers),
                "constructing_workers": self.constructing_workers + self.cold_constructing,
                "unresolved_owned_processes": len(self.quarantined_workers) + len(cold_processes),
                "cleanup_error_count": len(self.cleanup_errors),
                "cleanup_complete": (not workers and not cold_processes and not self.constructing_workers and not self.cold_constructing
                                     and self.pool.state()["physical_inflight_tasks"] == 0) if self.closing.is_set() else None,
                **self.pool.state()}

    def admission_capacity(self):
        physical = self.pool.state()["physical_available_capacity"]
        if self.config.worker_mode != "cold" or self.config.backend != "local":
            return physical
        with self.worker_lock:
            process_capacity = max(0, self.config.max_shadow_slots - len(self.cold_processes) - self.cold_constructing)
        return min(physical, process_capacity)

    def validate_worker_result(self, request, result):
        """Pure worker contract check; owns no production state or authority."""
        from .compare import utility
        from .contracts import State, digest
        if not isinstance(result, dict) or len(canonical(result)) > self.config.max_result_bytes:
            raise ValueError("worker body/schema bound")
        branch = request["branch"]
        if any(result.get(key) != value for key, value in branch.items()):
            raise ValueError("worker identity mismatch")
        if result.get("provenance") != "ESTIMATED" or result.get("schema_version") != 1:
            raise ValueError("worker provenance/schema mismatch")
        if result.get("status") not in ("REPORTED", "DEGRADED"):
            raise ValueError("worker terminal status mismatch")
        anchor_hash = request["anchor"]["snapshot_id"]
        if result.get("anchor_hash") != anchor_hash or result.get("initial_state_hash") != anchor_hash:
            raise ValueError("worker anchor mismatch")
        if result.get("observation_window") != [branch["start_sequence"], branch["end_sequence"]]:
            raise ValueError("worker window mismatch")
        metrics, trace = result.get("metrics"), result.get("trace")
        if not isinstance(metrics, dict) or not isinstance(trace, list) or len(trace) > self.config.horizon_ticks:
            raise ValueError("worker metrics/trace schema")
        keys = ("mean_queue", "waiting_vehicle_ticks", "phase_switches", "throughput", "final_queue")
        if any(type(metrics.get(k)) not in (int, float) or not math.isfinite(metrics[k]) or metrics[k] < 0 for k in keys):
            raise ValueError("worker numeric metrics")
        utility(metrics, self.config)
        if any(not isinstance(row, dict) or any(type(row.get(k)) not in (int, float) or not math.isfinite(row[k]) or row[k] < 0
                                               for k in ("queue_ns", "queue_ew")) for row in trace):
            raise ValueError("worker numeric trace")
        State(**result["final_state"]).validate()
        synchronization = result.get("synchronization")
        runtime = result.get("runtime")
        if not isinstance(synchronization, dict) or not isinstance(runtime, dict):
            raise ValueError("worker synchronization/runtime schema")
        required_times = ("execution_ms", "hydrate_ms", "cpu_ms", "worker_started_monotonic_s",
                          "model_completed_monotonic_s", "process_launch_to_entry_ms")
        timing_envelope = sys.float_info.max / 4
        if any(type(runtime.get(name)) not in (int, float) or not math.isfinite(runtime[name]) or
               runtime[name] < 0 or runtime[name] > timing_envelope
               for name in required_times):
            raise ValueError("worker timing schema")
        if (runtime["hydrate_ms"] > runtime["execution_ms"] or
                runtime["model_completed_monotonic_s"] < runtime["worker_started_monotonic_s"]):
            raise ValueError("worker timing relationship schema")
        accumulation_terms = max(1, self.config.duration_epochs *
                                 max(1, self.config.shadow_count + self.config.mirror_count))
        if runtime["cpu_ms"] > sys.float_info.max / (2 * accumulation_terms):
            raise ValueError("worker CPU exceeds finite run-aggregation envelope")
        if (type(runtime.get("inputs_consumed")) is not int or runtime["inputs_consumed"] != len(trace) or
                type(runtime.get("pid")) is not int or runtime["pid"] <= 0):
            raise ValueError("worker runtime identity schema")
        if "worker_startup_ms" in runtime and (
                type(runtime["worker_startup_ms"]) not in (int, float) or
                not math.isfinite(runtime["worker_startup_ms"]) or runtime["worker_startup_ms"] < 0 or
                runtime["worker_startup_ms"] > timing_envelope):
            raise ValueError("worker startup timing schema")
        if self.config.worker_mode == "warm" and (
                "worker_startup_ms" not in runtime or
                type(runtime.get("worker_metadata_version")) is not int or runtime["worker_metadata_version"] != 1 or
                type(runtime.get("worker_completed_tasks")) is not int or runtime["worker_completed_tasks"] <= 0 or
                runtime.get("reset_verified") is not True):
            raise ValueError("warm worker runtime reset schema")
        nullable_counts = ("peak_rss_bytes", "rss_bytes", "handle_count")
        if any(runtime.get(name) is not None and (type(runtime[name]) is not int or runtime[name] < 0)
               for name in nullable_counts):
            raise ValueError("worker resource counter schema")
        if runtime.get("process_cpu_s") is not None and (
                type(runtime["process_cpu_s"]) not in (int, float) or
                not math.isfinite(runtime["process_cpu_s"]) or runtime["process_cpu_s"] < 0):
            raise ValueError("worker process CPU schema")
        if branch["role"] == "MIRROR":
            # Production queues are nonnegative. This conservative envelope bounds
            # every possible production-minus-mirror vector for this input window.
            state = Anchor.from_envelope(request["anchor"]).hydrate()
            upper_ns = state.queue_ns + sum(event["arrivals_ns"] for event in request["events"])
            upper_ew = state.queue_ew + sum(event["arrivals_ew"] for event in request["events"])
            if any(row["queue_ns"] < 0 or row["queue_ew"] < 0 or not math.isfinite(
                math.hypot(max(upper_ns, row["queue_ns"]), max(upper_ew, row["queue_ew"]))) for row in trace):
                raise ValueError("worker mirror divergence overflow")
        if result["status"] == "REPORTED" and (
            len(trace) != self.config.horizon_ticks or synchronization.get("comparable") is not True or
            synchronization.get("consumed_sequence") != list(range(branch["start_sequence"], branch["end_sequence"] + 1)) or
            synchronization.get("input_hash") != digest(request["events"])
        ):
            raise ValueError("worker input mismatch")
        actuations = result.get("virtual_actuations")
        if not isinstance(actuations, list) or len(actuations) > self.config.horizon_ticks:
            raise ValueError("worker actuation schema")

    def launch(self, branches, anchor, events):
        futures = []
        for index, branch in enumerate(branches):
            self.ledger[branch.branch_id] = "BOUND"
            fault = "none"
            if branch.epoch == self.config.failure_epoch and branch.role == "SHADOW" and index == len(branches) - 1:
                fault = self.config.failure_scenario
            request = {"anchor": anchor.envelope(), "branch": asdict(branch),
                       "events": [asdict(e) for e in events], "config": asdict(self.config), "fault": fault}
            submitted = time.perf_counter()
            assignment_bytes = len(canonical(request))
            if assignment_bytes > self.config.max_assignment_bytes:
                future = Future()
                self.ledger[branch.branch_id] = "FAULTED"
                future._csc_admitted = False
                future._csc_drop_reason = "assignment_body_bound"
                future.set_result(None)
                futures.append((branch, future))
                continue  # No oversized serialized assignment enters physical queue.
            try:
                future = self.pool.submit(self._execute, request, index, submitted,
                                          _resident_bytes=assignment_bytes)
                future._csc_admitted = True
                future._csc_assignment_bytes = assignment_bytes
            except ExecutorCapacityError as exc:
                future = Future()
                future._csc_admitted = False
                future._csc_drop_reason = exc.reason
                future.set_result(None)
            futures.append((branch, future))
        return futures

    def _execute(self, request, index, submitted=None):
        started = time.perf_counter()
        queue_wait_ms = 0 if submitted is None else (started - submitted) * 1000
        request["_dispatch_monotonic_s"] = started
        branch = Branch(**request["branch"])
        self.ledger[branch.branch_id] = "RUNNING"
        try:
            if self.config.backend == "http":
                url = self.config.remote_shadow_urls[index % len(self.config.remote_shadow_urls)].rstrip("/") + "/v1/evaluate"
                req = urllib.request.Request(url, canonical(request), {"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=self.config.shadow_timeout_s) as response:
                    result = json.load(response)
            elif self.config.worker_mode == "warm":
                worker = self._acquire_worker()
                try:
                    if worker is None:
                        worker = self._new_worker()
                    if worker.expired():
                        self._discard_worker(worker)
                        self.worker_recycles += 1
                        worker = self._new_worker()
                    result = worker.evaluate(request)
                    # Validate while the process lease is still exclusive.
                    self.validate_worker_result(request, result)
                    self._enrich_result(request, result, started, submitted, queue_wait_ms)
                except BaseException:
                    self.worker_failures += 1
                    suspect = worker
                    worker = None
                    if suspect is not None:
                        try:
                            self._discard_worker(suspect)
                        except BaseException as exc:
                            self.cleanup_errors.append(type(exc).__name__)
                    raise
                finally:
                    self._return_worker(worker)
            else:
                # Spawned workers get a minimal environment, fresh ephemeral cwd,
                # serialized state only, and no coordinator mutation credentials.
                root = str(Path(__file__).resolve().parent.parent)
                env = {k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP") if k in os.environ}
                env["PYTHONPATH"], env["PYTHONDONTWRITEBYTECODE"] = root, "1"
                with tempfile.TemporaryDirectory(prefix="csc-shadow-") as scratch:
                    with self.worker_lock:
                        if (self.closing.is_set() or
                                len(self.cold_processes) + self.cold_constructing >= self.config.max_shadow_slots):
                            raise RuntimeError("cold worker capacity unavailable")
                        self.cold_constructing += 1
                    try:
                        proc = subprocess.Popen([sys.executable, "-m", "csc.worker"],
                                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                cwd=scratch, env=env)
                        with self.worker_lock:
                            self.cold_processes.add(proc)
                            self.worker_launches += 1
                    finally:
                        with self.worker_lock:
                            self.cold_constructing -= 1
                    settled = False
                    try:
                        if self.closing.is_set():
                            raise RuntimeError("cold child created during shutdown")
                        stdout, stderr = proc.communicate(canonical(request), timeout=self.config.shadow_timeout_s)
                        settled = True
                        if proc.returncode:
                            raise subprocess.CalledProcessError(proc.returncode, proc.args, stdout, stderr)
                    except BaseException:
                        try:
                            if proc.poll() is None:
                                proc.kill()
                            proc.communicate(timeout=5)
                            settled = True
                        except BaseException as exc:
                            self.cleanup_errors.append(type(exc).__name__)
                        raise
                    finally:
                        with self.worker_lock:
                            if settled and proc.poll() is not None:
                                self.cold_processes.discard(proc)
                if len(stdout) > self.config.max_result_bytes:
                    raise ValueError("worker result exceeds body bound")
                result = json.loads(stdout)
            # Never trust a worker's claimed identity: compare against the ledger.
            for key, value in asdict(branch).items():
                if result.get(key) != value:
                    raise ValueError(f"worker identity mismatch: {key}")
            if result.get("provenance") != "ESTIMATED":
                raise ValueError("forged outcome provenance")
            if self.config.worker_mode != "warm" or self.config.backend == "http":
                self.validate_worker_result(request, result)
                self._enrich_result(request, result, started, submitted, queue_wait_ms)
            self.ledger[branch.branch_id] = result["status"]
            return result
        except Exception as exc:
            status = "TIMEOUT" if isinstance(exc, (subprocess.TimeoutExpired, TimeoutError)) else "FAULTED"
            self.ledger[branch.branch_id] = status
            return {**asdict(branch), "status": status, "provenance": "ESTIMATED", "utility": None,
                    "failure_flags": [type(exc).__name__], "runtime": {"dispatch_roundtrip_ms": (time.perf_counter() - started) * 1000,
                    "queue_wait_ms": queue_wait_ms, "worker_mode": self.config.worker_mode}}

    def _enrich_result(self, request, result, started, submitted, queue_wait_ms):
            result["runtime"]["dispatch_roundtrip_ms"] = (time.perf_counter() - started) * 1000
            result["runtime"].setdefault("result_received_monotonic_s", time.perf_counter())
            result["runtime"].update(dispatch_submitted_monotonic_s=submitted,
                                     dispatch_started_monotonic_s=started)
            result["runtime"]["queue_wait_ms"] = queue_wait_ms
            result["runtime"]["transport_overhead_ms"] = max(0, result["runtime"]["dispatch_roundtrip_ms"] - result["runtime"].get("execution_ms", 0))
            result["runtime"]["worker_mode"] = self.config.worker_mode
            result["runtime"]["request_bytes"] = len(canonical(request))
            result["runtime"]["response_bytes"] = 0
            for _ in range(4):
                result["runtime"]["response_bytes"] = len(canonical(result))
            if len(canonical(result)) > self.config.max_result_bytes:
                raise ValueError("enriched worker result exceeds body bound")

    def collect(self, futures):
        results = [f.result() for _, f in futures]
        return results

    def reap(self):
        reaped = [{"branch_id": bid, "terminal_status": status, "status": "REAPED"}
                  for bid, status in self.ledger.items()]
        self.ledger.clear()
        return reaped

    def close(self, wait=True):
        with self.lease_condition:
            self.closing.set()
            self.lease_condition.notify_all()
        self.pool.shutdown(wait=False, cancel_futures=True)
        with self.worker_lock:
            workers = list(self.workers)
            cold_processes = list(self.cold_processes)
        # Kill transports before waiting: blocked pipe writes must be interrupted.
        errors = []
        for worker in workers:
            try:
                worker.abort()
            except BaseException as exc:
                errors.append(type(exc).__name__)
        for process in cold_processes:
            try:
                if process.poll() is None:
                    process.kill()
            except BaseException as exc:
                errors.append(type(exc).__name__)
        try:
            self.pool.shutdown(wait=wait, cancel_futures=True, timeout=12 + self.config.shadow_timeout_s)
        except BaseException as exc:
            errors.append(type(exc).__name__)
        with self.worker_lock:
            workers = list(self.workers)
            cold_processes = list(self.cold_processes)
        for worker in workers:
            try:
                self._discard_worker(worker)
            except BaseException as exc:
                errors.append(type(exc).__name__)
        for process in cold_processes:
            try:
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=5)
                with self.worker_lock:
                    self.cold_processes.discard(process)
            except BaseException as exc:
                errors.append(type(exc).__name__)
        self.cleanup_errors.extend(errors)
        if errors or self.workers or self.cold_processes or self.constructing_workers or self.cold_constructing:
            raise RuntimeError(f"incomplete worker cleanup: {errors}; warm={len(self.workers)} cold={len(self.cold_processes)} constructing={self.constructing_workers + self.cold_constructing}")
