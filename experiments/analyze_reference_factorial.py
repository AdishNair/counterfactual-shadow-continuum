"""Deterministic seed-level analysis for the frozen reference-fidelity factorial."""
import argparse
import csv
import json
from pathlib import Path
import random


CELL = ("horizon_ticks", "demand_regime", "incident_regime", "mismatch_regime")
RUN_METRICS = ("selected_epsilon_coverage", "gate_rate", "precision", "false_positive_rate",
               "false_negative_rate", "abstention_rate", "full_ranking_agreement",
               "regret_sign_agreement", "mean_choice_value_loss")


def lines(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def median(values):
    values = sorted(values)
    if not values:
        return None
    middle = len(values) // 2
    return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2


def bootstrap_median_interval(values, key, iterations=1000):
    if not values:
        return None, None
    rng = random.Random(f"reference-factorial-bootstrap-v1:{key}")
    samples = [median([values[rng.randrange(len(values))] for _ in values]) for _ in range(iterations)]
    samples.sort()
    return samples[int(.025 * (iterations - 1))], samples[int(.975 * (iterations - 1))]


def classify(observations, multiplier):
    comparable = [row for row in observations if row["comparable"]]
    positive = [row for row in comparable if row["estimated_improvement"] > multiplier * row["epsilon"]]
    negative = [row for row in comparable if row not in positive]
    ref_negative = [row for row in comparable if not row["reference_positive"]]
    ref_any_positive = [row for row in comparable if row["any_reference_positive"]]
    def rate(items, denominator):
        return len(items) / len(denominator) if denominator else None
    return {
        "selected_epsilon_coverage": rate([row for row in comparable if row["selected_epsilon_coverage"]], comparable),
        "gate_rate": rate(positive, comparable),
        "precision": rate([row for row in positive if row["reference_positive"]], positive),
        "false_positive_rate": rate([row for row in ref_negative if row in positive], ref_negative),
        "false_negative_rate": rate([row for row in ref_any_positive if row in negative], ref_any_positive),
        "abstention_rate": rate(negative, comparable),
        "full_ranking_agreement": rate([row for row in comparable if row["full_ranking_agreement"]], comparable),
        "regret_sign_agreement": rate([row for row in comparable if row["regret_sign_agreement"]], comparable),
        "mean_choice_value_loss": sum(row["choice_value_loss"] for row in comparable) / len(comparable) if comparable else None,
        "anchors_total": len(observations), "anchors_comparable": len(comparable),
        "anchors_excluded": len(observations) - len(comparable),
        "tp": sum(row["reference_positive"] for row in positive),
        "fp": sum(not row["reference_positive"] for row in positive),
        "fn": sum(row["any_reference_positive"] for row in negative),
        "tn": sum(not row["any_reference_positive"] for row in negative),
    }


def run_rows(series, multiplier):
    observations = lines(Path(series) / "anchor-observations.jsonl")
    groups = {}
    for row in observations:
        groups.setdefault(row["run_id"], []).append(row)
    rows = []
    for run_id, values in groups.items():
        first = values[0]
        rows.append({"run_id": run_id, **{key: first[key] for key in CELL + ("seed",)},
                     "gate_multiplier": multiplier, **classify(values, multiplier)})
    return rows


def cell_rows(rows, criteria):
    groups = {}
    for row in rows:
        groups.setdefault(tuple(row[key] for key in CELL), []).append(row)
    output = []
    for key, values in sorted(groups.items()):
        row = dict(zip(CELL, key))
        row["runs"] = len(values)
        for metric in RUN_METRICS:
            measure = [value[metric] for value in values if value[metric] is not None]
            row[f"median_{metric}"] = median(measure)
            low, high = bootstrap_median_interval(measure, f"{key}:{metric}")
            row[f"median_{metric}_ci_low"], row[f"median_{metric}_ci_high"] = low, high
        row["gate_supported"] = (row["median_precision"] is not None and
                                 row["median_precision"] >= criteria["median_precision_min"] and
                                 row["median_false_positive_rate"] is not None and
                                 row["median_false_positive_rate"] <= criteria["median_false_positive_rate_max"] and
                                 row["median_abstention_rate"] is not None and
                                 row["median_abstention_rate"] < criteria["median_abstention_rate_max"])
        output.append(row)
    return output


def action_rows(series):
    raw = lines(Path(series) / "action-observations.jsonl")
    by_run_action = {}
    for row in raw:
        key = (row["run_id"], row["action"])
        by_run_action.setdefault(key, []).append(row)
    reduced = []
    for (_, action), values in by_run_action.items():
        first = values[0]
        reduced.append({**{key: first[key] for key in CELL + ("seed",)}, "action": action,
                        "median_absolute_error": median([row["absolute_error"] for row in values]),
                        "median_signed_error": median([row["signed_error"] for row in values]),
                        "gain_epsilon_coverage": sum(row["epsilon_covers_gain_error"] for row in values) / len(values)})
    groups = {}
    for row in reduced:
        groups.setdefault(tuple(row[key] for key in CELL + ("action",)), []).append(row)
    output = []
    for key, values in sorted(groups.items()):
        row = dict(zip(CELL + ("action",), key))
        row["runs"] = len(values)
        for metric in ("median_absolute_error", "median_signed_error", "gain_epsilon_coverage"):
            row[f"median_{metric}"] = median([value[metric] for value in values])
        output.append(row)
    return output


def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def select_multiplier(series, design):
    candidates = []
    criteria = design["support_criteria"]
    for multiplier in design["decision_multipliers"]:
        rows = run_rows(series, multiplier)
        aggregate = {metric: median([row[metric] for row in rows if row[metric] is not None]) for metric in
                     ("precision", "false_positive_rate", "abstention_rate")}
        qualifies = (aggregate["precision"] is not None and aggregate["precision"] >= criteria["median_precision_min"] and
                     aggregate["false_positive_rate"] is not None and aggregate["false_positive_rate"] <= criteria["median_false_positive_rate_max"] and
                     aggregate["abstention_rate"] is not None and aggregate["abstention_rate"] < criteria["median_abstention_rate_max"])
        candidates.append({"multiplier": multiplier, **aggregate, "qualifies": qualifies})
    selected = next((row["multiplier"] for row in candidates if row["qualifies"]), None)
    return {"candidates": candidates, "selected_multiplier": selected}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("series")
    parser.add_argument("--output", required=True)
    parser.add_argument("--multiplier", type=float, default=1.0)
    parser.add_argument("--select-replacement", action="store_true")
    args = parser.parse_args()
    series, output = Path(args.series), Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    design = json.loads((series / "frozen-design.json").read_text())
    rows = run_rows(series, args.multiplier)
    cells = cell_rows(rows, design["support_criteria"])
    actions = action_rows(series)
    write_csv(output / "reference-factorial-run-summary.csv", rows)
    write_csv(output / "reference-factorial-cell-summary.csv", cells)
    write_csv(output / "reference-factorial-action-summary.csv", actions)
    supported = [row for row in cells if row["gate_supported"]]
    classification = "A. CURRENT GATE SUPPORTED" if len(supported) == len(cells) else "B. CONDITIONAL SUPPORT" if supported else "D. COUNTERFACTUAL VALIDITY NOT ESTABLISHED"
    report = ["# Confirmatory reference-fidelity factorial", "",
              "**Status:** Deterministic run/seed-level analysis.", "",
              f"**Series:** `{series.as_posix()}`", f"**Gate multiplier:** {args.multiplier}",
              f"**Provisional classification:** {classification}", "",
              "The independent unit is the seed x cell run. Three anchors are repeated observations reduced within run; bootstrap intervals resample runs.", "",
              "| H | Demand | Incident | Mismatch | Runs | Median precision | Median FP rate | Median abstention | Median selected coverage | Gate criterion |",
              "|---:|---|---|---|---:|---:|---:|---:|---:|---|"]
    for row in cells:
        fmt = lambda value: "NA" if value is None else f"{value:.4f}"
        report.append(f"| {row['horizon_ticks']} | {row['demand_regime']} | {row['incident_regime']} | {row['mismatch_regime']} | {row['runs']} | {fmt(row['median_precision'])} | {fmt(row['median_false_positive_rate'])} | {fmt(row['median_abstention_rate'])} | {fmt(row['median_selected_epsilon_coverage'])} | {'pass' if row['gate_supported'] else 'fail'} |")
    report.extend(["", "The reference is independent relative to `ShadowWorldModel` only. It is an authored production-software reference, not physical or factual ground truth. Do not treat the provisional classification as permission to implement learning."])
    (output / "reference-factorial-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if args.select_replacement:
        selection = select_multiplier(series, design)
        (output / "reference-factorial-replacement-selection.json").write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(selection))
    print(output / "reference-factorial-report.md")


if __name__ == "__main__":
    main()
