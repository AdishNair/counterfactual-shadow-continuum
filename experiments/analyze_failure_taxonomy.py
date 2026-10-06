"""Deterministic exploratory failure decomposition for confirmatory factorial artifacts.

This is a read-only analysis of immutable factorial result directories.  It
creates research artifacts; it never invokes the experiment driver or changes
anything below results/.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "reference-fidelity"
TABLES = ROOT / "research" / "tables"
FIGURES = ROOT / "research" / "figures"
CELL = ("horizon_ticks", "demand_regime", "incident_regime", "mismatch_regime")
SERIES = (
    ("initial_evaluation", "confirmatory-evaluation-20260928"),
    ("calibration", "confirmatory-calibration-20260928"),
    ("heldout_evaluation", "confirmatory-replacement-evaluation-20260928"),
)


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def percentile(values, fraction):
    values = sorted(values)
    return values[int((len(values) - 1) * fraction)]


def median(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return None
    middle = len(values) // 2
    return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2


def fmt(value):
    return "NA" if value is None else f"{value:.3f}"


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"No rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def action_distance(production, selected):
    """A contract-space proxy: 1 for BALANCED/directional, 2 for NS/EW reversal."""
    if production == selected:
        return 0
    if "BALANCED" in (production, selected):
        return 1
    return 2


def action_distance_label(distance):
    return {0: "same", 1: "balanced_directional", 2: "directional_reversal"}[distance]


def error_class(mirror, alternative, q1_m, q3_m, q1_a, q3_a):
    low_m, high_m = mirror <= q1_m, mirror >= q3_m
    low_a, high_a = alternative <= q1_a, alternative >= q3_a
    if low_m and high_a:
        return "low_mirror_high_alternative"
    if high_m and low_a:
        return "high_mirror_low_alternative"
    if low_m and low_a:
        return "low_mirror_low_alternative"
    if high_m and high_a:
        return "high_mirror_high_alternative"
    return "intermediate"


def load_series(series_name, directory):
    directory = RESULTS / directory
    action_rows = read_jsonl(directory / "action-observations.jsonl")
    anchor_rows = read_jsonl(directory / "anchor-observations.jsonl")
    anchor_rows = [row for row in anchor_rows if row["comparable"]]
    anchors = read_jsonl(directory / "anchors.jsonl")
    states = {}
    for row in anchors:
        payload = json.loads(row["payload"])
        states[(row["seed"], row["demand_regime"], row["incident_regime"], row["anchor_index"])] = (payload["state"], payload["decision_time"])
    actions = {(row["run_id"], row["anchor_index"], row["action"]): row for row in action_rows}
    merged = []
    for anchor in anchor_rows:
        key = (anchor["run_id"], anchor["anchor_index"])
        mirror = actions[key + (anchor["production_action"],)]
        selected = actions[key + (anchor["selected_action"],)]
        state, decision_time = states[(anchor["seed"], anchor["demand_regime"], anchor["incident_regime"], anchor["anchor_index"])]
        q_ns, q_ew = state["queue_ns"], state["queue_ew"]
        merged.append({
            "series": series_name,
            **{name: anchor[name] for name in CELL},
            "seed": anchor["seed"], "run_id": anchor["run_id"], "anchor_index": anchor["anchor_index"],
            "production_action": anchor["production_action"], "selected_action": anchor["selected_action"],
            "action_pair": f"{anchor['production_action']}->{anchor['selected_action']}",
            "action_distance": action_distance(anchor["production_action"], anchor["selected_action"]),
            "action_distance_label": action_distance_label(action_distance(anchor["production_action"], anchor["selected_action"])),
            "queue_ns": q_ns, "queue_ew": q_ew, "queue_total": q_ns + q_ew,
            "queue_imbalance_abs": abs(q_ns - q_ew), "phase_elapsed": state["phase_elapsed"],
            "signal_phase": state["signal_phase"], "decision_time": decision_time,
            "epsilon": anchor["epsilon"], "mirror_absolute_error": mirror["absolute_error"],
            "mirror_signed_error": mirror["signed_error"], "alternative_absolute_error": selected["absolute_error"],
            "alternative_signed_error": selected["signed_error"], "selected_gain_error": selected["gain_error"],
            "estimated_gain": selected["estimated_gain"], "reference_gain": selected["reference_gain"],
            "estimated_improvement": anchor["estimated_improvement"], "reference_improvement": anchor["reference_improvement"],
            "gate_margin": anchor["estimated_improvement"] - anchor["epsilon"],
            "selected_epsilon_coverage": anchor["selected_epsilon_coverage"],
            "gate_passed": anchor["gate_passed"], "recommendation_outcome": anchor["recommendation_outcome"],
            "reference_positive": anchor["reference_positive"], "any_reference_positive": anchor["any_reference_positive"],
            "full_ranking_agreement": anchor["full_ranking_agreement"], "regret_sign_agreement": anchor["regret_sign_agreement"],
            "choice_value_loss": anchor["choice_value_loss"],
            "reference_kind": anchor["reference_kind"],
        })
    return merged


def make_summary(rows, group_columns):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[name] for name in group_columns)].append(row)
    result = []
    for key, values in sorted(groups.items()):
        total = len(values)
        row = dict(zip(group_columns, key))
        row.update({
            "anchors": total,
            "share_of_group": None,  # populated by callers with an explicit denominator
            "fp": sum(value["recommendation_outcome"] == "FP" for value in values),
            "fn": sum(value["recommendation_outcome"] == "FN" for value in values),
            "tp": sum(value["recommendation_outcome"] == "TP" for value in values),
            "tn": sum(value["recommendation_outcome"] == "TN" for value in values),
            "gate_pass_rate": sum(value["gate_passed"] for value in values) / total,
            "coverage_rate": sum(value["selected_epsilon_coverage"] for value in values) / total,
            "median_mirror_absolute_error": median([value["mirror_absolute_error"] for value in values]),
            "median_alternative_absolute_error": median([value["alternative_absolute_error"] for value in values]),
            "median_estimated_gain": median([value["estimated_gain"] for value in values]),
            "median_reference_gain": median([value["reference_gain"] for value in values]),
            "median_reference_improvement": median([value["reference_improvement"] for value in values]),
            "median_queue_total": median([value["queue_total"] for value in values]),
            "median_queue_imbalance_abs": median([value["queue_imbalance_abs"] for value in values]),
            "median_choice_value_loss": median([value["choice_value_loss"] for value in values]),
        })
        result.append(row)
    return result


def add_denominator(rows, denominator_columns):
    denominators = defaultdict(int)
    for row in rows:
        denominators[tuple(row[name] for name in denominator_columns)] += 1
    for row in rows:
        key = tuple(row[name] for name in denominator_columns)
        row["share_of_group"] = row["anchors"] / denominators[key]


def write_svg(rows, path):
    # Compact heat map: rates of the two asymmetric extreme-error patterns.
    series_order = ["initial_evaluation", "calibration", "heldout_evaluation"]
    mismatches = ["aligned-control", "heterogeneity-omitted", "rate-and-incident-omitted"]
    horizons = [2, 6, 20]
    classes = ["low_mirror_high_alternative", "high_mirror_low_alternative"]
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["series"], row["mismatch_regime"], row["horizon_ticks"])].append(row)
    width, height = 1080, 610
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#1f2937}.title{font-size:18px;font-weight:bold}.label{font-size:12px}.small{font-size:10px}.cell{stroke:#fff;stroke-width:1}</style>',
           '<text x="30" y="30" class="title">Extreme mirror-versus-selected-alternative error patterns</text>',
           '<text x="30" y="49" class="label">Cell color and label are the anchor share; thresholds are series-specific empirical quartiles.</text>']
    colors = {"low_mirror_high_alternative": "#c2410c", "high_mirror_low_alternative": "#1d4ed8"}
    y = 82
    for pattern in classes:
        out.append(f'<text x="30" y="{y}" class="label">{pattern.replace("_", " ")}</text>')
        y += 16
        for series in series_order:
            out.append(f'<text x="30" y="{y + 21}" class="small">{series.replace("_", " ")}</text>')
            x = 200
            for mismatch in mismatches:
                for horizon in horizons:
                    values = grouped[(series, mismatch, horizon)]
                    rate = sum(row["error_taxonomy"] == pattern for row in values) / len(values)
                    alpha = 0.12 + 0.88 * rate
                    out.append(f'<rect class="cell" x="{x}" y="{y}" width="82" height="40" fill="{colors[pattern]}" fill-opacity="{alpha:.3f}"/>')
                    out.append(f'<text x="{x+41}" y="{y+18}" text-anchor="middle" class="small">{rate:.1%}</text>')
                    out.append(f'<text x="{x+41}" y="{y+32}" text-anchor="middle" class="small">H={horizon}</text>')
                    x += 84
                y += 0
            y += 44
        header_y = y - 132
        x = 200
        for mismatch in mismatches:
            out.append(f'<text x="{x+123}" y="{header_y-3}" text-anchor="middle" class="small">{mismatch}</text>')
            x += 252
        y += 24
    out.append('<text x="30" y="590" class="small">Source: immutable confirmatory anchor/action observations. Descriptive only; the reference is an authored production-software environment.</text>')
    out.append('</svg>')
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    rows = []
    thresholds = []
    for series_name, directory in SERIES:
        current = load_series(series_name, directory)
        q1_m, q3_m = percentile([row["mirror_absolute_error"] for row in current], .25), percentile([row["mirror_absolute_error"] for row in current], .75)
        q1_a, q3_a = percentile([row["alternative_absolute_error"] for row in current], .25), percentile([row["alternative_absolute_error"] for row in current], .75)
        thresholds.append({"series": series_name, "anchors": len(current), "mirror_q25": q1_m, "mirror_q75": q3_m, "alternative_q25": q1_a, "alternative_q75": q3_a})
        for row in current:
            row["error_taxonomy"] = error_class(row["mirror_absolute_error"], row["alternative_absolute_error"], q1_m, q3_m, q1_a, q3_a)
            rows.append(row)
    rows.sort(key=lambda row: (row["series"], row["run_id"], row["anchor_index"]))
    write_csv(TABLES / "failure_taxonomy.csv", rows)
    write_csv(TABLES / "failure_taxonomy_thresholds.csv", thresholds)
    summary = make_summary(rows, ("series",) + CELL + ("error_taxonomy",))
    add_denominator(summary, ("series",) + CELL)
    write_csv(TABLES / "failure_taxonomy_summary.csv", summary)
    pairs = make_summary(rows, ("series", "action_pair", "action_distance_label", "error_taxonomy"))
    add_denominator(pairs, ("series", "action_pair"))
    write_csv(TABLES / "failure_taxonomy_action_pair.csv", pairs)
    state = make_summary(rows, ("series", "error_taxonomy", "signal_phase"))
    add_denominator(state, ("series",))
    write_csv(TABLES / "failure_taxonomy_state_profile.csv", state)
    write_svg(rows, FIGURES / "failure-taxonomy-extremes.svg")

    classes = ["low_mirror_high_alternative", "high_mirror_low_alternative", "low_mirror_low_alternative", "high_mirror_high_alternative", "intermediate"]
    overview = make_summary(rows, ("series", "error_taxonomy"))
    add_denominator(overview, ("series",))
    by_outcome = make_summary(rows, ("series", "error_taxonomy", "recommendation_outcome"))
    add_denominator(by_outcome, ("series", "error_taxonomy"))
    markdown = [
        "# Exploratory failure analysis: confirmatory reference-fidelity factorial",
        "",
        "**Status:** Exploratory deterministic descriptive analysis of completed immutable artifacts (2026-09-28). It is neither a new experiment nor a replacement decision rule.",
        "",
        "## Question",
        "",
        "Where, in the completed factorial records, do mirror and selected-alternative errors separate, and what recorded factors, action pairs, anchor states, predicted/reference gains, and gate outcomes co-occur with those patterns?",
        "",
        "## Evidence and method",
        "",
        "The analysis reads all three immutable series: `results/reference-fidelity/confirmatory-evaluation-20260928/`, `results/reference-fidelity/confirmatory-calibration-20260928/`, and `results/reference-fidelity/confirmatory-replacement-evaluation-20260928/`. It joins each comparable anchor observation to its same-action mirror and fixed-rule selected-alternative action observation, then extracts the canonical anchor state. The deterministic generator is `experiments/analyze_failure_taxonomy.py`; it only writes the listed `research/` artifacts.",
        "",
        "Each series contributes 2,160 comparable anchor observations (720 seed × cell runs with three repeated anchors), for 6,480 observations total. Anchors are shown as descriptive exposures; they are not independent replicates. The confirmatory independent unit remains the seed × full-cell run in `research/evidence/cycle2/confirmatory_factorial_amendment.md`.",
        "",
        "For each series separately, `low` means absolute error at or below the empirical 25th percentile and `high` means at or above the 75th percentile. The selected alternative is the gate's recorded fixed-order choice, so this is a decision-path decomposition rather than a claim about every unselected alternative. `action_distance` is a contract-space proxy: 1 for BALANCED versus a directional action and 2 for an NS/EW directional reversal. It is not a physical distance.",
        "",
        "| Series | Anchors | Mirror q25 / q75 | Selected-alternative q25 / q75 |",
        "|---|---:|---:|---:|",
    ]
    for row in thresholds:
        markdown.append(f"| {row['series']} | {row['anchors']} | {fmt(row['mirror_q25'])} / {fmt(row['mirror_q75'])} | {fmt(row['alternative_q25'])} / {fmt(row['alternative_q75'])} |")
    markdown += ["", "## Descriptive taxonomy", "", "| Series | Error pattern | Anchors | Share | FP | FN | Gate-pass rate | Coverage rate | Median mirror / alternative error | Median reference gain |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in overview:
        markdown.append(f"| {row['series']} | {row['error_taxonomy']} | {row['anchors']} | {row['share_of_group']:.1%} | {row['fp']} | {row['fn']} | {row['gate_pass_rate']:.1%} | {row['coverage_rate']:.1%} | {fmt(row['median_mirror_absolute_error'])} / {fmt(row['median_alternative_absolute_error'])} | {fmt(row['median_reference_gain'])} |")
    markdown += [
        "",
        "The asymmetric strata are the diagnostic target. `low_mirror_high_alternative` means a locally small same-action error co-occurred with a large error on the selected alternative; `high_mirror_low_alternative` is the converse. Neither pattern shows that mirror error causes alternative error, or that any factor causes the pattern. The initial and held-out evaluations remain separate because the held-out series is the relevant disjoint replication; calibration was used only for the frozen multiplier selection.",
        "",
        "## Outcome mix within the asymmetric patterns",
        "",
        "| Series | Pattern | Outcome | Anchors | Share within pattern | Median estimated / reference gain | Median choice-value loss |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in by_outcome:
        if row["error_taxonomy"] in ("low_mirror_high_alternative", "high_mirror_low_alternative"):
            markdown.append(f"| {row['series']} | {row['error_taxonomy']} | {row['recommendation_outcome']} | {row['anchors']} | {row['share_of_group']:.1%} | {fmt(row['median_estimated_gain'])} / {fmt(row['median_reference_gain'])} | {fmt(row['median_choice_value_loss'])} |")
    markdown += [
        "",
        "## Factor, state, and action-pair decomposition",
        "",
        "The full audit tables preserve every crossed factor (horizon, demand, incident, and authored mismatch), action pair, state-derived queues and phase, gains, and outcome: `research/tables/failure_taxonomy.csv`, `research/tables/failure_taxonomy_summary.csv`, `research/tables/failure_taxonomy_action_pair.csv`, and `research/tables/failure_taxonomy_state_profile.csv`. The summary table is grouped by series × full factorial cell × taxonomy stratum; it is the appropriate source for checking co-occurrence by every factor rather than promoting a pooled rate to a factor effect. The figure `research/figures/failure-taxonomy-extremes.svg` visualizes the two asymmetric strata by series, horizon, and mismatch, pooled across demand and incident only for display.",
        "",
        "Recorded anchor payloads provide starting state (queue NS/EW, phase, and elapsed phase) and the raw action tables provide predicted and authored-reference utilities/gains. They do **not** retain per-tick estimated/reference state trajectories or a trajectory-divergence measure. Accordingly this analysis reports utility/gain error and choice-value loss only; it cannot attribute failure to a particular divergent transition or trajectory segment.",
        "",
        "## Findings and limits",
        "",
        "The records directly demonstrate that a small mirror error can co-occur with a high selected-alternative error, and the reverse pattern also occurs under the deterministic quartile definition. The factor/action/state tables locate those records in the constructed factorial but provide no causal identification: factors are crossed, yet anchors are repeated within run, mismatch mechanisms are bundled in `rate-and-incident-omitted`, and the analysis conditions on a selected action produced by the same gate whose performance is being described. The oracle is independent of `ShadowWorldModel` only; it remains an `AUTHORED_PRODUCTION_SOFTWARE_ENVIRONMENT`, not physical or factual counterfactual ground truth. These limitations and the failed global rule are preserved in `research/evidence/cycle2/red_team_factorial_review.md` and `research/tables/confirmatory-factorial-synthesis/cross-holdout-synthesis.md`.",
        "",
        "## Exploratory protocol and what remains predeclared",
        "",
        "This post hoc protocol fixes the source directories, comparable-anchor join keys, selected-action definition, series-specific quartile cut points, five mutually exclusive error strata, action-distance proxy, and descriptive outputs before interpreting the generated tables. It does not test significance, compute confidence intervals, choose a threshold, or alter the gate. It therefore cannot revise the pre-execution protocol or rescue the current gate.",
        "",
        "A future predeclared test should specify the error strata and thresholds before data collection; include separately crossed rate-only and incident-knowledge-only mismatch mechanisms; generate matched closed-loop anchors; retain per-tick reference and SEM trajectories with a prespecified divergence metric; cluster inference at the seed/run level; and evaluate a frozen regime detector plus abstention policy on a new disjoint held-out series. It would still need a separately maintained and validated reference before any stronger validity claim. No current result authorizes policy learning.",
        "",
        "## Next actions",
        "",
        "Preserve the immutable result series and use this taxonomy only to design the next protocol. Keep learning blocked under the current evidence status.",
    ]
    (ROOT / "research" / "failure_analysis.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} comparable anchor rows")


if __name__ == "__main__":
    main()
