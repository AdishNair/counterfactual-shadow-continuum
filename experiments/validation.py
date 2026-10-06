"""Persist same-action, fidelity, ablation and fault-injection evidence."""
import argparse
from dataclasses import replace
import json
from pathlib import Path

from csc.contracts import Config
from csc.runner import run
from experiments.replay import read_lines, replay


def validate(root):
    config = Config(duration_epochs=8, warmup_epochs=0, failure_epoch=3, shadow_timeout_s=1)
    rows = []
    baseline_path, baseline = run(replace(config, shadow_count=0, mirror_count=0), root)
    for fault in ("none", "crash", "timeout", "drop", "duplicate", "reorder", "delay", "model_error", "resource_budget", "capture"):
        path, summary = run(replace(config, failure_scenario=fault, experiment_name=f"fault-{fault}"), root)
        identical = baseline["production_semantic_sha256"] == summary["production_semantic_sha256"]
        if not identical:
            raise AssertionError(f"production changed under {fault}")
        rows.append({"scenario": fault, "path": str(path), "production_matches_baseline": identical,
                     "excluded_branches": summary["excluded_branches"], "replay": replay(path)})
    path, _ = run(replace(config, shadow_count=0, mirror_count=2, experiment_name="two-mirrors"), root)
    comparisons, violations = 0, 0
    for cfr in read_lines(path / "cfr.jsonl"):
        mirrors = [b for b in cfr["branches"] if b["role"] == "MIRROR"]
        comparisons += 1
        violations += mirrors[0]["trace"] != mirrors[1]["trace"]
    if violations:
        raise AssertionError("same-action determinism violation")
    rows.append({"scenario": "two-mirrors", "path": str(path), "comparisons": comparisons, "violations": violations})
    for horizon in (2, 6, 20):
        path, summary = run(replace(config, horizon_ticks=horizon, workload_profile="incident", experiment_name=f"fidelity-h{horizon}"), root)
        rows.append({"scenario": "incident-fidelity", "horizon": horizon, "path": str(path), "fidelity_gap": summary["fidelity_gap"]})
    for label, changes in (("no-mirror", {"mirror_count": 0}), ("no-sync-reorder", {"synchronization_enabled": False, "failure_scenario": "reorder"}),
                           ("biased-sem", {"shadow_service_rate": 4}), ("exact-control", {"production_heterogeneity": False})):
        path, summary = run(replace(config, experiment_name=label, **changes), root)
        rows.append({"scenario": label, "path": str(path), "summary": summary})
    result = {"scope": "short local validation; not full cluster E3/E6/E7 protocol", "baseline": str(baseline_path), "runs": rows}
    Path(root, "validation-summary.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/validation")
    args = parser.parse_args()
    print(json.dumps(validate(args.output), indent=2))
