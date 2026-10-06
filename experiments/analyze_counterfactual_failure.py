"""Read-only structural failure decomposition for completed factorial series."""
import argparse
import csv
from dataclasses import asdict
import json
import math
from pathlib import Path
import statistics
import sys


# Permit both `python -m experiments.analyze_counterfactual_failure` and a
# direct invocation from the repository root without changing import meaning.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from csc.branches import execute_shadow
from csc.compare import utility
from csc.contracts import ACTIONS, Anchor, Branch, Config, Event
from experiments.reference_oracle import trace as reference_trace
from experiments.verify_reference_factorial import verify


def read_lines(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def median(values):
    return statistics.median(values) if values else None


def quantile(values, proportion):
    values = sorted(values)
    index = (len(values) - 1) * proportion
    left = int(index)
    return values[left] + (values[min(left + 1, len(values) - 1)] - values[left]) * (index - left)


def l2(left, right):
    return math.hypot(left["queue_ns"] - right["queue_ns"], left["queue_ew"] - right["queue_ew"])


def trajectory_metrics(left, right):
    distances = [l2(a, b) for a, b in zip(left, right)]
    return {"integrated": sum(distances), "maximum": max(distances), "terminal": distances[-1]}


def action_distance(left, right):
    if left == right:
        return 0
    return 1 if "BALANCED" in (left, right) else 2


def rank(values):
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    result, start = [None] * len(values), 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][1] == ordered[start][1]:
            end += 1
        average = (start + end - 1) / 2
        for index, _ in ordered[start:end]:
            result[index] = average
        start = end
    return result


def spearman(left, right):
    if len(left) < 3 or len(set(left)) < 2 or len(set(right)) < 2:
        return None
    left, right = rank(left), rank(right)
    left_mean, right_mean = sum(left) / len(left), sum(right) / len(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right))
    denominator = math.sqrt(sum((x - left_mean) ** 2 for x in left) * sum((y - right_mean) ** 2 for y in right))
    return numerator / denominator if denominator else None


