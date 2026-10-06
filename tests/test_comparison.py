from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from csc.branches import MultiBranchScheduler, execute_shadow, outcome
from csc.compare import OutcomeComparisonEngine
from csc.contracts import Config, State, StateCaptureEngine
from csc.runner import run
from csc.sync import InputSynchronizationLayer
from csc.world import ProductionWorld, workload
from experiments.replay import replay
from experiments.runner import create_series_dir


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.config = Config(duration_epochs=1, warmup_epochs=0, horizon_ticks=3)
        self.anchor = StateCaptureEngine().capture(State(), "test", 0)
        self.plan = MultiBranchScheduler().plan(self.anchor, self.config, "test", 0, "NS_GREEN")
        events = list(workload(self.config, "test"))
        capability = object()
        world = ProductionWorld(State(), capability, self.config)
        world.apply_plan("NS_GREEN", capability, "test")
        _, sync = InputSynchronizationLayer().deliver(events, self.plan[0])
        trace = [world.step(e, i) for i, e in enumerate(events)]
        self.production = outcome(self.plan[0], self.anchor, world.snapshot_state(), trace, sync, {})
        self.shadows = [execute_shadow({"anchor": self.anchor.envelope(), "config": asdict(self.config),
                                        "branch": asdict(b), "events": [asdict(e) for e in events]}) for b in self.plan[1:]]

    def test_incomparable_windows_never_enter_regret(self):
        for field, bad_value in (("observation_window", [0, 1]), ("anchor_hash", "bad"), ("provenance", "REALISED"), ("action", "BALANCED")):
            with self.subTest(field=field):
                shadows = deepcopy(self.shadows)
                shadows[-1][field] = bad_value if shadows[-1].get(field) != bad_value else "NS_GREEN"
                cfr = OutcomeComparisonEngine(self.config).compare(self.anchor, self.plan, deepcopy(self.production), shadows)
                self.assertIn(self.plan[-1].branch_id, cfr["excluded"])
                self.assertIsNone(cfr["branches"][-1]["utility"])
                self.assertEqual(cfr["record_status"], "PARTIAL")

    def test_missing_production_no_record_and_mirror_fallback(self):
        comparator = OutcomeComparisonEngine(self.config)
        self.assertIsNone(comparator.compare(self.anchor, self.plan, None, self.shadows))
        first = comparator.compare(self.anchor, self.plan, self.production, self.shadows)
        second = comparator.compare(self.anchor, self.plan, self.production, self.shadows[1:])
        self.assertEqual(second["epsilon_source"], "ESTIMATED")
        self.assertEqual(first["epsilon"], second["epsilon"])
        self.assertEqual(second["record_status"], "PARTIAL")

    def test_replay_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as root:
            path, _ = run(self.config, root)
            result = replay(path)
            self.assertEqual(result["branches_replayed"], 4)
            with (path / "events.jsonl").open("a") as stream:
                stream.write("{}\n")
            with self.assertRaises(ValueError):
                replay(path)

    def test_replay_rejects_source_identity_mismatch(self):
        with tempfile.TemporaryDirectory() as root:
            path, _ = run(self.config, root)
            source_root = Path(root) / "source"
            shutil.copytree(Path(__file__).resolve().parents[1] / "csc", source_root / "csc")
            with (source_root / "csc" / "world.py").open("a") as stream:
                stream.write("\n# test source mismatch\n")
            with self.assertRaisesRegex(ValueError, "source identity mismatch"):
                replay(path, source_root)

    def test_matrix_series_directory_is_unique(self):
        with tempfile.TemporaryDirectory() as root:
            created = create_series_dir(root, "series-one")
            self.assertTrue(created.is_dir())
            with self.assertRaises(FileExistsError):
                create_series_dir(root, "series-one")

    def test_manifest_without_git_executable(self):
        from csc.store import KnowledgeStore
        with tempfile.TemporaryDirectory() as root:
            with patch("csc.store.subprocess.run", side_effect=FileNotFoundError):
                store = KnowledgeStore(root, self.config)
            self.assertIsNone(store.manifest["git_sha"])
            store.close()
