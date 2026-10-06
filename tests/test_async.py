"""Meaningful async invariants with deterministic fake completions and real workers."""
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
import json
import hashlib
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from csc.branches import MultiBranchScheduler, execute_shadow, outcome
from csc.compare import OutcomeComparisonEngine
from csc.contracts import Config, State, StateCaptureEngine
from csc.pending import PendingShadowLedger, transition
from csc.runner import run
from csc.store import KnowledgeStore
from csc.sync import InputSynchronizationLayer
from csc.world import ProductionWorld, workload
from experiments.replay import replay


class FakeStore:
    def __init__(self):
        self.entries = []
    def append(self, name, value):
        self.entries.append((name, value))


class FakeManager:
    def __init__(self):
        self.requests, self.futures, self.ledger = [], [], {}
    def launch(self, branches, anchor, events):
        output = []
        for branch in branches:
            future = Future()
            self.futures.append(future)
            self.requests.append(dict(anchor=anchor.envelope(), branch=branch.__dict__, events=[e.__dict__ for e in events]))
            output.append((branch, future))
        return output
    def close(self):
        for future in self.futures:
            future.cancel()


class AsyncTests(unittest.TestCase):
    def setUp(self):
        self.config = Config(duration_epochs=3, warmup_epochs=0, horizon_ticks=2, shadow_count=1,
                             execution_mode="asynchronous", shadow_result_deadline_s=.2)
        self.now = [10.]
        self.store, self.manager = FakeStore(), FakeManager()
        self.ledger = PendingShadowLedger(self.config, self.manager, OutcomeComparisonEngine(self.config), self.store, lambda: self.now[0])

    def package(self, epoch=0, eid="test"):
        state = State(input_sequence_watermark=epoch * 2 - 1)
        anchor = StateCaptureEngine().capture(state, eid, epoch)
        branches = MultiBranchScheduler().plan(anchor, self.config, eid, epoch, "NS_GREEN")
        events = list(workload(self.config, eid))[epoch * 2:epoch * 2 + 2]
        cap = object()
        world = ProductionWorld(state, cap, self.config)
        world.apply_plan("NS_GREEN", cap, "test")
        delivered, sync = InputSynchronizationLayer().deliver(events, branches[0])
        trace = [world.step(event, i) for i, event in enumerate(delivered)]
        production = outcome(branches[0], anchor, world.snapshot_state(), trace, sync, {})
        self.ledger.commit(anchor, branches, events, production)
        return self.ledger.pending.get(epoch), branches

    def result(self, index):
        return execute_shadow({**self.manager.requests[index], "config": self.config.__dict__})

    def records(self):
        return [v for n, v in self.store.entries if n == "cfr.jsonl"]

    def test_out_of_order_join_and_duplicates(self):
        p0, b0 = self.package(0)
        p1, b1 = self.package(1)
        for i in (2, 3):
            self.manager.futures[i].set_result(self.result(i))
        self.ledger.poll()
        self.assertEqual(self.records(), [])
        for i in (0, 1):
            self.manager.futures[i].set_result(self.result(i))
        self.ledger.poll()
        self.assertEqual([r["epoch"] for r in self.records()], [0, 1])
        self.ledger.accept(p0, b0[1], self.result(0))
        self.assertEqual(self.ledger.counts["DUPLICATE"], 1)
        self.assertEqual(len(self.records()), 2)

    def test_bad_epoch_anchor_action_window_input_provenance(self):
        for key, value in (("epoch", 1), ("anchor_hash", "wrong"), ("action", "BALANCED"),
                           ("observation_window", [9, 10]), ("provenance", "REALISED")):
            with self.subTest(key=key):
                self.setUp()
                package, branches = self.package()
                bad = self.result(0)
                bad[key] = value
                original = json.dumps(package["production"], sort_keys=True)
                self.ledger.accept(package, branches[1], bad)
                self.assertEqual(package["states"][branches[1].branch_id], "REJECTED")
                self.assertEqual(original, json.dumps(package["production"], sort_keys=True))

    def test_expiry_cannot_resurrect_or_actuate(self):
        package, branches = self.package()
        result = self.result(0)
        original = json.dumps(package["production"], sort_keys=True)
        self.now[0] += 1
        self.ledger.poll()
        original = json.dumps(package["production"], sort_keys=True)
        frozen = json.dumps(self.records(), sort_keys=True)
        self.ledger.accept(package, branches[1], result)
        self.assertEqual(json.dumps(self.records(), sort_keys=True), frozen)
        self.assertEqual(original, json.dumps(package["production"], sort_keys=True))
        self.assertEqual(self.ledger.counts["LATE"], 1)
        self.assertIsNone(self.records()[0]["regret_raw"])

    def test_capacity_retains_running_permit_after_expiry(self):
        self.config.max_pending_shadow_tasks = 2
        package, _ = self.package()
        for future in self.manager.futures:
            future.set_running_or_notify_cancel()
        self.now[0] += 1
        self.ledger.poll()
        self.package(1)
        self.assertEqual(self.ledger.counts["DROPPED"], 2)
        self.assertEqual(len(self.ledger.active), 2)
        self.assertEqual(self.ledger.max_active, 2)
        self.assertEqual(len(self.records()), 2)

    def test_illegal_transitions_and_idempotence(self):
        self.assertEqual(transition("COMPLETED", "COMPLETED"), "DUPLICATE")
        for previous in ("EXPIRED", "DROPPED", "FAILED", "REJECTED", "TIMED_OUT"):
            with self.assertRaises(ValueError):
                transition(previous, "COMPLETED")

    def test_malformed_output_and_service_unavailable_are_terminal(self):
        package, branches = self.package()
        self.manager.futures[0].set_result({"nonsense": True})
        self.manager.futures[1].set_exception(ConnectionError("service unavailable"))
        self.ledger.poll()
        self.assertEqual(self.records()[0]["record_status"], "PRODUCTION_ONLY")
        self.assertEqual(self.ledger.counts["REJECTED"], 1)
        self.assertEqual(self.ledger.counts["FAILED"], 1)

    def test_well_identified_malformed_metrics_are_rejected(self):
        package, branches = self.package()
        result = self.result(0)
        result["metrics"] = {"mean_queue": float("nan")}
        self.ledger.accept(package, branches[1], result)
        self.assertEqual(package["states"][branches[1].branch_id], "REJECTED")

    def test_duplicate_epoch_commit_rejected(self):
        self.package()
        with self.assertRaises(ValueError):
            self.package()
        self.assertEqual(sum(n == "epoch_journal.jsonl" for n, _ in self.store.entries), 1)

    def test_next_epoch_opens_before_previous_shadow_completion(self):
        seen = []
        manager = self.manager
        from csc.safety import ActuatorGateway
        original = ActuatorGateway.open_epoch
        def opened(gateway, epoch, branch_id):
            # Cancellation on evidence expiry is not shadow completion.
            seen.append((epoch, any(f.done() and not f.cancelled() for f in manager.futures)))
            return original(gateway, epoch, branch_id)
        with tempfile.TemporaryDirectory() as directory:
            with patch("csc.async_runner.BranchManager", return_value=manager), patch.object(ActuatorGateway, "open_epoch", opened):
                run(replace(self.config, shadow_result_deadline_s=.02), directory, "nonwait")
        self.assertEqual(seen, [(0, False), (1, False), (2, False)])

    def test_shutdown_inflight_and_worker_restart(self):
        package, branches = self.package()
        self.ledger.expire(package, "shutdown")
        self.ledger.finalize()
        self.manager.close()
        self.assertTrue(all(f.cancelled() for f in self.manager.futures))
        self.assertEqual(self.records()[0]["evidence_completeness"], "EXPIRED_OR_MISSING")
        # Stateless new worker receives exactly the same serialized package.
        first, restarted = self.result(0), self.result(0)
        self.assertEqual(first["trace"], restarted["trace"])
        self.ledger.accept(package, branches[1], restarted)
        self.assertEqual(len(self.records()), 1)

    def test_restart_store_reopen_and_stale_delivery(self):
        package, branches = self.package()
        result = self.result(0)
        self.ledger.expire(package, "shutdown")
        self.ledger.finalize()
        self.ledger.closed = True
        self.ledger.accept(package, branches[1], result)
        with tempfile.TemporaryDirectory() as directory:
            first = KnowledgeStore(directory, self.config, "old")
            first.close()
            with self.assertRaises(FileExistsError):
                KnowledgeStore(directory, self.config, "old")
            new = KnowledgeStore(directory, self.config, "new")
            fresh = PendingShadowLedger(self.config, FakeManager(), OutcomeComparisonEngine(self.config), new)
            self.assertFalse(fresh.valid_identity(package, replace(branches[1], experiment_id="new"), result))
            new.close()
            # Reopening raw old artifacts read-only cannot reopen a coordinator writer.
            self.assertEqual(json.loads((Path(directory) / "old/manifest.json").read_text())["status"], "COMPLETE")

    def test_single_writer_and_atomic_json(self):
        with tempfile.TemporaryDirectory() as directory:
            store = KnowledgeStore(directory, self.config, "single")
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(store.append, "cfr.jsonl", {"epoch": i}) for i in range(8)]
                for future in futures:
                    with self.assertRaises(RuntimeError):
                        future.result()
            for i in range(8):
                store.append("cfr.jsonl", {"epoch": i})
            store.write_json("atomic.json", {"finished": True})
            store.close()
            self.assertEqual(len((store.path / "cfr.jsonl").read_text().splitlines()), 8)
            self.assertFalse((store.path / "atomic.json.tmp").exists())

    def test_actual_delay_timeout_crash_trajectory_and_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline, expected = run(replace(self.config, shadow_count=0, mirror_count=0), directory, "baseline")
            for fault in ("none", "timeout", "crash"):
                config = replace(self.config, failure_scenario=fault, failure_epoch=0, shadow_injected_delay_s=.04,
                                 shadow_timeout_s=.3, shadow_result_deadline_s=.1)
                started = time.perf_counter()
                original_result = Future.result
                def completed_result(future, *args, **kwargs):
                    self.assertTrue(future.done(), "async path waited for unfinished evidence")
                    return original_result(future, *args, **kwargs)
                with patch.object(Future, "result", completed_result):
                    path, summary = run(config, directory, fault)
                self.assertLess(time.perf_counter() - started, 4)
                self.assertEqual(summary["production_semantic_sha256"], expected["production_semantic_sha256"])
                self.assertEqual(summary["workload_sha256"], expected["workload_sha256"])
                self.assertEqual(summary["unauthorized_production_mutations_from_shadow"], 0)
                self.assertEqual(replay(path)["trajectory_mismatches"], 0)
                resources = [json.loads(line) for line in (path / "resource_metrics.jsonl").read_text().splitlines()]
                self.assertTrue(all(r["barrier_ms"] == 0 for r in resources))

    def test_sync_remains_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            cfg = replace(self.config, execution_mode="synchronous")
            p1, s1 = run(cfg, directory, "sync1")
            p2, s2 = run(cfg, directory, "sync2")
            self.assertEqual(s1["production_semantic_sha256"], s2["production_semantic_sha256"])
            self.assertEqual(replay(p1)["trajectory_mismatches"], 0)
            self.assertEqual(replay(p2)["trajectory_mismatches"], 0)

    def test_finite_metrics_with_overflowing_utility_are_rejected(self):
        self.config = replace(self.config, wait_weight=1)
        self.ledger.config = self.config
        self.ledger.comparator = OutcomeComparisonEngine(self.config)
        package, branches = self.package()
        for location in ("metrics", "trace"):
            oversized = self.result(0)
            if location == "metrics":
                oversized["metrics"]["mean_queue"] = 10 ** 400
            else:
                oversized["trace"][0]["queue_ns"] = 10 ** 400
            self.assertFalse(self.ledger.valid_identity(package, branches[1], oversized))
        overflowing_distance = self.result(0)
        overflowing_distance["trace"][0].update(queue_ns=1.7e308, queue_ew=1.7e308)
        self.assertFalse(self.ledger.valid_identity(package, branches[1], overflowing_distance))
        forged = self.result(0)
        forged["metrics"].update(mean_queue=1e308, waiting_vehicle_ticks=1e308)
        self.manager.futures[0].set_result(forged)
        self.manager.futures[1].set_result(self.result(1))
        self.ledger.poll()
        self.assertEqual(package["states"][branches[1].branch_id], "REJECTED")
        record = self.records()[0]
        self.assertIsNone(record["epsilon"])
        self.assertIsNone(record["regret_raw"])
        # The next authoritative epoch can still commit despite bad old evidence.
        self.package(epoch=1)
        self.assertIn(1, self.ledger.pending)

    def test_journal_join_rejects_tampering_even_with_rehashed_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            path, _ = run(replace(self.config, shadow_count=0, mirror_count=0), directory, "join")
            journal = path / "epoch_journal.jsonl"
            entries = [json.loads(line) for line in journal.read_text().splitlines()]
            entries[0]["anchor_hash"] = "incorrect"
            journal.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8")
            manifest = json.loads((path / "manifest.json").read_text())
            manifest["artifact_hashes"]["epoch_journal.jsonl"] = hashlib.sha256(journal.read_bytes()).hexdigest()
            (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "journal mismatch"):
                replay(path)


if __name__ == "__main__":
    unittest.main()
