"""Verify and summarize the final post-review correction gate."""
import hashlib
import json
from pathlib import Path
import re

from csc.contracts import canonical

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "results/cycle5-validation/post-review-hardening-20261006-v4"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((DIRECTORY / "manifest.json").read_text())
    broken = [name for name, expected in manifest["artifact_hashes"].items()
              if sha(DIRECTORY / name) != expected]
    changed = [name for name, expected in manifest["source_hashes"].items()
               if not (ROOT / name).is_file() or sha(ROOT / name) != expected]
    runtime_changed = [name for name in changed if name.startswith(("csc/", "tests/"))
                       or name in ("experiments/cycle5_async.py", "experiments/cycle5_pressure.py",
                                   "experiments/cycle5_loss.py", "experiments/replay.py")]
    log = (DIRECTORY / "unittest.log").read_text()
    match = re.search(r"Ran (\d+) tests in ([\d.]+)s", log)
    if (manifest["status"] != "COMPLETE" or manifest.get("gate_passed") is not True or
            manifest["exit_code"] or broken or runtime_changed or not match or "\nOK\n" not in log):
        raise ValueError({"broken": broken, "runtime_changed": runtime_changed})
    negatives = {row["mode"]: json.loads(row["stdout"]) for row in manifest["negative_probes"]}
    summary = {
        "status": "LOCALLY_TESTED_POST_MEASUREMENT", "tests": int(match[1]),
        "test_seconds": float(match[2]), "gate_elapsed_s": manifest["gate_elapsed_s"],
        "validation_path": DIRECTORY.relative_to(ROOT).as_posix(),
        "source_identity_sha256": manifest["source_identity_sha256"],
        "csc_source_identity_sha256": manifest["csc_source_identity_sha256"],
        "manifest_sha256": sha(DIRECTORY / "manifest.json"),
        "broken_artifact_hashes": broken, "source_changed_during_gate": manifest["source_changed_during_gate"],
        "runtime_source_changes_after_gate": runtime_changed,
        "other_source_changes_after_gate": [name for name in changed if name not in runtime_changed],
        "negative_controls": negatives, "analysis_script_sha256": sha(Path(__file__)),
        "performance_claim": "none; no corrected-source main or long-run experiment"}
    (ROOT / "research/tables/cycle5_post_review_hardening_v4.json").write_bytes(canonical(summary))
    report = f"""# Cycle 5 final post-review hardening

**Status:** Implemented and locally tested after the immutable Cycle 5 measurements.
The final source-bound gate passed **{summary['tests']} tests in {summary['test_seconds']:.3f} seconds**.
No performance, memory, storage or evidence-yield run was repeated.

## Question, evidence and method

The v3 independent re-review narrowly closed the two R2 lifecycle mechanisms and
the utility-difference counterexample, while identifying bounded gaps in CPU
aggregation, cold-response validation, final-condition cleanup disposition,
Windows exit inspection and readiness-gate compatibility. The immutable final
gate is `{summary['validation_path']}`. Full closure identity:
`{summary['source_identity_sha256']}`; CSC identity:
`{summary['csc_source_identity_sha256']}`. Artifact hash failures: `{broken}`;
runtime/test/campaign changes after the gate: `{runtime_changed}`.

The validator archives the prior v3 source, runs four negative controls against
it, snapshots all current CSC/tests/experiments Python sources, runs the full
suite and records environment/config/script/artifact hashes. The later analysis
script is outside the runtime gate and is identified separately in the machine
table.

## Preserved v3 negative controls

- Two accepted `cpu_ms=1e308` values produced a nonfinite sum and returned the
  worker.
- A cold result with string `cpu_ms` was accepted as `REPORTED`.
- Final-condition uncertain cleanup left both row and campaign marked `COMPLETE`.
- The v3 manifest failed closed because the preparation path required a different
  passing-field format.

These are synthetic source-specific mechanisms, not observed main-run frequencies.

## Corrections and tested findings

The worker CPU contract now reserves finite headroom for every requested branch
in the declared finite run, before a reusable worker is released. The common
runtime, metric, trace and arithmetic contract is applied to local cold and warm
results; warm-only reset metadata remains conditional. Tests inject extreme CPU,
string CPU and negative metrics across both modes.

Uncertain cleanup now changes the current row to `FAILED`, including the last
condition, so aggregate completion cannot remain `COMPLETE`. The disposable
Windows test acquires a synchronization handle while the descendant is known
alive and requires an explicit signaled wait result after cleanup.

Future campaign preparation accepts either the historical `gate_passed` form or
a `status=COMPLETE` gate with exit code zero, then verifies current hashes for all
CSC/tests plus the campaign, pressure, loss and replay helpers. A regression
builds such a manifest from current source, archives it, and separately proves
that omitting the explicit gate still fails before collection.

## Limitations and next actions

This gate supports only the named cooperative first-party correctness mechanisms.
It cannot establish every schedule, OS kill success, hostile containment,
resource isolation, byte/RSS boundedness, storage durability or performance.
An independent static review remains separate. The measured source retains its
R1 storage, R5 memory, R6 cadence and R7 delayed-yield findings. Any future
performance collection needs a separately frozen protocol and unique directory.
Trust remains Decision D; learning remains BLOCKED.
"""
    (ROOT / "research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v4.md").write_text(report, encoding="utf-8")
    print(json.dumps({key: summary[key] for key in
                      ("status", "tests", "test_seconds", "broken_artifact_hashes", "runtime_source_changes_after_gate")}))


if __name__ == "__main__":
    main()
