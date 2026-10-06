"""Cycle 5 gate: reusable-process equivalence, integrity, replacement and bounds."""
from concurrent.futures import Future
from dataclasses import asdict, replace
import json
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from csc.branches import BranchManager, MultiBranchScheduler, execute_shadow, outcome
from csc.compare import OutcomeComparisonEngine
from csc.contracts import Config, State, StateCaptureEngine
from csc.pending import PendingShadowLedger
from csc.runner import run
from csc.sync import InputSynchronizationLayer
from csc.warm import WarmSession
from csc.world import ProductionWorld, workload


def request(config, epoch=0, action="NS_GREEN", regime=0):
    state = State(queue_ns=14 if not regime else 2, queue_ew=3 if not regime else 31,
                  signal_phase="NS_GREEN" if not regime else "EW_GREEN",
                  phase_elapsed=regime * 3, rng_seed=config.random_seed,
                  input_sequence_watermark=epoch * config.horizon_ticks - 1)
    anchor = StateCaptureEngine().capture(state, "gate", epoch)
    branch = MultiBranchScheduler().plan(anchor, config, "gate", epoch, action)[1]
    events = list(workload(config, "gate"))[epoch * config.horizon_ticks:(epoch + 1) * config.horizon_ticks]
    return {"anchor": anchor.envelope(), "branch": asdict(branch), "events": [asdict(e) for e in events],
            "config": asdict(config), "fault": "none"}


def semantic(result):
    value = {key: result[key] for key in ("trace", "metrics", "final_state", "anchor_hash", "initial_state_hash",
            "observation_window", "virtual_actuations", "status", "failure_flags", "provenance")}
    value["synchronization"] = {key: result["synchronization"][key] for key in ("input_hash", "consumed_sequence", "comparable")}
    return value


