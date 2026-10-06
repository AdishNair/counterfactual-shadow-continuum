"""Deterministically verify and summarize the immutable v3 correction gate."""
import hashlib
import json
from pathlib import Path
import re

from csc.contracts import canonical


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "results/cycle5-validation/post-review-hardening-20261006-v3"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((DIRECTORY / "manifest.json").read_text())
    broken = [name for name, expected in manifest["artifact_hashes"].items()
              if sha(DIRECTORY / name) != expected]
    current_changes = [name for name, expected in manifest["source_hashes"].items()
                       if not (ROOT / name).is_file() or sha(ROOT / name) != expected]
    runtime_changes = [name for name in current_changes if name.startswith(("csc/", "tests/"))
                       or name == "experiments/cycle5_async.py"]
    log = (DIRECTORY / "unittest.log").read_text()
    match = re.search(r"Ran (\d+) tests in ([\d.]+)s", log)
    if (manifest["status"] != "COMPLETE" or manifest["exit_code"] != 0 or
            broken or runtime_changes or not match or "\nOK\n" not in log):
        raise ValueError({"broken": broken, "runtime_changes": runtime_changes})
    negatives = {row["mode"]: {**row, "parsed": json.loads(row["stdout"]) if row["stdout"] else None}
                 for row in manifest["negative_probes"]}
    summary = {
        "status": "LOCALLY_TESTED_POST_MEASUREMENT",
        "tests": int(match[1]), "test_seconds": float(match[2]),
        "gate_elapsed_s": manifest["gate_elapsed_s"],
        "validation_path": DIRECTORY.relative_to(ROOT).as_posix(),
        "source_identity_sha256": manifest["source_identity_sha256"],
        "csc_source_identity_sha256": manifest["csc_source_identity_sha256"],
        "manifest_sha256": sha(DIRECTORY / "manifest.json"),
        "broken_artifact_hashes": broken,
        "source_changed_during_gate": manifest["source_changed_during_gate"],
        "runtime_source_changes_after_gate": runtime_changes,
        "other_gate_source_changes_after_gate": [name for name in current_changes if name not in runtime_changes],
        "negative_controls": negatives,
        "analysis_script_sha256": sha(Path(__file__)),
        "performance_claim": "none; measured 86-run archive unchanged",
        "remaining_empirical_findings": ["R1 storage availability", "R5 positive memory trend/offline allocation",
                                         "R6 cadence variability", "R7 delayed evidence yield"]}
    (ROOT / "research/tables/cycle5_post_review_hardening_v3.json").write_bytes(canonical(summary))
    report = f"""# Cycle 5 third post-review hardening

**Status:** Implemented and locally tested after the immutable main measurements.
The source-bound v3 gate passed **{summary['tests']} tests in {summary['test_seconds']:.3f} seconds**.
This is correctness evidence only; no cadence, yield, memory or storage experiment
was rerun.

## Question, evidence and method

The second independent re-review identified two remaining MAJOR runtime paths:
a dequeued warm task could wait forever for a lease token during closure, and
unresolved cold processes did not consume later creation capacity. It also found
incomplete runtime/derived-numeric validation and three qualified campaign cleanup
paths. The correction is archived at `{summary['validation_path']}`.

The gate copied the complete CSC, tests and experiments Python closure, ran the
full suite, and hashed every source and artifact. Full closure identity:
`{summary['source_identity_sha256']}`; CSC identity:
`{summary['csc_source_identity_sha256']}`. Broken artifact hashes:
`{broken}`. Runtime/test/campaign source changes after the gate: `{runtime_changes}`.
The later deterministic analysis script is outside the executed runtime closure.

## Preserved negative controls

The archived v2 source accepted string `runtime.cpu_ms` and returned its worker;
accepted a negative metric yielding utilities `+1e308` and `-1e308`, whose
difference was nonfinite; exceeded the three-second watchdog in the forced
empty-lease shutdown interleaving; and spawned two cold processes despite a
one-process configured capacity after termination denial. Exact probe records are
in the machine table and manifest. These synthetic paths support mechanism
diagnosis, not occurrence rates in the 86-run study.

## Corrections and tests

Warm lease acquisition now waits on a closure-aware condition with a finite
service timeout. Closure sets the flag and wakes all lease waiters before executor
cancellation and process cleanup. Lease return uses the same state boundary and
cannot publish after closure. Tests force the formerly stranded dequeued-task
schedule and an open-pool empty-token timeout.

Cold construction reserves a process slot before `Popen`, atomically replaces the
reservation with owned-process tracking, and counts unresolved live processes
against admission and direct dispatch capacity. A denied-termination fixture
shows a second assignment cannot spawn while the first process remains owned.

The warm result contract now validates required timing/CPU fields, task/reset
metadata, PID/input counters, nullable OS counters, nonnegative domain metrics and
queue traces before releasing the emitter. Utility has an explicit IEEE-754
arithmetic envelope with headroom for epsilon and regret subtraction. Comparison
excludes an invalid production utility instead of serializing a nonfinite record;
regret subtraction independently rejects overflow. Corrupt CPU, boolean counter,
negative metric and extreme-utility fixtures destroy the tested worker.

The campaign launcher now cleans and reaps its owned process tree on non-timeout
communication failure, treats non-object cleanup JSON as uncertainty, records all
later conditions `NOT_ATTEMPTED`, and distinguishes confirmed process absence from
an inconclusive Windows handle error. A future campaign requires an explicitly
supplied source-compatible correctness gate; historical gates do not authorize it.

## Limits and next actions

These changes support the named first-party lifecycle and numeric mechanisms under
tested schedules. They do not prove every concurrency schedule, OS termination,
hostile containment, byte-bounded memory, storage durability or resource
non-interference. Independent review remains separate from this deterministic
report. The original measured source retains R1 storage, R5 memory, R6 cadence and
R7 delayed-yield findings. Trust remains Decision D; learning remains BLOCKED.
"""
    (ROOT / "research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v3.md").write_text(report, encoding="utf-8")
    print(json.dumps({key: summary[key] for key in
                      ("status", "tests", "test_seconds", "broken_artifact_hashes", "runtime_source_changes_after_gate")}))


if __name__ == "__main__":
    main()
