"""Disposable deterministic machinery tests; never Gate A measurements."""
from collections import Counter
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from csc.contracts import canonical, digest
from csc.store import KnowledgeStore
from experiments import cycle6_campaign as campaign
from experiments.cycle6_faults import optional_fault


class Cycle6CampaignTests(unittest.TestCase):
    def test_short_campaign_does_not_apply_continuous_capacity_preflight(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "new-parent" / "series"
            metadata = {"registry": [], "source_hashes": {}, "configs": {}, "config_hashes": {}}
            with patch.object(campaign, "capacity") as forbidden, \
                 patch.object(campaign, "prepare", return_value=metadata), \
                 patch.object(campaign, "atomic"):
                result = campaign.execute(target, "gate")
            forbidden.assert_not_called()
            self.assertTrue(target.parent.is_dir())

    def test_continuous_run_requires_frozen_capacity_threshold(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "series"
            row = {"run_id": "continuous", "kind": "continuous"}
            metadata = {"registry": [row], "source_hashes": {}, "configs": {"continuous": {}},
                        "config_hashes": {"continuous": {}}}
            with patch.object(campaign, "prepare", return_value=metadata), \
                 patch.object(campaign, "capacity", return_value={"free_disk_bytes": 3 * campaign.GIB,
                                                                   "available_memory_bytes": campaign.GIB}), \
                 patch.object(campaign, "atomic"):
                result = campaign.execute(target, "gate")
            self.assertEqual(result["status"], "HAS_FAILED_OR_UNATTEMPTED_RUNS")

    def test_exact_registry_and_seed_units(self):
        rows = campaign.registry()
        self.assertEqual(len(rows), 70)
        self.assertEqual(len({r["run_id"] for r in rows}), 70)
        self.assertEqual(Counter(r["kind"] for r in rows), dict(factorial=54, storage_fault=15, continuous=1))
        self.assertEqual([r["order"] for r in rows], list(range(70)))
        for seed in (26001, 26002, 26003):
            block = [r for r in rows if r["seed"] == seed]
            self.assertEqual(Counter(r["mode"] for r in block), dict(k0=4, warm1=7, warm2=7))
        self.assertEqual(rows, campaign.registry())

    def test_config_frozen_contract(self):
        for row in campaign.registry():
            config = campaign.configuration(row)
            self.assertEqual(config.shadow_result_deadline_s, .3)
            self.assertEqual(config.production_period_s, .04)
            self.assertEqual(config.horizon_ticks, 6)
            self.assertEqual(config.evidence_spool_max_items, 256)
            self.assertEqual(config.evidence_spool_max_bytes, 16 * 1024 * 1024)
            if row["mode"] == "k0":
                self.assertEqual((config.shadow_count, config.mirror_count), (0, 0))
            if row["condition"] == "capacity1":
                self.assertEqual((config.max_shadow_slots, config.max_pending_shadow_tasks), (1, 1))
        long = campaign.configuration(campaign.registry()[-1])
        self.assertEqual((long.duration_epochs, long.warmup_epochs), (10000, 500))

    def test_gate_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeError, "explicit"):
                campaign.prepare(Path(td) / "series", None)
            self.assertFalse((Path(td) / "series").exists())

    def test_gate_runtime_mismatch_rejected_before_directory(self):
        with tempfile.TemporaryDirectory() as td:
            gate = Path(td) / "gate.json"
            gate.write_bytes(canonical(dict(gate_passed=True, exit_code=0, source_hashes={}, source_identity_sha256=digest({}))))
            with self.assertRaisesRegex(RuntimeError, "identity mismatch"):
                campaign.prepare(Path(td) / "series", gate)
            self.assertFalse((Path(td) / "series").exists())

    def archive(self, path):
        source = path / "source"
        source.mkdir()
        (source / "fixture.py").write_text("stable")
        config = {"id": {"duration_epochs": 8}}
        rows = [dict(run_id="id")]
        hashes = {"fixture.py": campaign.sha(source / "fixture.py")}
        meta = dict(registry=rows, registry_sha256=digest(rows), source_hashes=hashes,
                    source_identity_sha256=digest(hashes), configs=config,
                    config_hashes={"id": digest(config["id"])})
        campaign.atomic(path / "preregistration.json", meta)
        return meta

    def test_archive_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            self.archive(path)
            campaign.verify_archive(path)
            (path / "source/fixture.py").write_text("tampered")
            with self.assertRaisesRegex(RuntimeError, "source mismatch"):
                campaign.verify_archive(path)

    def test_config_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            meta = self.archive(path)
            meta["configs"]["id"]["duration_epochs"] = 9
            campaign.atomic(path / "preregistration.json", meta)
            with self.assertRaisesRegex(RuntimeError, "config mismatch"):
                campaign.verify_archive(path)

    def test_run_one_requires_archive_execution(self):
        with tempfile.TemporaryDirectory() as td:
            self.archive(Path(td))
            with self.assertRaisesRegex(RuntimeError, "archived source"):
                campaign.run_one(td, "id")

    def test_helper_cleanup_attempts_all_steps(self):
        proc = MagicMock(returncode=-9)
        proc.wait.side_effect = [subprocess.TimeoutExpired("helper", 10), subprocess.TimeoutExpired("helper", 2), 0]
        proc.terminate.side_effect = PermissionError("injected")
        with tempfile.TemporaryDirectory() as td:
            cleanup = campaign.stop_helper(proc, Path(td))
        self.assertTrue(cleanup["reaped"])
        proc.kill.assert_called_once()
        self.assertTrue(cleanup["errors"])

    def test_communication_error_triggers_owned_cleanup(self):
        proc = MagicMock(pid=12345)
        proc.communicate.side_effect = OSError("pipe failure")
        with patch.object(campaign.subprocess, "Popen", return_value=proc), patch.object(campaign, "terminate_tree", return_value=[]) as cleanup:
            with self.assertRaisesRegex(RuntimeError, "pipe failure"):
                campaign.execute_child(["fixture"], Path("."), {}, 1)
            cleanup.assert_called_once_with(proc)

    def test_campaign_failed_attempt_blocks_later_ownership(self):
        rows = [dict(run_id="first", kind="factorial"), dict(run_id="second", kind="factorial")]
        meta = dict(registry=rows, configs={"first": dict(duration_epochs=8)}, status="PREREGISTERED_NOT_STARTED")
        with tempfile.TemporaryDirectory() as td, patch.object(campaign, "prepare", return_value=meta), patch.object(campaign, "verify_archive"), patch.object(campaign, "execute_child", side_effect=RuntimeError("uncertain cleanup")) as child:
            result = campaign.execute(td, "fixture", smoke=True)
            statuses = json.loads((Path(td) / "execution_status.json").read_text())
            self.assertEqual([s["status"] for s in statuses], ["FAILED", "NOT_ATTEMPTED"])
            self.assertEqual(child.call_count, 1)
            self.assertEqual(result["status"], "HAS_FAILED_OR_UNATTEMPTED_RUNS")

    def test_storage_helper_exact_scratch_duty_and_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            proc = subprocess.Popen([sys.executable, "-m", "experiments.cycle6_pressure", "storage", td],
                                    creationflags=subprocess.CREATE_NO_WINDOW if campaign.os.name == "nt" else 0)
            try:
                deadline = time.monotonic() + 10
                while not (directory / "scratch.bin").exists():
                    self.assertIsNone(proc.poll())
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(.01)
            finally:
                campaign.stop_helper(proc, directory)
            final = json.loads((directory / "final.json").read_text())
            self.assertEqual(final["scratch_file_bytes"], 8 * 1024 * 1024)
            self.assertEqual(final["written_bytes"], final["iterations"] * 8 * 1024 * 1024)
            self.assertEqual(final["exit_state"], "COOPERATIVE_STOP")

    @unittest.skipUnless(campaign.os.name == "nt", "Windows owned descendant cleanup")
    def test_timeout_reaps_real_owned_descendant_with_preopened_handle(self):
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handles = []
        original = subprocess.Popen
        with tempfile.TemporaryDirectory() as td:
            pid_path = Path(td) / "owned-child.pid"
            script = ("import pathlib,subprocess,sys,time; "
                      "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']); "
                      "pathlib.Path(sys.argv[1]).write_text(str(child.pid)); time.sleep(60)")
            command = [sys.executable, "-c", script, str(pid_path)]
            def spawn(args, **kwargs):
                proc = original(args, **kwargs)
                if args == command:
                    deadline = time.monotonic() + 10
                    while not pid_path.is_file():
                        if proc.poll() is not None or time.monotonic() >= deadline:
                            proc.kill()
                            proc.wait(timeout=5)
                            self.fail("owned descendant fixture failed to start")
                        time.sleep(.01)
                    pid = int(pid_path.read_text())
                    handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE before cleanup.
                    if not handle:
                        campaign.terminate_tree(proc)
                        self.fail("cannot open owned descendant handle before cleanup: " + str(ctypes.get_last_error()))
                    handles.append(handle)
                return proc
            try:
                with patch.object(campaign.subprocess, "Popen", side_effect=spawn):
                    with self.assertRaisesRegex(RuntimeError, "TimeoutExpired"):
                        campaign.execute_child(command, campaign.ROOT, dict(campaign.os.environ), .1)
                self.assertEqual(len(handles), 1)
                self.assertEqual(kernel.WaitForSingleObject(handles[0], 5000), 0,
                                 "owned descendant did not exit after tree cleanup")
            finally:
                for handle in handles:
                    kernel.CloseHandle(handle)


class Cycle6FaultTests(unittest.TestCase):
    def test_write_attempt_fault_boundaries_and_restoration(self):
        for case, expected in (("control", []), ("preappend", [25]),
                               ("temporary", list(range(25, 75))), ("sustained", list(range(25, 81)))):
            with patch.object(KnowledgeStore, "_write_optional", return_value=None) as original:
                original_function = KnowledgeStore._write_optional
                failed = []
                with optional_fault(case) as state:
                    store = object.__new__(KnowledgeStore)
                    for attempt in range(1, 81):
                        try:
                            store._write_optional("cfr.jsonl", b"{}\n")
                        except OSError:
                            failed.append(attempt)
                self.assertIs(KnowledgeStore._write_optional, original_function)
                self.assertEqual(failed, expected)
                self.assertEqual(state["injected"], len(expected))
                self.assertEqual(original.call_count, 80 - len(expected))

    def test_torn_write_restores_valid_boundary_and_retry(self):
        stream = BytesIO(b'{"old":1}\n')
        store = object.__new__(KnowledgeStore)
        store._open_evidence_stream = lambda name: stream
        with patch.object(KnowledgeStore, "_write_optional", return_value=None) as original:
            with optional_fault("torn") as state:
                for _ in range(24):
                    store._write_optional("cfr.jsonl", b'{"new":2}\n')
                with self.assertRaises(OSError):
                    store._write_optional("cfr.jsonl", b'{"new":2}\n')
                self.assertEqual(stream.getvalue(), b'{"old":1}\n')
                store._write_optional("cfr.jsonl", b'{"new":2}\n')
                self.assertEqual(state["attempts"], 26)
                self.assertGreater(state["torn_bytes"], 0)
                self.assertEqual(original.call_count, 25)

    def test_faults_never_touch_required_stream(self):
        with optional_fault("sustained"):
            with self.assertRaisesRegex(ValueError, "required stream"):
                object.__new__(KnowledgeStore)._write_optional("epoch_journal.jsonl", b"{}\n")


if __name__ == "__main__":
    unittest.main()
