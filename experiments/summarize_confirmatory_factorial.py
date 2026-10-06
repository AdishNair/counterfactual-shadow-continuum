"""Cross-holdout seed-level synthesis for the frozen reference factorial."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random


CELL = ("horizon_ticks", "demand_regime", "incident_regime", "mismatch_regime")


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def median(values):
    values = sorted(values)
    if not values:
        return None
    middle = len(values) // 2
    return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2


def ranks(values):
    ordered = sorted(enumerate(values), key=lambda pair: pair[1])
    result = [None] * len(values)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][1] == ordered[index][1]:
            end += 1
        rank = (index + end - 1) / 2
        for position, _ in ordered[index:end]:
            result[position] = rank
        index = end
    return result


def correlation(left, right):
    if len(left) < 3 or len(set(left)) < 2 or len(set(right)) < 2:
        return None
    left, right = ranks(left), ranks(right)
    left_mean, right_mean = sum(left) / len(left), sum(right) / len(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right))
    denominator = (sum((x - left_mean) ** 2 for x in left) * sum((y - right_mean) ** 2 for y in right)) ** .5
    return numerator / denominator if denominator else None


def bootstrap_correlation(left, right, key, iterations=1000):
    if correlation(left, right) is None:
        return None, None
    rng, samples = random.Random(f"factorial-rho-v1:{key}"), []
    for _ in range(iterations):
        indices = [rng.randrange(len(left)) for _ in left]
        value = correlation([left[index] for index in indices], [right[index] for index in indices])
        if value is not None:
            samples.append(value)
    if not samples:
        return None, None
    samples.sort()
    return samples[int(.025 * (len(samples) - 1))], samples[int(.975 * (len(samples) - 1))]


def run_level(series):
    observations = read_jsonl(Path(series) / "anchor-observations.jsonl")
    actions = read_jsonl(Path(series) / "action-observations.jsonl")
    design = json.loads((Path(series) / "frozen-design.json").read_text())
    criteria = design["support_criteria"]
    by_run, action_by_run = {}, {}
    for row in observations:
        by_run.setdefault(row["run_id"], []).append(row)
    for row in actions:
        action_by_run.setdefault(row["run_id"], []).append(row)
    rows = []
    for run_id, values in by_run.items():
        comparable = [row for row in values if row["comparable"]]
        positives = [row for row in comparable if row["gate_passed"]]
        negatives = [row for row in comparable if not row["gate_passed"]]
        ref_negative = [row for row in comparable if not row["reference_positive"]]
        def rate(items, denominator):
            return len(items) / len(denominator) if denominator else None
        first = values[0]
        action_values = action_by_run[run_id]
        mirror_errors = [row["absolute_error"] for row in action_values if row["action_role"] == "MIRROR"]
        alternative_errors = [row["absolute_error"] for row in action_values if row["action_role"] == "SHADOW"]
        rows.append({"run_id": run_id, **{key: first[key] for key in CELL + ("seed",)},
                     "precision": rate([row for row in positives if row["reference_positive"]], positives),
                     "false_positive_rate": rate([row for row in ref_negative if row["gate_passed"]], ref_negative),
                     "abstention_rate": rate(negatives, comparable),
                     "mirror_absolute_error": median(mirror_errors),
                     "alternative_absolute_error": median(alternative_errors),
                     "gate_margin": median([row["estimated_improvement"] - row["epsilon"] for row in comparable]),
                     "reference_gain": median([row["reference_improvement"] for row in comparable])})
    groups = {}
    for row in rows:
        groups.setdefault(tuple(row[key] for key in CELL), []).append(row)
    cells = {}
    relationships = []
    for key, values in groups.items():
        precision = median([row["precision"] for row in values if row["precision"] is not None])
        fpr = median([row["false_positive_rate"] for row in values if row["false_positive_rate"] is not None])
        abstention = median([row["abstention_rate"] for row in values if row["abstention_rate"] is not None])
        passed = (precision is not None and precision >= criteria["median_precision_min"] and
                  fpr is not None and fpr <= criteria["median_false_positive_rate_max"] and
                  abstention is not None and abstention < criteria["median_abstention_rate_max"])
        cells[key] = {"precision": precision, "false_positive_rate": fpr, "abstention_rate": abstention, "gate_supported": passed}
        mirror, alternative = [row["mirror_absolute_error"] for row in values], [row["alternative_absolute_error"] for row in values]
        margin, gain = [row["gate_margin"] for row in values], [row["reference_gain"] for row in values]
        mirror_low, mirror_high = bootstrap_correlation(mirror, alternative, f"mirror:{key}")
        gain_low, gain_high = bootstrap_correlation(margin, gain, f"gain:{key}")
        relationships.append({**dict(zip(CELL, key)), "runs": len(values),
                              "mirror_to_alternative_spearman_rho": correlation(mirror, alternative),
                              "mirror_to_alternative_ci_low": mirror_low, "mirror_to_alternative_ci_high": mirror_high,
                              "margin_to_reference_gain_spearman_rho": correlation(margin, gain),
                              "margin_to_reference_gain_ci_low": gain_low, "margin_to_reference_gain_ci_high": gain_high})
    return cells, relationships


def write_csv(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evaluation_series")
    parser.add_argument("heldout_series")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    first_cells, first_relationships = run_level(args.evaluation_series)
    second_cells, second_relationships = run_level(args.heldout_series)
    consensus = []
    for key in sorted(first_cells):
        first, second = first_cells[key], second_cells[key]
        consensus.append({**dict(zip(CELL, key)), "evaluation_pass": first["gate_supported"],
                          "heldout_pass": second["gate_supported"], "support_reproduced": first["gate_supported"] and second["gate_supported"],
                          "evaluation_median_precision": first["precision"], "heldout_median_precision": second["precision"],
                          "evaluation_median_false_positive_rate": first["false_positive_rate"], "heldout_median_false_positive_rate": second["false_positive_rate"],
                          "evaluation_median_abstention_rate": first["abstention_rate"], "heldout_median_abstention_rate": second["abstention_rate"]})
    relationships = [{"series": "evaluation", **row} for row in first_relationships] + [{"series": "heldout", **row} for row in second_relationships]
    write_csv(output / "gate-consensus.csv", consensus)
    write_csv(output / "mirror-alternative-relationships.csv", relationships)
    reproducible = [row for row in consensus if row["support_reproduced"]]
    report = ["# Cross-holdout factorial synthesis", "",
              "**Status:** Deterministic seed-level synthesis of two disjoint evaluation blocks.", "",
              f"Reproduced support appears in {len(reproducible)} of {len(consensus)} predeclared cells.", "",
              "| H | Demand | Incident | Mismatch | Evaluation | Held-out | Reproduced support |",
              "|---:|---|---|---|---|---|---|"]
    for row in consensus:
        report.append(f"| {row['horizon_ticks']} | {row['demand_regime']} | {row['incident_regime']} | {row['mismatch_regime']} | {'pass' if row['evaluation_pass'] else 'fail'} | {'pass' if row['heldout_pass'] else 'fail'} | {'yes' if row['support_reproduced'] else 'no'} |")
    report.extend(["", "Correlation rows use one seed x cell run as each observation. They are descriptive associations in the authored software environment; the bootstrap intervals resample runs and do not turn anchors into independent units."])
    (output / "cross-holdout-synthesis.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    artifact = {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in ("gate-consensus.csv", "mirror-alternative-relationships.csv", "cross-holdout-synthesis.md")}
    (output / "manifest.json").write_text(json.dumps({"script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "outputs": artifact}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"reproduced_support_cells": len(reproducible), "total_cells": len(consensus), "output": str(output)}))


if __name__ == "__main__":
    main()
