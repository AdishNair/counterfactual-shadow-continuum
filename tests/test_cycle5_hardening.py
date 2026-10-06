"""Post-measurement regressions for physical bounds, quarantine and pipe timeout."""
from concurrent.futures import Future
from dataclasses import replace
import json
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch

from csc.branches import BranchManager, execute_shadow
from csc.contracts import Config
from csc.executor import BoundedExecutor
from csc.warm import WarmProcess
from tests.test_cycle5_runtime import request


def warm_result(cfg, epoch=0):
    """Valid first-party warm response before a test injects one corruption."""
    result = execute_shadow(request(cfg, epoch))
    result["runtime"].update(process_launch_to_entry_ms=0, worker_startup_ms=0,
                             worker_metadata_version=1, worker_completed_tasks=1,
                             reset_verified=True)
    return result


class HardeningTests(unittest.TestCase):
    def config(self):
        return Config(duration_epochs=12, warmup_epochs=0, horizon_ticks=4,
                      execution_mode="asynchronous", worker_mode="warm", max_shadow_slots=1,
                      shadow_timeout_s=.15)

    def test_corrupt_warm_outcome_quarantined_before_next_lease(self):
        for corruption in ("identity", "numeric", "input", "schema", "provenance"):
            cfg = self.config()
            manager = BranchManager(cfg)
            try:
                worker = next(iter(manager.workers))
                result = warm_result(cfg)
                if corruption == "identity":
                    result["epoch"] = 99
                elif corruption == "numeric":
                    result["metrics"]["mean_queue"] = float("nan")
                elif corruption == "input":
                    result["synchronization"]["input_hash"] = "wrong"
                elif corruption == "schema":
                    result["schema_version"] = 99
                else:
                    result["provenance"] = "REALISED"
                with patch.object(worker, "evaluate", return_value=result):
                    self.assertEqual(manager._execute(request(cfg), 0)["status"], "FAULTED")
                self.assertIsNotNone(worker.process.poll())
                self.assertNotIn(worker, manager.workers)
                recovered = manager._execute(request(cfg, 1), 0)
                self.assertEqual(recovered["status"], "REPORTED")
                self.assertNotEqual(recovered["runtime"]["pid"], worker.process.pid)
            finally:
                manager.close()

    def test_cancelled_physical_queue_cannot_grow_on_readmission(self):
        capacity = 12
        executor = BoundedExecutor(1, capacity)
        started, release = threading.Event(), threading.Event()
        def blocked():
            started.set()
            release.wait(3)
        try:
            executor.submit(blocked)
            self.assertTrue(started.wait(1))
            queued = [executor.submit(lambda: None) for _ in range(capacity - 1)]
            for future in queued:
                self.assertTrue(future.cancel())
            for _ in range(1000):
                with self.assertRaisesRegex(RuntimeError, "capacity"):
                    executor.submit(lambda: None)
                state = executor.state()
                self.assertEqual(state["physical_inflight_tasks"], capacity)
                self.assertEqual(state["physical_queue_depth"], capacity - 1)
            release.set()
            deadline = time.monotonic() + 2
            while executor.state()["physical_inflight_tasks"] and time.monotonic() < deadline:
                time.sleep(.001)
            self.assertEqual(executor.state()["physical_inflight_tasks"], 0)
            self.assertEqual(executor.submit(lambda: 7).result(timeout=1), 7)
        finally:
            release.set()
            executor.shutdown(timeout=3)

    def unresponsive_worker(self, cfg):
        # A real process acknowledges readiness but never reads the input pipe.
        original = subprocess.Popen
        source = "import sys,time;sys.stdout.buffer.write(b'{\"status\":\"READY\"}\\n');sys.stdout.buffer.flush();time.sleep(30)"
        def spawned(args, **kwargs):
            return original([sys.executable, "-c", source], **kwargs)
        with patch("csc.warm.subprocess.Popen", side_effect=spawned):
            return WarmProcess(cfg)

    def test_unread_pipe_write_has_absolute_timeout_and_destroys_worker(self):
        cfg = self.config()
        worker = self.unresponsive_worker(cfg)
        started = time.monotonic()
        try:
            with self.assertRaisesRegex(TimeoutError, "write timeout"):
                worker.evaluate({"padding": "x" * (1024 * 1024)})
            self.assertLess(time.monotonic() - started, 2)
            worker.process.wait(timeout=2)
            self.assertIsNotNone(worker.process.poll())
        finally:
            worker.close()
        self.assertFalse(worker.writer.is_alive())
        self.assertFalse(worker.reader.is_alive())

    def test_manager_shutdown_kills_transport_before_executor_join(self):
        cfg = replace(self.config(), shadow_timeout_s=5)
        manager = BranchManager(cfg)
        try:
            ordinary = next(iter(manager.workers))
            manager.available_workers.get_nowait()
            manager._discard_worker(ordinary)
            worker = self.unresponsive_worker(cfg)
            manager.workers.add(worker)
            manager.available_workers.put(worker)
            req = request(cfg)
            req["padding"] = "x" * (1024 * 1024)
            future = manager.pool.submit(manager._execute, req, 0)
            time.sleep(.05)
            started = time.monotonic()
            manager.close()
            self.assertLess(time.monotonic() - started, 2)
            self.assertTrue(future.done())
            self.assertIsNotNone(worker.process.poll())
            self.assertFalse(worker.writer.is_alive())
        finally:
            manager.close()

    def test_parent_reader_does_not_retain_consumed_outcome(self):
        cfg = replace(self.config(), shadow_timeout_s=1)
        manager = BranchManager(cfg)
        try:
            worker = next(iter(manager.workers))
            self.assertEqual(manager._execute(request(cfg), 0)["status"], "REPORTED")
            time.sleep(.01)
            frame = sys._current_frames()[worker.reader.ident]
            while frame and frame.f_code.co_name != "_read":
                frame = frame.f_back
            self.assertIsNotNone(frame)
            self.assertNotIn("value", frame.f_locals)
            self.assertNotIn("line", frame.f_locals)
            self.assertEqual(worker.responses.qsize(), 0)
        finally:
            manager.close()

    def test_oversized_assignment_never_enters_physical_executor(self):
        from csc.contracts import Anchor, Branch, Event
        cfg = replace(self.config(), max_assignment_bytes=256)
        manager = BranchManager(cfg)
        try:
            req = request(cfg)
            branch = Branch(**req["branch"])
            futures = manager.launch([branch], Anchor.from_envelope(req["anchor"]), [Event(**e) for e in req["events"]])
            future = futures[0][1]
            self.assertIsNone(future.result(timeout=.1))
            self.assertFalse(future._csc_admitted)
            self.assertEqual(future._csc_drop_reason, "assignment_body_bound")
            self.assertEqual(manager.pool.state()["physical_inflight_tasks"], 0)
        finally:
            manager.close()

    def test_failed_destruction_never_republishes_corrupt_lease(self):
        cfg = replace(self.config(), shadow_timeout_s=1)
        manager = BranchManager(cfg)
        try:
            worker = next(iter(manager.workers))
            result = warm_result(cfg)
            result["epoch"] = 99
            with patch.object(worker, "evaluate", return_value=result), patch.object(worker, "close", side_effect=PermissionError("denied")):
                self.assertEqual(manager._execute(request(cfg), 0)["status"], "FAULTED")
                self.assertIn(worker, manager.quarantined_workers)
                self.assertIsNone(manager.available_workers.get_nowait())
                manager.available_workers.put(None)
                self.assertEqual(manager._execute(request(cfg, 1), 0)["status"], "FAULTED")
                self.assertEqual(manager.worker_launches, 1)
        finally:
            manager.close()

    def test_malformed_runtime_mirror_overflow_and_enrichment_are_quarantined(self):
        for corruption in ("runtime_string", "runtime_negative", "mirror_overflow", "enriched_size"):
            cfg = replace(self.config(), shadow_timeout_s=1)
            manager = BranchManager(cfg)
            try:
                worker = next(iter(manager.workers))
                result = warm_result(cfg)
                if corruption == "runtime_string":
                    result["runtime"]["execution_ms"] = "bad"
                elif corruption == "runtime_negative":
                    result["runtime"]["execution_ms"] = -1
                elif corruption == "mirror_overflow":
                    result["trace"][0].update(queue_ns=1.7e308, queue_ew=1.7e308)
                else:
                    from csc.contracts import canonical
                    manager.config = replace(cfg, max_result_bytes=len(canonical(result)) + 5)
                with patch.object(worker, "evaluate", return_value=result):
                    self.assertEqual(manager._execute(request(cfg), 0)["status"], "FAULTED")
                self.assertIsNotNone(worker.process.poll())
                self.assertNotIn(worker, manager.workers)
            finally:
                manager.close()

    def test_partial_constructor_thread_start_failure_reaps_real_child(self):
        cfg = self.config()
        original_spawn = subprocess.Popen
        processes = []
        def spawned(*args, **kwargs):
            process = original_spawn(*args, **kwargs)
            processes.append(process)
            return process
        with patch("csc.warm.subprocess.Popen", side_effect=spawned), patch("csc.warm.threading.Thread.start", side_effect=RuntimeError("helper start failed")):
            with self.assertRaisesRegex(RuntimeError, "helper start"):
                WarmProcess(cfg)
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].poll())

    def test_failed_replacement_constructor_does_not_escape_ownership(self):
        cfg = replace(self.config(), shadow_timeout_s=1, worker_max_tasks=1)
        manager = BranchManager(cfg)
        try:
            self.assertEqual(manager._execute(request(cfg), 0)["status"], "REPORTED")
            original_start = threading.Thread.start
            def start(thread):
                if thread.name.startswith("Thread-"):
                    raise RuntimeError("replacement helper failure")
                return original_start(thread)
            with patch("csc.warm.threading.Thread.start", side_effect=start):
                self.assertEqual(manager._execute(request(cfg, 1), 0)["status"], "FAULTED")
            self.assertFalse(manager.workers)
            self.assertFalse(manager.constructing_workers)
            self.assertEqual(manager._execute(request(cfg, 2), 0)["status"], "REPORTED")
        finally:
            manager.close()

    def test_close_attempts_all_owned_workers_after_one_cleanup_error(self):
        cfg = replace(self.config(), max_shadow_slots=2)
        manager = BranchManager(cfg)
        try:
            first, second = list(manager.workers)
            with patch.object(first, "abort", side_effect=PermissionError("denied")), patch.object(first, "close", side_effect=PermissionError("denied")):
                with self.assertRaisesRegex(RuntimeError, "incomplete worker cleanup"):
                    manager.close()
                self.assertIsNotNone(second.process.poll())
                self.assertIn(first, manager.workers)
                self.assertIn(first, manager.quarantined_workers)
        finally:
            manager.close()
        self.assertTrue(manager.resource_state()["cleanup_complete"])

    def test_cold_spawn_after_close_snapshot_is_immediately_reaped(self):
        cfg = replace(self.config(), worker_mode="cold", shadow_timeout_s=.1)
        manager = BranchManager(cfg)
        spawned, release = threading.Event(), threading.Event()
        processes = []
        original = subprocess.Popen
        def paused_spawn(*args, **kwargs):
            process = original(*args, **kwargs)
            processes.append(process)
            spawned.set()
            release.wait(1)
            return process
        try:
            with patch("csc.branches.subprocess.Popen", side_effect=paused_spawn):
                future = manager.pool.submit(manager._execute, request(cfg), 0)
                self.assertTrue(spawned.wait(1))
                timer = threading.Timer(.03, release.set)
                timer.start()
                manager.close()
                timer.join()
                self.assertTrue(future.done())
                self.assertIsNotNone(processes[0].poll())
                self.assertFalse(manager.cold_processes)
        finally:
            release.set()
            manager.close()

    def test_concurrent_cancel_dequeue_and_shutdown_preserve_physical_bound(self):
        executor = BoundedExecutor(2, 12)
        futures = []
        lock = threading.Lock()
        def submit_cancel():
            for _ in range(300):
                try:
                    future = executor.submit(lambda: time.sleep(.0001))
                except RuntimeError:
                    continue
                future.cancel()
                with lock:
                    futures.append(future)
                self.assertLessEqual(executor.state()["physical_inflight_tasks"], 12)
        threads = [threading.Thread(target=submit_cancel) for _ in range(3)]
        for thread in threads:
            thread.start()
        time.sleep(.001)
        executor.shutdown(timeout=3)
        for thread in threads:
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())
        self.assertEqual(executor.state()["physical_inflight_tasks"], 0)
        self.assertTrue(all(future.done() for future in futures))

    def test_warm_creation_during_close_keeps_owned_constructor_then_reaps(self):
        cfg = replace(self.config(), worker_mode="cold", shadow_timeout_s=.1)
        manager = BranchManager(cfg)
        manager.config = replace(cfg, worker_mode="warm")
        manager.available_workers.put(None)
        spawned, release = threading.Event(), threading.Event()
        original = subprocess.Popen
        processes = []
        def paused_spawn(*args, **kwargs):
            process = original(*args, **kwargs)
            processes.append(process)
            spawned.set()
            release.wait(1)
            return process
        try:
            with patch("csc.warm.subprocess.Popen", side_effect=paused_spawn):
                future = manager.pool.submit(manager._execute, request(manager.config), 0)
                self.assertTrue(spawned.wait(1))
                self.assertEqual(manager.constructing_workers, 1)
                timer = threading.Timer(.03, release.set)
                timer.start()
                manager.close()
                timer.join()
                self.assertTrue(future.done())
                self.assertIsNotNone(processes[0].poll())
                self.assertFalse(manager.workers)
                self.assertFalse(manager.constructing_workers)
        finally:
            release.set()
            manager.close()

    def test_cold_failed_termination_keeps_ownership_and_bounds_second_communicate(self):
        cfg = replace(self.config(), worker_mode="cold")
        manager = BranchManager(cfg)
        class FailedProcess:
            def __init__(self):
                self.timeouts = []
                self.pid = 0
                self.terminated = False
            def poll(self):
                return 0 if self.terminated else None
            def kill(self):
                raise PermissionError("termination denied")
            def communicate(self, body=None, timeout=None):
                self.timeouts.append(timeout)
                if self.terminated:
                    return b"", b""
                raise subprocess.TimeoutExpired("fake", timeout)
        failed = FailedProcess()
        try:
            with patch("csc.branches.subprocess.Popen", return_value=failed):
                self.assertEqual(manager._execute(request(cfg), 0)["status"], "TIMEOUT")
            self.assertIn(failed, manager.cold_processes)
            self.assertEqual(failed.timeouts, [cfg.shadow_timeout_s])
            with self.assertRaisesRegex(RuntimeError, "incomplete worker cleanup"):
                manager.close()
            self.assertIn(failed, manager.cold_processes)
        finally:
            failed.terminated = True
            manager.close()
        self.assertEqual(failed.timeouts[-1], 5)

    def test_cold_second_communicate_timeout_preserves_owned_process(self):
        cfg = replace(self.config(), worker_mode="cold")
        manager = BranchManager(cfg)
        class SlowCleanup:
            pid = 0
            def __init__(self):
                self.timeouts = []
                self.settled = False
            def poll(self):
                return 0 if self.settled else None
            def kill(self):
                pass
            def communicate(self, body=None, timeout=None):
                self.timeouts.append(timeout)
                if self.settled:
                    return b"", b""
                raise subprocess.TimeoutExpired("fake", timeout)
        process = SlowCleanup()
        try:
            with patch("csc.branches.subprocess.Popen", return_value=process):
                self.assertEqual(manager._execute(request(cfg), 0)["status"], "TIMEOUT")
            self.assertEqual(process.timeouts, [cfg.shadow_timeout_s, 5])
            self.assertIn(process, manager.cold_processes)
        finally:
            process.settled = True
            manager.close()

    def test_shutdown_wakes_dequeued_warm_task_waiting_for_lease(self):
        cfg = replace(self.config(), shadow_timeout_s=2)
        manager = BranchManager(cfg)
        held = manager.available_workers.get_nowait()
        future = manager.pool.submit(manager._execute, request(cfg), 0)
        deadline = time.monotonic() + 1
        while not future.running() and time.monotonic() < deadline:
            time.sleep(.001)
        self.assertTrue(future.running())
        started = time.monotonic()
        manager.close()
        self.assertLess(time.monotonic() - started, 2)
        self.assertTrue(future.done())
        self.assertEqual(future.result()["status"], "FAULTED")
        self.assertIsNotNone(held.process.poll())
        self.assertEqual(manager.pool.state()["physical_inflight_tasks"], 0)

    def test_open_manager_warm_lease_wait_has_finite_timeout(self):
        cfg = self.config()
        manager = BranchManager(cfg)
        held = manager.available_workers.get_nowait()
        try:
            started = time.monotonic()
            result = manager._execute(request(cfg), 0)
            self.assertEqual(result["status"], "TIMEOUT")
            self.assertLess(time.monotonic() - started, 1)
            self.assertEqual(manager.worker_launches, 1)
        finally:
            manager._return_worker(held)
            manager.close()

    def test_unresolved_cold_process_consumes_process_capacity(self):
        cfg = replace(self.config(), worker_mode="cold", max_shadow_slots=1)
        manager = BranchManager(cfg)
        class UnresolvedProcess:
            pid = 0
            returncode = None
            def poll(self): return None
            def kill(self): raise PermissionError("denied")
            def communicate(self, body=None, timeout=None):
                raise subprocess.TimeoutExpired("fake", timeout)
        process = UnresolvedProcess()
        try:
            with patch("csc.branches.subprocess.Popen", return_value=process) as spawn:
                self.assertEqual(manager._execute(request(cfg), 0)["status"], "TIMEOUT")
                self.assertEqual(spawn.call_count, 1)
            self.assertEqual(manager.admission_capacity(), 0)
            with patch("csc.branches.subprocess.Popen") as forbidden_spawn:
                self.assertEqual(manager._execute(request(cfg, 1), 0)["status"], "FAULTED")
                forbidden_spawn.assert_not_called()
            self.assertEqual(len(manager.cold_processes), 1)
        finally:
            process.poll = lambda: 0
            process.communicate = lambda body=None, timeout=None: (b"", b"")
            manager.close()

    def test_runtime_schema_and_extreme_utility_corruption_quarantine(self):
        corruptions = (
            ("cpu_string", lambda result: result["runtime"].update(cpu_ms="bad")),
            ("cpu_negative", lambda result: result["runtime"].update(cpu_ms=-1)),
            ("cpu_aggregate_overflow", lambda result: result["runtime"].update(cpu_ms=1e308)),
            ("hydrate_median_overflow", lambda result: result["runtime"].update(hydrate_ms=1e308)),
            ("bool_counter", lambda result: result["runtime"].update(inputs_consumed=True)),
            ("negative_metric", lambda result: result["metrics"].update(mean_queue=-100)),
        )
        for name, corrupt in corruptions:
            with self.subTest(name=name):
                cfg = self.config()
                manager = BranchManager(cfg)
                try:
                    worker = next(iter(manager.workers))
                    result = warm_result(cfg)
                    corrupt(result)
                    with patch.object(worker, "evaluate", return_value=result):
                        self.assertEqual(manager._execute(request(cfg), 0)["status"], "FAULTED")
                    self.assertIsNotNone(worker.process.poll())
                    self.assertNotIn(worker, manager.workers)
                finally:
                    manager.close()

        cfg = replace(self.config(), queue_weight=1e306)
        manager = BranchManager(cfg)
        try:
            worker = next(iter(manager.workers))
            result = warm_result(cfg)
            result["metrics"]["mean_queue"] = 100
            with patch.object(worker, "evaluate", return_value=result):
                self.assertEqual(manager._execute(request(cfg), 0)["status"], "FAULTED")
            self.assertIsNotNone(worker.process.poll())
        finally:
            manager.close()

    def test_cold_result_uses_same_runtime_and_metric_validation(self):
        from csc.contracts import canonical
        cfg = replace(self.config(), worker_mode="cold", shadow_timeout_s=1)
        for name, corrupt in (
            ("cpu", lambda result: result["runtime"].update(cpu_ms="bad")),
            ("metric", lambda result: result["metrics"].update(mean_queue=-1)),
            ("optional_startup", lambda result: result["runtime"].update(worker_startup_ms="bad")),
        ):
            with self.subTest(name=name):
                manager = BranchManager(cfg)
                req = request(cfg)
                req["_dispatch_monotonic_s"] = time.perf_counter()
                result = execute_shadow(req)
                corrupt(result)
                class Process:
                    pid = 12345
                    returncode = 0
                    def poll(self): return 0
                    def communicate(self, body=None, timeout=None): return canonical(result), b""
                try:
                    with patch("csc.branches.subprocess.Popen", return_value=Process()):
                        outcome = manager._execute(request(cfg), 0)
                    self.assertEqual(outcome["status"], "FAULTED")
                    self.assertFalse(manager.cold_processes)
                finally:
                    manager.close()

    def test_comparison_rejects_extreme_production_utility_without_nonfinite_record(self):
        from csc.compare import OutcomeComparisonEngine, RegretCalculator
        from csc.contracts import Anchor, Branch
        cfg = replace(self.config(), queue_weight=1e306)
        req = request(cfg)
        anchor = Anchor.from_envelope(req["anchor"])
        production_branch = Branch("prod", "hardening", 0, "PRODUCTION", "NS_GREEN",
                                   anchor.snapshot_id, 0, cfg.horizon_ticks - 1)
        production = warm_result(cfg)
        production.update(branch_id="prod", experiment_id="hardening", role="PRODUCTION",
                          provenance="REALISED", action="NS_GREEN")
        production["metrics"]["mean_queue"] = 100
        production["synchronization"].update(comparable=True)
        self.assertIsNone(OutcomeComparisonEngine(cfg).compare(anchor, [production_branch], production, []))
        with self.assertRaisesRegex(ValueError, "regret"):
            RegretCalculator.calculate(-1e308, [1e308], 0)

    def test_generic_distinct_k5_accounting_without_traffic_execution(self):
        """Synthetic labels exercise core accounting; traffic still rejects K>2."""
        from dataclasses import dataclass, asdict
        from csc.contracts import State, StateCaptureEngine
        from csc.pending import PendingShadowLedger
        from csc.compare import OutcomeComparisonEngine
        @dataclass(frozen=True)
        class AccountingBranch:
            branch_id: str
            experiment_id: str
            epoch: int
            role: str
            action: str
            parent_snapshot_id: str
            start_sequence: int = 0
            end_sequence: int = 0
        class Store:
            def __init__(self):
                self.records = []
            def append(self, name, value):
                if name == "cfr.jsonl":
                    self.records.append(value)
        with self.assertRaises(ValueError):
            replace(self.config(), shadow_count=5).validate()
        for capacity, expected_k, completeness in ((4, 3, "PARTIAL_ALTERNATIVES"), (6, 5, "COMPLETE_COMPARISON")):
            cfg = replace(self.config(), horizon_ticks=1, shadow_count=5, max_pending_shadow_tasks=capacity)
            anchor = StateCaptureEngine().capture(State(), "generic-accounting", 0)
            branches = [AccountingBranch("prod", "generic-accounting", 0, "PRODUCTION", "PRIMARY", anchor.snapshot_id),
                        AccountingBranch("mirror", "generic-accounting", 0, "MIRROR", "PRIMARY", anchor.snapshot_id)]
            branches += [AccountingBranch(f"alt-{i}", "generic-accounting", 0, "SHADOW", f"CHOICE-{i}", anchor.snapshot_id) for i in range(5)]
            def result(branch):
                return {**asdict(branch), "status": "REPORTED", "provenance": "REALISED" if branch.role == "PRODUCTION" else "ESTIMATED",
                        "anchor_hash": anchor.snapshot_id, "initial_state_hash": anchor.snapshot_id, "observation_window": [0, 0],
                        "trace": [{"queue_ns": 1, "queue_ew": 1}],
                        "metrics": {"mean_queue": 2, "waiting_vehicle_ticks": 2, "phase_switches": 0, "throughput": 0},
                        "synchronization": {"input_hash": "synthetic-window", "comparable": True}, "runtime": {}}
            class Manager:
                ledger = {}
                def admission_capacity(self):
                    return capacity
                def launch(self, selected, anchor, events):
                    output = []
                    for branch in selected:
                        future = Future()
                        future.set_result(result(branch))
                        output.append((branch, future))
                    return output
            store = Store()
            ledger = PendingShadowLedger(cfg, Manager(), OutcomeComparisonEngine(cfg), store)
            ledger.commit(anchor, branches, [], result(branches[0]))
            ledger.poll()
            record = store.records[0]
            self.assertEqual(record["requested_k"], 5)
            self.assertEqual(record["admitted_k"], expected_k)
            self.assertEqual(record["completed_k"], expected_k)
            self.assertEqual(record["evidence_completeness"], completeness)
            self.assertEqual(ledger.counts["DROPPED"], 5 - expected_k)
            self.assertEqual(len({b.action for b in branches if b.role == "SHADOW"}), 5)


if __name__ == "__main__":
    unittest.main()
