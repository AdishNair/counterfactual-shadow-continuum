"""Regenerate an evidence table from paired run summaries, without dependencies."""
import argparse
import json
from pathlib import Path
from csc.runner import distribution


def report(root):
    root = Path(root)
    rows = json.loads((root / "matrix-summary.json").read_text())
    text = ["# Measured local CSC smoke experiment", "",
            "Generated from matrix-summary.json and its referenced raw run artifacts. "
            "All outcomes concern a software environment. This is a short local validation, "
            "not the specification's full 500/10,000-epoch cluster protocol.", "",
            "K counts alternative actions; each K>0 run adds one mirror. "
            "Production policy is unchanged. Latencies include Python instrumentation; "
            "local epochs wait for bounded shadow completion before the next epoch.", "",
            "| K | Runs | Median epoch ms | Median production decision ms | Median fidelity gap | Median discounted regret |", 
            "|---:|---:|---:|---:|---:|---:|"]
    for k in sorted({r["k"] for r in rows}):
        group = [r["summary"] for r in rows if r["k"] == k]
        vals = [distribution([s["timing"]["epoch_ms"]["median"] for s in group])["median"],
                distribution([s["timing"]["production_decision_ms"]["median"] for s in group])["median"],
                distribution([s["fidelity_gap"]["median"] for s in group])["median"],
                distribution([s["regret_discounted"]["median"] for s in group])["median"]]
        text.append(f"| {k} | {len(group)} | " + " | ".join("N/A" if v is None else f"{v:.4f}" for v in vals) + " |")
    text.extend(["", "Paired checks (same seed across K):", ""])
    for seed in sorted({r["seed"] for r in rows}):
        group = [r for r in rows if r["seed"] == seed]
        same_workload = len({r["summary"]["workload_sha256"] for r in group}) == 1
        same_production = len({r["summary"]["production_semantic_sha256"] for r in group}) == 1
        text.append(f"- Seed {seed}: workload hashes identical={same_workload}; production trajectories identical={same_production}.")
    escapes = sum(r["summary"]["unauthorized_production_mutations_from_shadow"] for r in rows)
    text.extend(["", f"Environment audit: {escapes} commands with an unexpected gateway correlation/action. "
                 "This checks application routing; it does not establish OS/network containment.", "",
                 "No learning was run. Equal production trajectories are expected: "
                 "counterfactual evidence is recorded but does not change the policy. "
                 "The mirror error is a calibration diagnostic at the production action, "
                 "not a confidence bound on unexecuted actions.", ""])
    (root / "REPORT.md").write_text("\n".join(text), encoding="utf-8")
    return root / "REPORT.md"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", default="results/matrix", nargs="?")
    print(report(parser.parse_args().root))
