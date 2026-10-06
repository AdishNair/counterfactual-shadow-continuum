"""Read-only deterministic decomposition of immutable Cycle 4 async evidence."""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import statistics

from csc.contracts import canonical
from experiments.replay import read_lines, sha256_file


def analyze(series, output):
    series, output = Path(series), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    registry = json.loads((series / "preregistration.json").read_text())["registry"]
    epochs, runs = [], []
    for row in registry:
        if not row["mode"].startswith("async"):
            continue
        path = series / "runs" / row["run_id"]
        config = json.loads((path / "manifest.json").read_text())["config"]
        lifecycle = list(read_lines(path / "lifecycle.jsonl"))
        by_id = defaultdict(list)
        for event in lifecycle:
            by_id[event.get("branch_id")].append(event)
        branch_reasons, overhead, executions, hydrations, queue_delays = Counter(), [], [], [], []
        complete, reported, planned, incomplete = 0, 0, 0, 0
        epoch_reasons = Counter()
        for record in read_lines(path / "cfr.jsonl"):
            if record["epoch"] < config["warmup_epochs"]:
                continue
            branches = record["branches"][1:]
            reasons = Counter()
            complete += record["evidence_completeness"] == "COMPLETE_COMPARISON"
            reported += sum(b["status"] == "REPORTED" for b in branches)
            planned += len(branches)
            for branch in branches:
                if branch["status"] == "REPORTED":
                    continue
                flags = branch.get("failure_flags", [])
                if branch["status"] == "DROPPED":
                    reason = "queue_admission_failure"
                elif branch["status"] == "EXPIRED":
                    reason = "shutdown" if "shutdown" in flags else "pending_capacity" if "epoch_capacity" in flags else "deadline_expiry"
                elif branch["status"] == "TIMEOUT":
                    reason = "execution_timeout"
                elif branch["status"] == "FAULTED":
                    reason = "worker_or_transport_failure"
                elif branch["status"] == "REJECTED":
                    reason = "identity_or_numeric_rejection"
                else:
                    reason = "other:" + branch["status"]
                reasons[reason] += 1
                branch_reasons[reason] += 1
            if reasons:
                incomplete += 1
                key = "+".join(sorted(reasons))
                epoch_reasons[key] += 1
            epochs.append(dict(**row, epoch=record["epoch"], complete=not bool(reasons),
                               planned_branches=len(branches), reported_branches=sum(b["status"] == "REPORTED" for b in branches),
                               loss_reason_set="+".join(sorted(reasons)) or "none", branch_loss_counts=dict(reasons)))
        for bid, events in by_id.items():
            starts = [e["monotonic_s"] for e in events if e["status"] == "RUNNING"]
            queued = [e["monotonic_s"] for e in events if e["status"] == "QUEUED"]
            if starts and queued:
                queue_delays.append((starts[0] - queued[0]) * 1000)
            for event in events:
                runtime = event.get("worker_runtime", {})
                if runtime and event.get("epoch", -1) >= config["warmup_epochs"]:
                    if "dispatch_roundtrip_ms" in runtime and "execution_ms" in runtime:
                        overhead.append(runtime["dispatch_roundtrip_ms"] - runtime["execution_ms"])
                    executions.append(runtime.get("execution_ms", 0))
                    hydrations.append(runtime.get("hydrate_ms", 0))
        runs.append(dict(**row, complete_epochs=complete, incomplete_epochs=incomplete,
                         measured_epochs=config["duration_epochs"] - config["warmup_epochs"],
                         planned_branches=planned, reported_branches=reported,
                         branch_loss_counts=dict(branch_reasons), epoch_loss_counts=dict(epoch_reasons),
                         reported_or_late_dispatch_nonexecution_median_ms=statistics.median(overhead) if overhead else None,
                         execution_median_ms=statistics.median(executions) if executions else None,
                         hydration_median_ms=statistics.median(hydrations) if hydrations else None,
                         observed_queue_to_running_median_ms=statistics.median(queue_delays) if queue_delays else None))
    report = dict(source_series=str(series), analysis_script_sha256=sha256_file(__file__), runs=runs,
                  limitations=["Archive has no process-ready timestamp: dispatch nonexecution includes process launch, Python imports, serialization, transport and scheduler delay; cannot causally partition worker startup.",
                               "RUNNING is coordinator observation of a thread future, not subprocess start or execution start.",
                               "Reported branches are accepted before epoch deadline; lifecycle late successful results are distinct from usable comparable evidence.",
                               "No archived result-store/flush timing, OS worker RSS or reliable shared resource contention measurements."])
    (output / "cycle5_cycle4_loss.json").write_bytes(canonical(report))
    fields = ["kind", "seed", "mode", "condition", "run_id", "order", "epoch", "complete", "planned_branches", "reported_branches", "loss_reason_set", "branch_loss_counts"]
    with (output / "cycle5_cycle4_epoch_loss.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for epoch in epochs:
            writer.writerow({**epoch, "branch_loss_counts": json.dumps(epoch["branch_loss_counts"], sort_keys=True)})
    groups = []
    for key in sorted({(r["kind"], r["mode"], r["condition"]) for r in runs}):
        selected = [r for r in runs if (r["kind"], r["mode"], r["condition"]) == key]
        counts = Counter()
        reasons = Counter()
        for r in selected:
            counts.update(r["branch_loss_counts"])
            reasons.update(r["epoch_loss_counts"])
        group = dict(kind=key[0], mode=key[1], condition=key[2], runs=len(selected),
                     complete_fraction_median=statistics.median(r["complete_epochs"] / r["measured_epochs"] for r in selected),
                     branch_completion_fraction=sum(r["reported_branches"] for r in selected) / sum(r["planned_branches"] for r in selected),
                     branch_loss_counts=dict(counts), epoch_loss_counts=dict(reasons))
        groups.append(group)
    (output / "cycle5_cycle4_loss_groups.json").write_bytes(canonical(groups))
    lines = ["# Cycle 5 evidence loss analysis", "", "**Status:** Implemented deterministic read-only decomposition of immutable Cycle 4 archives; Cycle 5 attribution is reported in its own results tables.", "",
             "**Question:** Why did logical async decoupling yield little complete comparable evidence?", "",
             f"**Evidence:** `{series}`; `{output / 'cycle5_cycle4_loss.json'}` and epoch-level CSV. Method: exclude each run's declared warmups; classify every unavailable branch from its terminal status and failure flags; retain overlapping loss reasons per epoch rather than force a misleading single cause.", "",
             "| Track | Mode | Condition | Runs | Median complete epoch fraction | Accepted branch fraction | Branch loss counts | Incomplete epoch reason sets |", "|---|---|---|---:|---:|---:|---|---|"]
    for g in groups:
        lines.append(f"| {g['kind']} | {g['mode']} | {g['condition']} | {g['runs']} | {g['complete_fraction_median']:.3f} | {g['branch_completion_fraction']:.3f} | {g['branch_loss_counts']} | {g['epoch_loss_counts']} |")
    normal = [r for r in runs if r["kind"] == "primary" and r["condition"] == "normal"]
    for mode in ("async1", "async2"):
        selected = [r for r in normal if r["mode"] == mode]
        def median(name):
            vals = [r[name] for r in selected if r[name] is not None]
            return statistics.median(vals) if vals else None
        lines += ["", f"Normal {mode}: median across run medians of dispatch nonexecution time = {median('reported_or_late_dispatch_nonexecution_median_ms'):.3f} ms, worker execution = {median('execution_median_ms'):.3f} ms, hydration = {median('hydration_median_ms'):.3f} ms. The large nonexecution component motivates reuse, but is not an identified startup-only measurement."]
    lines += ["", "**Findings:** Whole-batch queue admission and deadline expiry account for the recorded loss; branch completion alone does not imply a full mirror-plus-all-requested-alternatives comparison. Coordinator-observed RUNNING, comparison serialization order and late successful outcomes must retain their timing/provenance distinction.", "", "**Limitations:** " + " ".join(report["limitations"]), "", "**Open questions / next actions:** Measure warm/cold dispatch stages directly without enlarging the 300 ms deadline; preserve cold baseline; record every requested/admitted/completed alternative count and measure bounded history during continuous operation."]
    Path("research/evidence/cycle5/cycle5_evidence_loss_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return groups


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("series")
    parser.add_argument("--output", default="research/tables")
    args = parser.parse_args()
    print(json.dumps(analyze(args.series, args.output), indent=2))
