"""Evaluate shadow estimates against all-action reference replays in J1's software world.

The reference path imports ProductionWorld but never ShadowWorldModel. It is an
independent oracle only for this authored software environment, not physical
counterfactual ground truth.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from csc.compare import utility
from csc.contracts import ACTIONS, Anchor, Config, Event, canonical
from csc.runner import run
from csc.world import ProductionWorld, domain_metrics
from experiments.replay import read_lines, replay
from experiments.runner import create_series_dir, write_json


def write_jsonl(path, values):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        for value in values:
            stream.write(canonical(value).decode() + "\n")


def load_epoch_inputs(run_path):
    anchors = {row["snapshot_id"]: Anchor.from_envelope(row) for row in read_lines(run_path / "anchors.jsonl")}
    events = defaultdict(list)
    for row in read_lines(run_path / "events.jsonl"):
        events[row["epoch"]].append(Event(**row))
    return anchors, events


def reference_trace(anchor, action, events, config):
    capability = object()
    world = ProductionWorld(anchor.hydrate(), capability, config)
    world.apply_plan(action, capability, "reference-only")
    return [world.step(event, tick) for tick, event in enumerate(events)]


def analyze_run(run_path):
    """Return branch-level reference errors and epoch-level gate/ranking diagnostics."""
    run_path = Path(run_path)
    replay_result = replay(run_path)
    manifest = json.loads((run_path / "manifest.json").read_text())
    config = Config(**manifest["config"])
    anchors, events_by_epoch = load_epoch_inputs(run_path)
    branch_rows, epoch_rows = [], []
    for cfr in read_lines(run_path / "cfr.jsonl"):
        branches = [branch for branch in cfr["branches"] if branch.get("status") == "REPORTED" and branch.get("utility") is not None]
        action_set = {branch["action"] for branch in branches}
        if not set(ACTIONS).issubset(action_set):
            raise ValueError(f"all-action reference requires complete action coverage at epoch {cfr['epoch']}")
        anchor, events = anchors[cfr["anchor_hash"]], events_by_epoch[cfr["epoch"]]
        reference_by_action = {}
        for action in ACTIONS:
            trace = reference_trace(anchor, action, events, config)
            reference_by_action[action] = utility(domain_metrics(trace), config)
        production_branch = next(branch for branch in branches if branch["role"] == "PRODUCTION")
        production_reference = reference_by_action[production_branch["action"]]
        alternative_estimates, alternative_references = {}, {}
        for branch in branches:
            reference_utility = reference_by_action[branch["action"]]
            estimated_utility = branch["utility"]
            row = {"experiment_id": cfr["experiment_id"], "epoch": cfr["epoch"],
                   "branch_id": branch["branch_id"], "role": branch["role"], "action": branch["action"],
                   "estimated_utility": estimated_utility, "reference_utility": reference_utility,
                   "signed_error": estimated_utility - reference_utility,
                   "absolute_error": abs(estimated_utility - reference_utility),
                   "epsilon": cfr["epsilon"], "horizon_ticks": cfr["horizon_ticks"],
                   "reference_kind": "AUTHORED_SOFTWARE_ENVIRONMENT"}
            branch_rows.append(row)
            if branch["role"] == "SHADOW":
                alternative_estimates[branch["action"]] = estimated_utility
                alternative_references[branch["action"]] = reference_utility
        best_estimated = max(alternative_estimates, key=alternative_estimates.get)
        best_reference = max(alternative_references, key=alternative_references.get)
        estimate_gain = alternative_estimates[best_estimated] - cfr["u_real"]
        reference_gain = alternative_references[best_estimated] - production_reference
        gate_passed = cfr["epsilon"] is not None and estimate_gain > cfr["epsilon"]
        epoch_rows.append({"experiment_id": cfr["experiment_id"], "epoch": cfr["epoch"],
                           "horizon_ticks": cfr["horizon_ticks"], "epsilon": cfr["epsilon"],
                           "best_estimated_action": best_estimated, "best_reference_action": best_reference,
                           "ranking_agrees": best_estimated == best_reference,
                           "epsilon_gate_passed": gate_passed,
                           "selected_reference_improvement": reference_gain > 0,
                           "selected_reference_gain": reference_gain,
                           "epsilon_covers_selected_error": abs(estimate_gain - reference_gain) <= cfr["epsilon"] if cfr["epsilon"] is not None else None})
    return {"run_path": str(run_path), "replay": replay_result, "branch_rows": branch_rows, "epoch_rows": epoch_rows}


def median(values):
    values = sorted(values)
    if not values:
        return None
    middle = len(values) // 2
    return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2


def main():
    parser = argparse.ArgumentParser(description="Local all-action reference fidelity smoke study")
    parser.add_argument("--matrix", default="experiments/reference_fidelity_smoke.json")
    parser.add_argument("--output", default="results/reference-fidelity")
    parser.add_argument("--series-id")
    args = parser.parse_args()
    design_path = Path(args.matrix)
    design = json.loads(design_path.read_text())
    if design.get("schema_version") != 1:
        raise ValueError("unsupported reference-fidelity design schema")
    series = create_series_dir(args.output, args.series_id)
    series_manifest = {"schema_version": 1, "kind": "reference_fidelity_series", "status": "RUNNING",
                       "created_utc": datetime.now(timezone.utc).isoformat(), "design_path": str(design_path),
                       "design_sha256": hashlib.sha256(design_path.read_bytes()).hexdigest(),
                       "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "runs": []}
    write_json(series / "series-manifest.json", series_manifest)
    branch_rows, epoch_rows, run_summaries = [], [], []
    for seed in design["seeds"]:
        for horizon in design["horizons"]:
            for shadow_rate in design["shadow_service_rates"]:
                config = Config(random_seed=seed, experiment_name=f"reference-h{horizon}-rate{shadow_rate}-seed{seed}",
                                workload_profile=design["workload_profile"], duration_epochs=design["duration_epochs"],
                                warmup_epochs=design["warmup_epochs"], horizon_ticks=horizon, shadow_count=2,
                                mirror_count=1, shadow_service_rate=shadow_rate,
                                production_heterogeneity=design["production_heterogeneity"],
                                model_incidents=design["model_incidents"])
                run_path, _ = run(config, series)
                analysis = analyze_run(run_path)
                measured_epochs = {row["epoch"] for row in analysis["epoch_rows"] if row["epoch"] >= config.warmup_epochs}
                measured_branch = [row for row in analysis["branch_rows"] if row["epoch"] in measured_epochs]
                measured_epoch = [row for row in analysis["epoch_rows"] if row["epoch"] in measured_epochs]
                branch_rows.extend(analysis["branch_rows"])
                epoch_rows.extend(analysis["epoch_rows"])
                summary = {"seed": seed, "horizon_ticks": horizon, "shadow_service_rate": shadow_rate,
                           "run_path": str(run_path), "measured_epochs": len(measured_epoch),
                           "mirror_median_absolute_error": median([row["absolute_error"] for row in measured_branch if row["role"] == "MIRROR"]),
                           "alternative_median_absolute_error": median([row["absolute_error"] for row in measured_branch if row["role"] == "SHADOW"]),
                           "ranking_agreement": sum(row["ranking_agrees"] for row in measured_epoch) / len(measured_epoch),
                           "epsilon_gate_coverage": sum(row["epsilon_covers_selected_error"] for row in measured_epoch) / len(measured_epoch)}
                run_summaries.append(summary)
                series_manifest["runs"].append({"run_path": str(run_path), "manifest_sha256": hashlib.sha256((run_path / "manifest.json").read_bytes()).hexdigest()})
                print(json.dumps(summary), flush=True)
    write_jsonl(series / "reference-branches.jsonl", branch_rows)
    write_jsonl(series / "reference-epochs.jsonl", epoch_rows)
    write_json(series / "reference-summary.json", run_summaries)
    series_manifest.update(status="COMPLETE", completed_utc=datetime.now(timezone.utc).isoformat(),
                           outputs={name: hashlib.sha256((series / name).read_bytes()).hexdigest() for name in
                                    ("reference-branches.jsonl", "reference-epochs.jsonl", "reference-summary.json")})
    write_json(series / "series-manifest.json", series_manifest)
    print(json.dumps({"series": str(series), "status": "COMPLETE"}))


if __name__ == "__main__":
    main()