def write_csv(path, rows):
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def series_rows(series_path, label):
    verify(series_path)
    series_path = Path(series_path)
    design = json.loads((series_path / "frozen-design.json").read_text())
    anchors = {row["snapshot_id"]: Anchor.from_envelope(row) for row in read_lines(series_path / "anchors.jsonl")}
    windows = {row["anchor_hash"]: [Event(**event) for event in row["events"]] for row in read_lines(series_path / "input-windows.jsonl")}
    action_rows = {}
    for row in read_lines(series_path / "action-observations.jsonl"):
        action_rows[(row["run_id"], row["anchor_index"], row["action"])] = row
    observations, derived = read_lines(series_path / "anchor-observations.jsonl"), []
    for observation in observations:
        if not observation["comparable"]:
            continue
        anchor = anchors[observation["anchor_hash"]]
        state = anchor.hydrate()
        horizon = observation["horizon_ticks"]
        events = windows[anchor.snapshot_id][:horizon]
        mismatch = design["mismatch_regimes"][observation["mismatch_regime"]]
        config = Config(random_seed=observation["seed"], workload_profile=observation["demand_regime"],
                        duration_epochs=1, warmup_epochs=0, horizon_ticks=horizon, shadow_count=2,
                        mirror_count=1, production_heterogeneity=mismatch["production_heterogeneity"],
                        shadow_service_rate=mismatch["shadow_service_rate"], model_incidents=mismatch["model_incidents"])
        reference = {action: reference_trace(anchor, action, events, config) for action in ACTIONS}
        start = state.input_sequence_watermark + 1
        eid = json.loads(anchor.payload)["experiment_id"]
        estimates = {}
        for action in ACTIONS:
            role = "MIRROR" if action == observation["production_action"] else "SHADOW"
            branch = Branch(f"derive-{label}-{observation['run_id']}-{observation['anchor_index']}-{action}", eid,
                            observation["anchor_index"], role, action, anchor.snapshot_id, start, start + horizon - 1)
            result = execute_shadow({"anchor": anchor.envelope(), "branch": asdict(branch),
                                     "events": [asdict(event) for event in events], "config": asdict(config)})
            if result["status"] != "REPORTED" or not result["synchronization"]["comparable"]:
                raise ValueError("derived replay produced non-comparable branch")
            estimates[action] = {"trace": result["trace"], "utility": utility(result["metrics"], config)}
            saved = action_rows[(observation["run_id"], observation["anchor_index"], action)]
            if abs(saved["estimated_utility"] - estimates[action]["utility"]) > 1e-9:
                raise AssertionError("derived SEM utility differs from saved observation")
        production = observation["production_action"]
        mirror_trace = estimates[production]["trace"]
        for alternative in ACTIONS:
            if alternative == production:
                continue
            saved = action_rows[(observation["run_id"], observation["anchor_index"], alternative)]
            ref_divergence = trajectory_metrics(reference[alternative], reference[production])
            sem_divergence = trajectory_metrics(estimates[alternative]["trace"], mirror_trace)
            alt_error_trace = trajectory_metrics(estimates[alternative]["trace"], reference[alternative])
            derived.append({"series": label, "run_id": observation["run_id"], "seed": observation["seed"],
                            "horizon_ticks": horizon, "demand_regime": observation["demand_regime"],
                            "incident_regime": observation["incident_regime"], "mismatch_regime": observation["mismatch_regime"],
                            "anchor_index": observation["anchor_index"], "anchor_hash": anchor.snapshot_id,
                            "production_action": production, "alternative_action": alternative,
                            "action_distance": action_distance(production, alternative),
                            "state_signal_phase": state.signal_phase, "state_queue_total": state.queue_ns + state.queue_ew,
                            "state_queue_imbalance": abs(state.queue_ns - state.queue_ew), "state_phase_elapsed": state.phase_elapsed,
                            "mirror_absolute_error": observation["epsilon"], "alternative_absolute_error": saved["absolute_error"],
                            "alternative_signed_error": saved["signed_error"], "estimated_gain": saved["estimated_gain"],
                            "reference_gain": saved["reference_gain"], "gain_error": saved["gain_error"],
                            "gate_passed": observation["gate_passed"], "recommendation_outcome": observation["recommendation_outcome"],
                            "selected_action": observation["selected_action"], "is_selected": alternative == observation["selected_action"],
                            "reference_action_divergence_integrated": ref_divergence["integrated"],
                            "reference_action_divergence_maximum": ref_divergence["maximum"],
                            "reference_action_divergence_terminal": ref_divergence["terminal"],
                            "sem_action_divergence_integrated": sem_divergence["integrated"],
                            "sem_action_divergence_maximum": sem_divergence["maximum"],
                            "sem_action_divergence_terminal": sem_divergence["terminal"],
                            "alternative_trace_error_integrated": alt_error_trace["integrated"],
                            "alternative_trace_error_maximum": alt_error_trace["maximum"],
                            "alternative_trace_error_terminal": alt_error_trace["terminal"],
                            "oracle_any_better_alternative": observation["any_reference_positive"],
                            "oracle_selected_gain": observation["reference_improvement"],
                            "reference_kind": observation["reference_kind"]})
    return derived


def classify(rows):
    thresholds = {}
    for series in sorted({row["series"] for row in rows}):
        subset = [row for row in rows if row["series"] == series]
        thresholds[series] = {"low_mirror": quantile([row["mirror_absolute_error"] for row in subset], .25),
                              "high_mirror": quantile([row["mirror_absolute_error"] for row in subset], .75),
                              "low_alternative": quantile([row["alternative_absolute_error"] for row in subset], .25),
                              "high_alternative": quantile([row["alternative_absolute_error"] for row in subset], .75)}
    for row in rows:
        threshold = thresholds[row["series"]]
        low_mirror, high_mirror = row["mirror_absolute_error"] <= threshold["low_mirror"], row["mirror_absolute_error"] >= threshold["high_mirror"]
        low_alt, high_alt = row["alternative_absolute_error"] <= threshold["low_alternative"], row["alternative_absolute_error"] >= threshold["high_alternative"]
        row["failure_category"] = "LOW_MIRROR_HIGH_ALTERNATIVE" if low_mirror and high_alt else "HIGH_MIRROR_LOW_ALTERNATIVE" if high_mirror and low_alt else "OTHER"
    return thresholds


