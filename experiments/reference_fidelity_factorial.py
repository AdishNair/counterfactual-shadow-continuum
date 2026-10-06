"""Frozen, seed-replicated SEM/reference calibration factorial for authored J1."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random

from csc.branches import execute_shadow
from csc.contracts import ACTIONS, Anchor, Branch, Config, Event, State, StateCaptureEngine, canonical
from csc.world import ProductionWorld
from experiments.reference_oracle import REFERENCE_KIND, outcome as reference_outcome
from experiments.runner import create_series_dir, write_json


def hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


def write_jsonl(stream, value):
    stream.write(canonical(value).decode() + "\n")


def source_hashes(paths):
    root = Path(__file__).resolve().parent.parent
    targets = list(sorted((root / "csc").glob("*.py"))) + [root / path for path in paths]
    return {str(path.relative_to(root)).replace("\\", "/"): hash_bytes(path.read_bytes()) for path in targets}


def event_window(seed, demand, incident, anchor_index, start_sequence, count, experiment_id):
    rng = random.Random(f"factorial-v1:{seed}:{demand}:{incident}:{anchor_index}")
    events = []
    for offset in range(count):
        if demand == "light":
            ns, ew = int(rng.random() < .2), int(rng.random() < .2)
        else:
            heavy, light = rng.randrange(4), int(rng.random() < .5)
            ns, ew = (heavy, light) if offset % 120 < 60 else (light, heavy)
        sequence = start_sequence + offset
        events.append(Event(f"factorial-arrival-{seed}-{demand}-{incident}-{anchor_index}-{sequence}",
                            experiment_id, sequence, sequence, anchor_index, ns, ew,
                            incident == "blocked_ew"))
    return events


def make_anchor(seed, demand, incident, anchor_index, design):
    experiment_id = f"factorial-anchor-s{seed}-{demand}-{incident}-a{anchor_index}"
    config = Config(random_seed=seed, workload_profile=demand, duration_epochs=1,
                    warmup_epochs=0, horizon_ticks=design["max_horizon_ticks"],
                    production_heterogeneity=False, model_incidents=True)
    capability = object()
    world = ProductionWorld(State(rng_seed=seed), capability, config)
    history = event_window(seed, demand, incident, anchor_index, 0,
                           design["anchor_history_ticks"], experiment_id)
    history_action = ACTIONS[anchor_index % len(ACTIONS)]
    world.apply_plan(history_action, capability, "anchor-history")
    for tick, event in enumerate(history):
        world.step(event, tick)
    anchor = StateCaptureEngine().capture(world.snapshot_state(), experiment_id, anchor_index)
    future = event_window(seed, demand, incident, anchor_index,
                          design["anchor_history_ticks"], design["max_horizon_ticks"], experiment_id)
    return experiment_id, anchor, future


def best_actions(values, tolerance):
    maximum = max(values.values())
    return tuple(action for action in ACTIONS if action in values and maximum - values[action] <= tolerance)


def sign(value, tolerance):
    return 1 if value > tolerance else -1 if value < -tolerance else 0


def evaluate_anchor(run_id, seed, demand, incident, mismatch_id, horizon, anchor_index,
                    anchor, all_events, mismatch, design, multiplier):
    config = Config(random_seed=seed, workload_profile=demand, duration_epochs=1,
                    warmup_epochs=0, horizon_ticks=horizon, shadow_count=2, mirror_count=1,
                    production_policy="queue", production_heterogeneity=mismatch["production_heterogeneity"],
                    shadow_service_rate=mismatch["shadow_service_rate"],
                    model_incidents=mismatch["model_incidents"])
    events = all_events[:horizon]
    production_action = "NS_GREEN" if anchor.hydrate().queue_ns >= anchor.hydrate().queue_ew else "EW_GREEN"
    start = anchor.hydrate().input_sequence_watermark + 1
    reference = {action: reference_outcome(anchor, action, events, config) for action in ACTIONS}
    anchor_payload = json.loads(anchor.payload)
    anchor_experiment_id = anchor_payload["experiment_id"]
    branches = [Branch(f"{run_id}-mirror", anchor_experiment_id, anchor_index, "MIRROR",
                       production_action, anchor.snapshot_id, start, start + horizon - 1)]
    branches.extend(Branch(f"{run_id}-shadow-{action}", anchor_experiment_id, anchor_index,
                           "SHADOW", action, anchor.snapshot_id, start, start + horizon - 1)
                    for action in ACTIONS if action != production_action)
    estimated = {}
    outcomes = []
    for branch in branches:
        request = {"anchor": anchor.envelope(), "branch": asdict(branch),
                   "events": [asdict(event) for event in events], "config": asdict(config)}
        result = execute_shadow(request)
        if result["status"] != "REPORTED" or not result["synchronization"]["comparable"]:
            return {"run_id": run_id, "seed": seed, "demand_regime": demand,
                    "incident_regime": incident, "mismatch_regime": mismatch_id,
                    "horizon_ticks": horizon, "anchor_index": anchor_index,
                    "anchor_hash": anchor.snapshot_id, "input_sha256": hash_bytes(canonical([asdict(event) for event in events])),
                    "comparable": False, "exclusion_reason": "incomplete_sem_branch"}, []
        estimated[branch.action] = result["utility"] if result.get("utility") is not None else None
        # execute_shadow returns metrics but not a calculated utility; use the shared, fixed utility definition.
        if estimated[branch.action] is None:
            from csc.compare import utility
            estimated[branch.action] = utility(result["metrics"], config)
        outcomes.append((branch, result))
    if set(estimated) != set(ACTIONS) or len(outcomes) != 3:
        return {"run_id": run_id, "seed": seed, "demand_regime": demand,
                "incident_regime": incident, "mismatch_regime": mismatch_id,
                "horizon_ticks": horizon, "anchor_index": anchor_index,
                "anchor_hash": anchor.snapshot_id, "input_sha256": hash_bytes(canonical([asdict(event) for event in events])),
                "comparable": False, "exclusion_reason": "incomplete_action_coverage"}, []
    epsilon = abs(estimated[production_action] - reference[production_action]["utility"])
    alternative_actions = tuple(action for action in ACTIONS if action != production_action)
    best_estimated_alternatives = best_actions({action: estimated[action] for action in alternative_actions}, design["tie_tolerance"])
    selected_action = best_estimated_alternatives[0]
    estimated_gain = estimated[selected_action] - reference[production_action]["utility"]
    reference_gain = reference[selected_action]["utility"] - reference[production_action]["utility"]
    oracle_alternative_gain = max(reference[action]["utility"] for action in alternative_actions) - reference[production_action]["utility"]
    gate_passed = estimated_gain > multiplier * epsilon
    reference_positive = reference_gain > design["tie_tolerance"]
    any_reference_positive = oracle_alternative_gain > design["tie_tolerance"]
    outcome_name = "TP" if gate_passed and reference_positive else "FP" if gate_passed else "FN" if any_reference_positive else "TN"
    full_estimated_best = best_actions(estimated, design["tie_tolerance"])
    full_reference_values = {action: reference[action]["utility"] for action in ACTIONS}
    full_reference_best = best_actions(full_reference_values, design["tie_tolerance"])
    action_rows = []
    for action in ACTIONS:
        estimated_gain_by_action = estimated[action] - reference[production_action]["utility"]
        reference_gain_by_action = reference[action]["utility"] - reference[production_action]["utility"]
        action_rows.append({"run_id": run_id, "seed": seed, "demand_regime": demand,
                            "incident_regime": incident, "mismatch_regime": mismatch_id,
                            "horizon_ticks": horizon, "anchor_index": anchor_index,
                            "anchor_hash": anchor.snapshot_id, "input_sha256": hash_bytes(canonical([asdict(event) for event in events])),
                            "production_action": production_action, "action": action,
                            "action_role": "MIRROR" if action == production_action else "SHADOW",
                            "estimated_utility": estimated[action], "reference_utility": reference[action]["utility"],
                            "signed_error": estimated[action] - reference[action]["utility"],
                            "absolute_error": abs(estimated[action] - reference[action]["utility"]),
                            "estimated_gain": estimated_gain_by_action, "reference_gain": reference_gain_by_action,
                            "gain_error": estimated_gain_by_action - reference_gain_by_action,
                            "epsilon": epsilon, "epsilon_covers_gain_error": abs(estimated_gain_by_action - reference_gain_by_action) <= epsilon,
                            "reference_kind": REFERENCE_KIND})
    return {"run_id": run_id, "seed": seed, "demand_regime": demand,
            "incident_regime": incident, "mismatch_regime": mismatch_id,
            "horizon_ticks": horizon, "anchor_index": anchor_index,
            "anchor_hash": anchor.snapshot_id, "input_sha256": hash_bytes(canonical([asdict(event) for event in events])),
            "comparable": True, "exclusion_reason": None, "production_action": production_action,
            "epsilon": epsilon, "gate_multiplier": multiplier, "selected_action": selected_action,
            "estimated_improvement": estimated_gain, "reference_improvement": reference_gain,
            "selected_epsilon_coverage": abs(estimated_gain - reference_gain) <= epsilon,
            "gate_passed": gate_passed, "reference_positive": reference_positive,
            "any_reference_positive": any_reference_positive, "recommendation_outcome": outcome_name,
            "full_ranking_agreement": full_estimated_best == full_reference_best,
            "estimated_best_actions": list(full_estimated_best), "reference_best_actions": list(full_reference_best),
            "regret_sign_agreement": sign(max(estimated[action] for action in alternative_actions) - reference[production_action]["utility"], design["tie_tolerance"]) == sign(oracle_alternative_gain, design["tie_tolerance"]),
            "choice_value_loss": max(full_reference_values.values()) - reference[selected_action]["utility"],
            "reference_kind": REFERENCE_KIND}, action_rows


def run_summary(run_id, observations, metadata):
    comparable = [row for row in observations if row["comparable"]]
    def proportion(selector, denominator):
        values = [row for row in denominator if selector(row)]
        return len(values) / len(denominator) if denominator else None
    positive = [row for row in comparable if row["gate_passed"]]
    negatives = [row for row in comparable if not row["gate_passed"]]
    reference_negative = [row for row in comparable if not row["reference_positive"]]
    reference_any_positive = [row for row in comparable if row["any_reference_positive"]]
    return {**metadata, "run_id": run_id, "anchors_total": len(observations), "anchors_comparable": len(comparable),
            "anchors_excluded": len(observations) - len(comparable),
            "mirror_absolute_error_median": sorted([row["epsilon"] for row in comparable])[len(comparable) // 2] if comparable else None,
            "selected_epsilon_coverage": proportion(lambda row: row["selected_epsilon_coverage"], comparable),
            "gate_rate": proportion(lambda row: row["gate_passed"], comparable),
            "precision": proportion(lambda row: row["reference_positive"], positive),
            "false_positive_rate": proportion(lambda row: row["gate_passed"], reference_negative),
            "false_negative_rate": proportion(lambda row: not row["gate_passed"], reference_any_positive),
            "abstention_rate": proportion(lambda row: not row["gate_passed"], comparable),
            "full_ranking_agreement": proportion(lambda row: row["full_ranking_agreement"], comparable),
            "regret_sign_agreement": proportion(lambda row: row["regret_sign_agreement"], comparable),
            "mean_choice_value_loss": sum(row["choice_value_loss"] for row in comparable) / len(comparable) if comparable else None,
            "tp": sum(row["recommendation_outcome"] == "TP" for row in comparable),
            "fp": sum(row["recommendation_outcome"] == "FP" for row in comparable),
            "fn": sum(row["recommendation_outcome"] == "FN" for row in comparable),
            "tn": sum(row["recommendation_outcome"] == "TN" for row in comparable)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", default="experiments/reference_fidelity_factorial.json")
    parser.add_argument("--phase", choices=("evaluation", "calibration", "replacement-evaluation"), required=True)
    parser.add_argument("--multiplier", type=float, default=1.0)
    parser.add_argument("--output", default="results/reference-fidelity")
    parser.add_argument("--series-id", required=True)
    args = parser.parse_args()
    design_path = Path(args.design)
    design = json.loads(design_path.read_text())
    if design.get("schema_version") != 1:
        raise ValueError("unsupported factorial design schema")
    phase_seeds = design[{"evaluation": "evaluation_seeds", "calibration": "calibration_seeds", "replacement-evaluation": "replacement_evaluation_seeds"}[args.phase]]
    series = create_series_dir(args.output, args.series_id)
    write_json(series / "frozen-design.json", design)
    conditions = [{"seed": seed, "demand_regime": demand, "incident_regime": incident,
                   "mismatch_regime": mismatch, "horizon_ticks": horizon}
                  for seed in phase_seeds for demand in design["demand_regimes"]
                  for incident in design["incident_regimes"] for mismatch in design["mismatch_regimes"]
                  for horizon in design["horizons"]]
    random.Random(design["condition_order_seed"]).shuffle(conditions)
    write_json(series / "planned-conditions.json", conditions)
    manifest = {"schema_version": 1, "kind": "reference_fidelity_factorial", "status": "RUNNING",
                "phase": args.phase, "gate_multiplier": args.multiplier,
                "created_utc": datetime.now(timezone.utc).isoformat(), "design_path": str(design_path),
                "design_sha256": hash_bytes(design_path.read_bytes()), "reference_kind": REFERENCE_KIND,
                "execution_mode": "in_process_sem_evaluation", "source_hashes": source_hashes([
                    "experiments/reference_fidelity_factorial.py", "experiments/reference_oracle.py",
                    "experiments/analyze_reference_factorial.py"]), "completed_runs": [], "failed_runs": []}
    write_json(series / "series-manifest.json", manifest)
    anchor_cache = {}
    with (series / "anchors.jsonl").open("x", encoding="utf-8") as anchors_file, \
         (series / "input-windows.jsonl").open("x", encoding="utf-8") as inputs_file, \
         (series / "anchor-observations.jsonl").open("x", encoding="utf-8") as observations_file, \
         (series / "action-observations.jsonl").open("x", encoding="utf-8") as actions_file, \
         (series / "run-summaries.jsonl").open("x", encoding="utf-8") as summaries_file:
        for sequence, condition in enumerate(conditions):
            seed, demand, incident = condition["seed"], condition["demand_regime"], condition["incident_regime"]
            run_id = f"{args.phase}-s{seed}-{demand}-{incident}-{condition['mismatch_regime']}-h{condition['horizon_ticks']}"
            observations = []
            try:
                for anchor_index in range(design["anchors_per_run"]):
                    key = (seed, demand, incident, anchor_index)
                    if key not in anchor_cache:
                        anchor_cache[key] = make_anchor(seed, demand, incident, anchor_index, design)
                        anchor_eid, anchor, future = anchor_cache[key]
                        write_jsonl(anchors_file, {"anchor_experiment_id": anchor_eid, "seed": seed,
                                                   "demand_regime": demand, "incident_regime": incident,
                                                   "anchor_index": anchor_index, **anchor.envelope()})
                        write_jsonl(inputs_file, {"anchor_hash": anchor.snapshot_id, "events": [asdict(event) for event in future]})
                    _, anchor, future = anchor_cache[key]
                    observation, action_rows = evaluate_anchor(run_id, seed, demand, incident,
                                                               condition["mismatch_regime"], condition["horizon_ticks"],
                                                               anchor_index, anchor, future,
                                                               design["mismatch_regimes"][condition["mismatch_regime"]],
                                                               design, args.multiplier)
                    observations.append(observation)
                    write_jsonl(observations_file, observation)
                    for action_row in action_rows:
                        write_jsonl(actions_file, action_row)
                metadata = {**condition, "phase": args.phase, "gate_multiplier": args.multiplier}
                summary = run_summary(run_id, observations, metadata)
                write_jsonl(summaries_file, summary)
                manifest["completed_runs"].append({"run_id": run_id, "condition_sequence": sequence})
                print(json.dumps({"completed": run_id, "sequence": sequence + 1, "total": len(conditions)}), flush=True)
            except BaseException as exc:
                manifest["failed_runs"].append({"run_id": run_id, "condition_sequence": sequence,
                                                "error": f"{type(exc).__name__}: {exc}"})
                write_json(series / "series-manifest.json", manifest)
                raise
    manifest.update(status="COMPLETE", completed_utc=datetime.now(timezone.utc).isoformat(),
                    output_sha256={name: hash_bytes((series / name).read_bytes()) for name in
                                   ("frozen-design.json", "planned-conditions.json", "anchors.jsonl", "input-windows.jsonl",
                                    "anchor-observations.jsonl", "action-observations.jsonl", "run-summaries.jsonl")})
    write_json(series / "series-manifest.json", manifest)
    print(json.dumps({"series": str(series), "runs": len(conditions), "status": "COMPLETE"}))


if __name__ == "__main__":
    main()
