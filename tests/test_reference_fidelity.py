from dataclasses import replace
import ast
from pathlib import Path
import tempfile
import unittest

from csc.contracts import Config
from csc.runner import run
from experiments.reference_fidelity import analyze_run
from experiments.reference_fidelity_factorial import evaluate_anchor, make_anchor
from experiments.reference_oracle import REFERENCE_KIND


class ReferenceFidelityTests(unittest.TestCase):
    def test_all_actions_are_evaluated_against_production_reference(self):
        config = Config(duration_epochs=2, warmup_epochs=0, horizon_ticks=3, shadow_count=2, mirror_count=1)
        with tempfile.TemporaryDirectory() as root:
            path, _ = run(config, root)
            analysis = analyze_run(path)
        self.assertEqual(len(analysis["epoch_rows"]), 2)
        self.assertEqual(len(analysis["branch_rows"]), 8)
        self.assertTrue(all(row["reference_kind"] == "AUTHORED_SOFTWARE_ENVIRONMENT" for row in analysis["branch_rows"]))
        self.assertTrue(all(row["epsilon_covers_selected_error"] in (True, False) for row in analysis["epoch_rows"]))

    def test_factorial_anchor_evaluates_all_actions_with_sem_independent_reference(self):
        design = {"max_horizon_ticks": 3, "anchor_history_ticks": 2, "tie_tolerance": 1e-9}
        _, anchor, events = make_anchor(901, "peak", "blocked_ew", 0, design)
        observation, action_rows = evaluate_anchor(
            "test-run", 901, "peak", "blocked_ew", "aligned-control", 3, 0, anchor, events,
            {"production_heterogeneity": False, "shadow_service_rate": 2, "model_incidents": True}, design, 1.0)
        self.assertTrue(observation["comparable"])
        self.assertEqual({row["action"] for row in action_rows}, {"NS_GREEN", "EW_GREEN", "BALANCED"})
        self.assertTrue(all(row["reference_kind"] == REFERENCE_KIND for row in action_rows))
        self.assertIn(observation["recommendation_outcome"], {"TP", "FP", "FN", "TN"})

    def test_reference_oracle_does_not_import_shadow_model(self):
        source = Path("experiments/reference_oracle.py").read_text(encoding="utf-8")
        imports = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ImportFrom)]
        self.assertFalse(any(node.module == "csc.world" and any(alias.name == "ShadowWorldModel" for alias in node.names)
                             for node in imports))


if __name__ == "__main__":
    unittest.main()