def summaries(rows):
    taxonomy = {}
    for row in rows:
        key = tuple(row[field] for field in ("series", "failure_category", "horizon_ticks", "demand_regime", "incident_regime", "mismatch_regime", "production_action", "alternative_action"))
        taxonomy.setdefault(key, []).append(row)
    taxonomy_rows = []
    for key, values in sorted(taxonomy.items()):
        row = dict(zip(("series", "failure_category", "horizon_ticks", "demand_regime", "incident_regime", "mismatch_regime", "production_action", "alternative_action"), key))
        row.update(observations=len(values), median_mirror_error=median([item["mirror_absolute_error"] for item in values]),
                   median_alternative_error=median([item["alternative_absolute_error"] for item in values]),
                   median_reference_divergence=median([item["reference_action_divergence_integrated"] for item in values]),
                   selected_fraction=sum(item["is_selected"] for item in values) / len(values),
                   false_positive_selected=sum(item["is_selected"] and item["recommendation_outcome"] == "FP" for item in values))
        taxonomy_rows.append(row)
    run_groups = {}
    for row in rows:
        key = tuple(row[field] for field in ("series", "run_id", "horizon_ticks", "demand_regime", "incident_regime", "mismatch_regime"))
        run_groups.setdefault(key, []).append(row)
    relationship_groups = {}
    for key, values in run_groups.items():
        series, run_id, horizon, demand, incident, mismatch = key
        cell = (series, horizon, demand, incident, mismatch)
        relationship_groups.setdefault(cell, []).append({"mirror": median([item["mirror_absolute_error"] for item in values]),
                                                           "alternative": median([item["alternative_absolute_error"] for item in values]),
                                                           "divergence": median([item["reference_action_divergence_integrated"] for item in values]),
                                                           "sem_divergence": median([item["sem_action_divergence_integrated"] for item in values]),
                                                           "imbalance": median([item["state_queue_imbalance"] for item in values]),
                                                           "gain": median([item["reference_gain"] for item in values])})
    relationships = []
    for key, values in sorted(relationship_groups.items()):
        series, horizon, demand, incident, mismatch = key
        relationships.append({"series": series, "horizon_ticks": horizon, "demand_regime": demand,
                              "incident_regime": incident, "mismatch_regime": mismatch, "runs": len(values),
                              "mirror_to_alternative_error_spearman": spearman([item["mirror"] for item in values], [item["alternative"] for item in values]),
                              "reference_divergence_to_alternative_error_spearman": spearman([item["divergence"] for item in values], [item["alternative"] for item in values]),
                              "sem_divergence_to_alternative_error_spearman": spearman([item["sem_divergence"] for item in values], [item["alternative"] for item in values]),
                              "state_imbalance_to_alternative_error_spearman": spearman([item["imbalance"] for item in values], [item["alternative"] for item in values]),
                              "reference_divergence_to_reference_gain_spearman": spearman([item["divergence"] for item in values], [item["gain"] for item in values])})
    oracle = []
    for series in sorted({row["series"] for row in rows}):
        selected = [row for row in rows if row["series"] == series and row["is_selected"]]
        oracle.append({"series": series, "selected_anchor_observations": len(selected),
                       "oracle_better_alternative_rate": sum(row["oracle_any_better_alternative"] for row in selected) / len(selected),
                       "csc_gate_pass_rate": sum(row["gate_passed"] for row in selected) / len(selected),
                       "selected_reference_positive_rate": sum(row["oracle_selected_gain"] > 0 for row in selected) / len(selected),
                       "false_positive_recommendation_rate": sum(row["recommendation_outcome"] == "FP" for row in selected) / len(selected)})
    return taxonomy_rows, relationships, oracle