class WarmCorrectnessGate(unittest.TestCase):
    def setUp(self):
        self.config = Config(duration_epochs=12, warmup_epochs=0, horizon_ticks=4, shadow_count=1,
                             mirror_count=1, max_shadow_slots=1, worker_mode="warm",
                             execution_mode="asynchronous", shadow_timeout_s=1,
                             workload_profile="incident", model_incidents=True)

    def test_repeated_hydration_actions_regimes_incidents_cold_equivalence(self):
        warm = BranchManager(self.config)
        cold = BranchManager(replace(self.config, worker_mode="cold"))
        pids = set()
        try:
            for epoch in range(12):
                req = request(self.config, epoch, ("NS_GREEN", "EW_GREEN", "BALANCED")[epoch % 3], epoch % 2)
                actual = warm._execute(req, 0)
                expected = cold._execute(req, 0)
                self.assertEqual(actual["status"], "REPORTED")
                self.assertEqual(semantic(actual), semantic(expected))
                self.assertTrue(actual["runtime"]["reset_verified"])
                pids.add(actual["runtime"]["pid"])
            self.assertEqual(len(pids), 1)
        finally:
            warm.close()
            cold.close()

    def test_two_workers_same_action_determinism(self):
        managers = [BranchManager(self.config), BranchManager(self.config)]
        try:
            req = request(self.config)
            results = [manager._execute(req, 0) for manager in managers]
            self.assertNotEqual(results[0]["runtime"]["pid"], results[1]["runtime"]["pid"])
            self.assertEqual(semantic(results[0]), semantic(results[1]))
        finally:
            for manager in managers:
                manager.close()

    def test_contamination_destroys_worker_before_replacement(self):
        manager = BranchManager(self.config)
        try:
            old = next(iter(manager.workers))
            req = request(self.config)
            req["fault"] = "worker_contamination"
            self.assertEqual(manager._execute(req, 0)["status"], "FAULTED")
            self.assertIsNotNone(old.process.poll())
            result = manager._execute(request(self.config, 1), 0)
            self.assertEqual(result["status"], "REPORTED")
            self.assertNotEqual(result["runtime"]["pid"], old.process.pid)
        finally:
            manager.close()

    def test_environment_and_buffer_integrity_checks(self):
        session = WarmSession()
        session.buffers.append("old input")
        with self.assertRaisesRegex(RuntimeError, "integrity"):
            session.evaluate(request(self.config))
        session.buffers.clear()
        with patch.dict(os.environ, {"CSC_UNDECLARED_SECRET": "bad"}):
            with self.assertRaisesRegex(RuntimeError, "integrity"):
                session.evaluate(request(self.config))

    def test_undeclared_persistent_model_state_rejected(self):
        session = WarmSession()
        session.task_state = {"queue_ns": 99}
        with self.assertRaisesRegex(RuntimeError, "integrity"):
            session.evaluate(request(self.config))
        del session.task_state
        session.version = 2
        with self.assertRaisesRegex(RuntimeError, "integrity"):
            session.evaluate(request(self.config))

    def test_completed_task_and_lifetime_recycle(self):
        for overrides in ({"worker_max_tasks": 1}, {"worker_max_lifetime_s": .001}):
            cfg = replace(self.config, **overrides)
            manager = BranchManager(cfg)
            try:
                first = manager._execute(request(cfg), 0)
                time.sleep(.003)
                second = manager._execute(request(cfg, 1), 0)
                self.assertEqual(first["status"], second["status"])
                self.assertNotEqual(first["runtime"]["pid"], second["runtime"]["pid"])
                self.assertGreaterEqual(manager.worker_recycles, 1)
                self.assertEqual(semantic(second), semantic(execute_shadow(request(cfg, 1))))
            finally:
                manager.close()

    def test_crash_and_timeout_destroy_then_replace(self):
        for fault in ("crash", "timeout"):
            cfg = replace(self.config, shadow_timeout_s=.5)
            manager = BranchManager(cfg)
            try:
                old = next(iter(manager.workers))
                req = request(cfg)
                req["fault"] = fault
                result = manager._execute(req, 0)
                self.assertEqual(result["status"], "TIMEOUT" if fault == "timeout" else "FAULTED")
                self.assertIsNotNone(old.process.poll())
                recovered = manager._execute(request(cfg, 1), 0)
                self.assertEqual(recovered["status"], "REPORTED")
                self.assertNotEqual(recovered["runtime"]["pid"], old.process.pid)
            finally:
                manager.close()

    def test_physical_worker_death_during_processing(self):
        cfg = replace(self.config, shadow_injected_delay_s=.2)
        manager = BranchManager(cfg)
        try:
            old = next(iter(manager.workers))
            timer = threading.Timer(.04, old.process.kill)
            timer.start()
            result = manager._execute(request(cfg), 0)
            timer.join()
            self.assertEqual(result["status"], "FAULTED")
            recovered = manager._execute(request(cfg, 1), 0)
            self.assertEqual(recovered["status"], "REPORTED")
            self.assertNotEqual(recovered["runtime"]["pid"], old.process.pid)
        finally:
            manager.close()

    def test_duplicate_stale_malformed_assignment_destroy(self):
        for fault in ("duplicate", "stale", "malformed", "wrong_anchor", "wrong_window"):
            manager = BranchManager(self.config)
            try:
                old = next(iter(manager.workers))
                req = request(self.config, 1)
                if fault in ("duplicate", "stale"):
                    self.assertEqual(manager._execute(req, 0)["status"], "REPORTED")
                if fault == "stale":
                    req = request(self.config, 0)
                if fault == "malformed":
                    req["events"] = [{"bad": True}]
                if fault == "wrong_anchor":
                    req["anchor"]["snapshot_id"] = "bad"
                if fault == "wrong_window":
                    req["branch"]["start_sequence"] += 1
                self.assertEqual(manager._execute(req, 0)["status"], "FAULTED")
                self.assertIsNotNone(old.process.poll())
                self.assertEqual(manager._execute(request(self.config, 2), 0)["status"], "REPORTED")
            finally:
                manager.close()

    def test_minimal_environment_has_no_production_credentials(self):
        from csc.warm import worker_environment
        with patch.dict(os.environ, {"CSC_PRODUCTION_TOKEN": "secret", "AWS_SECRET_ACCESS_KEY": "secret"}):
            env = worker_environment()
            self.assertNotIn("CSC_PRODUCTION_TOKEN", env)
            self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
            self.assertTrue(set(env).issubset({"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE"}))

    def test_continuous_hot_counts_bounded_and_production_equivalent(self):
        cfg = replace(self.config, duration_epochs=90, retention_completed_epochs=8,
                      production_period_s=.004, shadow_result_deadline_s=.3)
        with tempfile.TemporaryDirectory() as directory:
            path, summary = run(cfg, directory, "warm")
            _, baseline = run(replace(cfg, shadow_count=0, mirror_count=0, worker_mode="cold"), directory, "base")
            self.assertEqual(summary["production_semantic_sha256"], baseline["production_semantic_sha256"])
            with (path / "resource_metrics.jsonl").open() as stream:
                resources = [json.loads(line) for line in stream]
            for row in resources:
                self.assertLessEqual(row["retained_completed_epochs"], 8)
                self.assertLessEqual(row["duplicate_cache_size"], 8)
                self.assertLessEqual(row["resource_history_size"], 8)
                self.assertLessEqual(row["pending_epochs"], cfg.max_pending_epochs)
                self.assertLessEqual(row["active_shadow_tasks"], cfg.max_pending_shadow_tasks)
                self.assertLessEqual(row["worker_count"], cfg.max_shadow_slots)
            with (path / "cfr.jsonl").open() as stream:
                self.assertEqual(sum(1 for _ in stream), 90)


if __name__ == "__main__":
    unittest.main()
