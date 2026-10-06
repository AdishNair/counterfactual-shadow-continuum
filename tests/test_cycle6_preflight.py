"""Bounded Cycle 6 gate for queue-byte and optional-evidence isolation."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from csc.contracts import Config
from csc.executor import BoundedExecutor, ExecutorCapacityError
from csc.runner import run
from csc.store import KnowledgeStore


class Cycle6PreflightTests(unittest.TestCase):
    def config(self, **changes):
        return replace(Config(duration_epochs=4, warmup_epochs=0, horizon_ticks=1,
                              execution_mode="asynchronous", worker_mode="warm",
                              shadow_count=1, mirror_count=1, shadow_result_deadline_s=.2,
                              evidence_spool_drain_s=.5), **changes).validate()

    def test_executor_accounts_bytes_and_rejects_without_admission(self):
        release = threading.Event()
        executor = BoundedExecutor(1, 2, 100)
        first = executor.submit(release.wait, 1, _resident_bytes=60)
        deadline = time.monotonic() + 1
        while not first.running() and time.monotonic() < deadline:
            time.sleep(.001)
        with self.assertRaisesRegex(ExecutorCapacityError, "physical_byte_capacity"):
            executor.submit(lambda: None, _resident_bytes=41)
        state = executor.state()
        self.assertEqual(state["physical_inflight_bytes"], 60)
        self.assertEqual(state["physical_byte_rejections"], 1)
        self.assertEqual(state["physical_high_water_inflight_bytes"], 60)
        release.set()
        executor.shutdown(timeout=1)
        self.assertEqual(executor.state()["physical_inflight_bytes"], 0)

    def test_cancelled_queue_releases_bytes_only_on_physical_removal(self):
        release = threading.Event()
        executor = BoundedExecutor(1, 2, 100)
        first = executor.submit(release.wait, 1, _resident_bytes=40)
        second = executor.submit(lambda: None, _resident_bytes=50)
        second.cancel()
        self.assertEqual(executor.state()["physical_inflight_bytes"], 90)
        release.set()
        executor.shutdown(timeout=1)
        self.assertEqual(executor.state()["physical_inflight_bytes"], 0)

    def test_optional_evidence_spool_persists_and_reports_bounds(self):
        with tempfile.TemporaryDirectory() as root:
            store = KnowledgeStore(root, self.config(), "spool")
            self.assertEqual(store.append_evidence("cfr.jsonl", {"epoch": 1}, "e1"), "PENDING")
            self.assertTrue(store.drain_evidence(1))
            state = store.evidence_state()
            self.assertEqual(state["evidence_dispositions"]["PERSISTED"], 1)
            self.assertLessEqual(state["evidence_spool_high_water_items"], 1)
            store.close()
            self.assertEqual(json.loads((Path(root) / "spool/cfr.jsonl").read_text())["epoch"], 1)
            delivery = json.loads((Path(root) / "spool/evidence_delivery.jsonl").read_text())
            self.assertEqual((delivery["record_id"], delivery["status"]), ("e1", "PERSISTED"))

    def test_optional_evidence_failure_is_terminal_without_raising(self):
        with tempfile.TemporaryDirectory() as root:
            store = KnowledgeStore(root, self.config(evidence_spool_max_attempts=2), "failed")
            with patch.object(store, "_write_optional", side_effect=OSError("unavailable")):
                self.assertEqual(store.append_evidence("cfr.jsonl", {"epoch": 1}, "e1"), "PENDING")
                self.assertTrue(store.drain_evidence(1))
            self.assertEqual(store.evidence_state()["evidence_dispositions"]["FAILED"], 1)
            store.close()
            delivery = json.loads((Path(root) / "failed/evidence_delivery.jsonl").read_text())
            self.assertEqual((delivery["record_id"], delivery["status"], delivery["attempts"]),
                             ("e1", "FAILED", 2))

    def test_partial_line_is_rolled_back_before_retry(self):
        with tempfile.TemporaryDirectory() as root:
            store = KnowledgeStore(root, self.config(evidence_spool_max_attempts=2), "torn")
            path = store.path / "cfr.jsonl"
            original = store._write_optional
            calls = [0]
            def torn_once(name, line):
                calls[0] += 1
                if calls[0] == 1:
                    stream = store._open_evidence_stream(name)
                    stream.write(line[:5])
                    stream.flush()
                    stream.close()
                    store.evidence_streams.pop(name, None)
                    raise OSError("torn append")
                return original(name, line)
            with patch.object(store, "_write_optional", side_effect=torn_once):
                store.append_evidence("cfr.jsonl", {"epoch": 7}, "e7")
                self.assertTrue(store.drain_evidence(1))
            store.close()
            lines = path.read_text().splitlines()
            self.assertEqual(lines, ['{"epoch":7}'])

    def test_sustained_optional_failure_does_not_stop_production(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(KnowledgeStore, "_write_optional", side_effect=OSError("offline")):
                path, summary = run(self.config(evidence_spool_max_attempts=1), root, "isolation")
            manifest = json.loads((path / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "COMPLETE")
            self.assertEqual(summary["epochs_total"], 4)
            self.assertGreater(manifest["evidence_persistence"]["evidence_dispositions"]["FAILED"], 0)


if __name__ == "__main__":
    unittest.main()