def write_svg(path, rows):
    categories = ("LOW_MIRROR_HIGH_ALTERNATIVE", "HIGH_MIRROR_LOW_ALTERNATIVE")
    values = [(series, category, sum(row["observations"] for row in rows if row["series"] == series and row["failure_category"] == category))
              for series in sorted({row["series"] for row in rows}) for category in categories]
    maximum = max(value[2] for value in values) or 1
    labels, bars = [], []
    for index, (series, category, value) in enumerate(values):
        x, height = 80 + index * 120, int(300 * value / maximum)
        bars.append(f'<rect x="{x}" y="{360-height}" width="70" height="{height}" fill="#b42318"/>')
        labels.append(f'<text x="{x}" y="380" font-size="10">{series[:12]}</text><text x="{x}" y="394" font-size="9">{"false confidence" if category.startswith("LOW") else "unnecessary abstain"}</text><text x="{x}" y="{350-height}" font-size="10">{value}</text>')
    Path(path).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="900" height="430"><rect width="100%" height="100%" fill="white"/><text x="40" y="30" font-size="18">Descriptive failure taxonomy counts</text><line x1="50" y1="360" x2="850" y2="360" stroke="black"/>' + ''.join(bars + labels) + '</svg>', encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--series", nargs="+", required=True, help="label=path entries")
    parser.add_argument("--tables", default="research/tables")
    parser.add_argument("--figures", default="research/figures")
    parser.add_argument("--report", default="research/evidence/cycle3/failure_analysis.md")
    args = parser.parse_args()
    all_rows = []
    for entry in args.series:
        label, path = entry.split("=", 1)
        all_rows.extend(series_rows(path, label))
    thresholds = classify(all_rows)
    taxonomy, relationships, oracle = summaries(all_rows)
    tables, figures = Path(args.tables), Path(args.figures)
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    write_csv(tables / "failure_observations.csv", all_rows)
    write_csv(tables / "failure_taxonomy.csv", taxonomy)
    write_csv(tables / "failure_relationships.csv", relationships)
    write_csv(tables / "oracle_bounds.csv", oracle)
    write_svg(figures / "failure_taxonomy.svg", taxonomy)
    false_confidence = [row for row in all_rows if row["failure_category"] == "LOW_MIRROR_HIGH_ALTERNATIVE"]
    unnecessary = [row for row in all_rows if row["failure_category"] == "HIGH_MIRROR_LOW_ALTERNATIVE"]
    clusters = {}
    for row in false_confidence:
        key = tuple(row[field] for field in ("series", "horizon_ticks", "demand_regime", "incident_regime", "mismatch_regime", "production_action", "alternative_action"))
        clusters[key] = clusters.get(key, 0) + 1
    report = ["# Counterfactual failure analysis", "", "**Status:** Exploratory, read-only derived analysis of completed immutable factorial series.", "",
              "## Question", "", "Why does same-action mirror error fail as a uniform conservative estimate of alternative-action error?", "",
              "## Method", "", "The frozen Cycle 3 protocol (`research/evidence/cycle3/cycle3_analysis_protocol.md`) keeps seed x cell as the independent unit. This script verifies each source series, then deterministically reconstructs SEM and authored-reference traces from saved anchors and windows. It does not collect new observations. Low/high labels use within-series quartiles solely as descriptive taxonomy labels, never operational thresholds.", "",
              "## Descriptive findings", "", f"Derived alternative-action observations: {len(all_rows)}. Low-mirror/high-alternative-error cases: {len(false_confidence)}. High-mirror/low-alternative-error cases: {len(unnecessary)}.", "", "Failure counts and factor strata are in `research/tables/failure_taxonomy.csv`; run-level association rows are in `research/tables/failure_relationships.csv`; the analysis-only oracle bounds are in `research/tables/oracle_bounds.csv`.", "",
              "### Low-mirror/high-alternative-error clusters", "", "| Series | H | Demand | Incident | Mismatch | Production | Alternative | Observations |", "|---|---:|---|---|---|---|---|---:|"]
    for key, count in sorted(clusters.items(), key=lambda item: (-item[1], item[0]))[:12]:
        report.append("| " + " | ".join(map(str, key)) + f" | {count} |")
    report.extend([
              "", "### Analysis-only oracle bound", "", "| Series | Better alternative exists | CSC gate pass | Selected reference-positive | False positive recommendation |", "|---|---:|---:|---:|---:|"])
    for row in oracle:
        report.append(f"| {row['series']} | {row['oracle_better_alternative_rate']:.4f} | {row['csc_gate_pass_rate']:.4f} | {row['selected_reference_positive_rate']:.4f} | {row['false_positive_recommendation_rate']:.4f} |")
    report.extend([
              "", "The structural hypothesis is supported only as a descriptive candidate when alternative trajectory divergence co-occurs with alternative error in a stratum. It is not a causal conclusion: horizon, mismatch, action, and constructed anchor state can jointly influence divergence and error. Mirror error captures same-action error (A); alternative trajectory divergence is a candidate marker of extrapolation error (B); horizon can compound both (C). This is an uncertainty taxonomy/hypothesis, not a proven additive decomposition.", "",
              "## Next implication", "", "No derived signal is enabled in CSC. Any trust selector must be frozen and tested using new development, calibration, and final held-out seeds against a separately maintained reference. Oracle columns are analysis-only and must never enter online CSC decisions.", "", "## Descriptive thresholds", "", json.dumps(thresholds, indent=2)])
    Path(args.report).write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"derived_rows": len(all_rows), "false_confidence": len(false_confidence), "unnecessary_abstention": len(unnecessary)}))


if __name__ == "__main__":
    main()
