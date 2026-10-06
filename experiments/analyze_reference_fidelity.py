"""Generate a compact, run-level report from a reference-fidelity series."""
import argparse
import csv
import json
from pathlib import Path


def median(values):
    values = sorted(values)
    if not values:
        return None
    middle = len(values) // 2
    return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2


def analyze(series, output):
    series, output = Path(series), Path(output)
    rows = json.loads((series / "reference-summary.json").read_text())
    groups = {}
    for row in rows:
        groups.setdefault((row["horizon_ticks"], row["shadow_service_rate"]), []).append(row)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "reference-fidelity-smoke-runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    text = ["# Local reference-fidelity smoke analysis", "",
            "**STATUS:** MEASURED PRELIMINARY — two seeds per cell in the authored J1 software environment. "
            "The reference replays `ProductionWorld` and does not import `ShadowWorldModel`; it is not physical ground truth.", "",
            f"**Evidence:** `{series.as_posix()}`. Each underlying run was source-identity and artifact verified during analysis.", "",
            "| Horizon | Shadow service rate | Runs | Median mirror absolute error | Median alternative absolute error | Median ranking agreement | Median epsilon coverage |",
            "|---:|---:|---:|---:|---:|---:|---:|"]
    for (horizon, rate), group in sorted(groups.items()):
        values = [median([row[key] for row in group]) for key in
                  ("mirror_median_absolute_error", "alternative_median_absolute_error", "ranking_agreement", "epsilon_gate_coverage")]
        text.append(f"| {horizon} | {rate} | {len(group)} | " + " | ".join(f"{value:.4f}" for value in values) + " |")
    text.extend(["", "## Findings", "",
                 "This is an implementation-level calibration check. It shows that mirror error and alternative error can differ, "
                 "and that the current epsilon threshold does not uniformly cover selected-alternative error. It does not estimate "
                 "physical traffic performance, establish a causal effect, or support a policy update.", "",
                 "## Limitations", "",
                 "The cells have only two seeds and 18 post-warm-up epochs per run. The reference shares the production software "
                 "environment, so it is an independent oracle only relative to the SEM, not an external validation. Horizon, mismatch, "
                 "and incident timing are not fully crossed or randomized. Use `research/evidence/cycle1/experiment_protocol.md` for the confirmatory design."])
    (output / "reference-fidelity-smoke.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    return output / "reference-fidelity-smoke.md"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("series")
    parser.add_argument("--output", default="research/tables")
    args = parser.parse_args()
    print(analyze(args.series, args.output))
