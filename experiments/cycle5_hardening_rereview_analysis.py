"""Verify and report second post-review correctness source without performance claims."""
import hashlib
import json
from pathlib import Path
import re

from csc.contracts import canonical, digest


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "results/cycle5-validation/post-review-hardening-20261006-v2"
    manifest = json.loads((directory / "manifest.json").read_text())
    broken = [name for name, expected in manifest["artifact_hashes"].items()
              if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected]
    changed = [name for name, expected in manifest["after_source_hashes"].items()
               if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected]
    log = (directory / "unittest.log").read_text()
    match = re.search(r"Ran (\d+) tests in ([\d.]+)s", log)
    runtime_changed = [name for name in changed if name.startswith(("csc/", "tests/"))]
    if broken or runtime_changed or manifest["status"] != "COMPLETE" or not match or "\nOK\n" not in log:
        raise ValueError(f"gate integrity mismatch {broken}, {changed}")
    negatives = {row["mode"]: json.loads(row["stdout"]) for row in manifest["negative_probes"]}
    csc_hashes = {name: value for name, value in manifest["after_source_hashes"].items() if name.startswith("csc/")}
    summary = {"status": "LOCALLY_TESTED_POST_MEASUREMENT", "gate_tests": int(match[1]), "gate_seconds": float(match[2]),
               "validation_path": directory.relative_to(root).as_posix(), "broken_artifact_hashes": broken,
               "source_changes_after_gate": changed, "runtime_test_source_changes_after_gate": runtime_changed,
               "source_identity_sha256": manifest["source_identity_sha256"],
               "csc_source_identity_sha256": digest(csc_hashes), "negative_probes": negatives,
               "analysis_script_identity_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "manifest_sha256": hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest(),
               "performance_claim": "No post-hardening main or long-run measurement",
               "open_runtime_metadata_issue": {"status": "OPEN_IDENTIFIED_IMPLEMENTATION_PATH", "field": "runtime.cpu_ms",
                   "mechanism": "String CPU metadata can pass lease validation; synchronous runner then sums cpu_ms and raises TypeError",
                   "evidence_type": "source-established path; not a main-run failure or measured frequency",
                   "scope": "Do not claim every downstream-consumed runtime field is validated"},
               "disposition": "Corrected tested source paths; independent closure judgment remains separate"}
    (root / "research/tables/cycle5_post_review_hardening_v2.json").write_bytes(canonical(summary))
    table = ["| Before-80-gate source probe | Outcome | Worker republished | Additional observation |", "|---|---|---|---|"]
    for name, row in negatives.items():
        additional = "Mirror norm overflowed to infinity" if name == "mirror" else "Synthetic cleanup denied" if name == "cleanup" else "String execution timing" if name == "runtime" else "Body limit crossed by enrichment"
        table.append(f"| {name} | {row['status']} | {row['worker_returned']} | {additional} |")
    report = f"""# Cycle 5 second post-review hardening

**Status:** Implemented and locally tested after main measurement. The new full
gate passed {summary['gate_tests']} tests in {summary['gate_seconds']:.3f} seconds.
The 80-test source archive, first independent re-review and all main results are
preserved. No main performance study was rerun or reinterpreted as the new source.

## Question, evidence and method

The first independent re-review retained R2/R4 as MAJOR because destruction errors
could republish suspect workers, rejection-producing enrichment occurred after
lease release, and child creation/cleanup had ownership gaps. The question is
whether those named paths can be corrected and regression-tested while preserving
negative measurement evidence, production authority, trust D and blocked learning.

Raw immutable evidence is `{summary['validation_path']}/`: BEFORE source is the
80-test post-review variant; AFTER includes all CSC, test and experiment Python
files executed by this gate. Manifests preserve config hash, seed, factors,
environment, script identity, source and artifact hashes. There are zero broken
artifact hashes and zero CSC/test source changes after the gate. Unrelated offline
experiment scripts changed afterward: `{changed}`. The immutable gate manifest
reports no source changes during execution. Full archived closure identity:
`{summary['source_identity_sha256']}`; CSC-only identity:
`{summary['csc_source_identity_sha256']}`.

`experiments/cycle5_hardening_rereview_analysis.py` deterministically verifies and
generates this artifact and `research/tables/cycle5_post_review_hardening_v2.json`.

## Preserved BEFORE negative findings

{chr(10).join(table)}

These are bounded synthetic probes of the archived 80-test source, not failures
observed in the 86-run main series. They validate the independent review's
specific rejection/republication predictions. Creation/cleanup race corrections
also have new positive adversarial tests; no fabricated old-run frequency follows.

## Current corrections and tested findings

Quarantine is irrevocable before destruction: the local lease variable is cleared
before cleanup, and the manager marks the emitter quarantined before `close()`.
Failed destruction leaves an owned, non-reusable object and its slot reserved;
replacement cannot silently grow the worker population. A permission-error test
injects invalid output and failed destruction, verifies no worker token is
republished, and verifies no replacement is launched until ownership resolves.

Lease-held validation now checks execution timing type, finiteness and nonnegative
value; applies a conservative nonnegative-queue/input envelope preventing mirror
distance overflow; and performs runtime enrichment followed by the final body
bound while still holding the process. The body field is stabilized after
enrichment. String/negative timing, finite-coordinate overflowing mirror distance
and post-enrichment size overflow all fault and destroy the tested emitter.
The conservative mirror envelope can reject extreme legitimate values; it does
not replace the coordinator's independent production-comparison validation.

Warm construction reserves manager capacity before process creation and registers
the returned child before helper creation or readiness. The constructor's cleanup
guard covers spawn, ownership callback, helper startup and readiness. Partial
helper-start failure reaps a real child. Failed replacement construction is
tracked/reaped and a subsequent valid request can recover. A concurrent warm
construction/close test confirms the shutdown flag prevents an escaped child.

Cold dispatch checks closure before spawning and immediately after registering
the child. An actual spawn paused across a concurrent close is then immediately
killed and reaped. The failure path's second `communicate()` has a five-second
timeout; failed termination/settlement retains process ownership instead of
erasing it. Synthetic termination-denied and second-communication-timeout cases
verify that ownership remains explicit and later confirmed settlement clears it.

Shutdown attempts every owned resource even when one abort/close fails. It records
bounded cleanup error history, retains unresolved handles, and raises an explicit
incomplete-cleanup failure. A two-worker permission-error fixture proves the
second actual process is still attempted/reaped; successful retry confirms empty
ownership and `cleanup_complete`. Creation reservations, quarantine counts and
cleanup status are visible. Killing processes still precedes executor joins.

The owned executor's physical capacity regression remains, with a new concurrent
submit/cancel/dequeue/shutdown test. A separate **orchestration-only** fixture uses
five distinct synthetic choice labels to verify requested/admitted/completed K,
mirror exclusion, drops and completeness. It executes no traffic model or
actuation; the traffic config still rejects K>2, and no empirical K>2 claim follows.

The full gate includes the campaign agent's 13 cleanup/launcher regressions,
including a disposable real Windows process tree and an integrated stop-before-
next-condition case. Their exact scope is reported in the campaign hardening
artifact; raw main pressure measurements retain their original limits.

## Review boundary, limitations and next actions

**OPEN implementation issue:** Optional `runtime.cpu_ms` is not type-checked by
the lease validator. A string there can pass current validation, while the
synchronous runner subsequently computes a sum of branch CPU values and raises
`TypeError`. This is a concrete source-established rejection/consumption mismatch,
not a measured main-run failure or an estimate of failure frequency. No broad
assertion that all downstream-consumed runtime fields are validated is justified.
It remains visible pending independent judgment; the frozen 96-test source has
not been changed to hide it. The typed execution-time checks above address their
named transport-overhead path, not this separate CPU aggregation path.

These changes support corrected ownership/quarantine/validation paths under the
tested first-party contract. Independent re-review must determine finding closure;
passing tests alone do not close broad implementation or systems claims.
Readiness, write/receive, process settlement, helper joins and executor joins have
explicit operation limits. Serialization/validation and OS scheduling are not an
absolute real-time assignment guarantee, and software cannot prove termination
when the OS denies it. Such errors remain quarantined, owned and reported.

The new physical count cap is not a measured aggregate RSS/byte quota. Archived
evidence and exact offline reductions still grow. Storage availability R1, memory
trends R5, cadence R6 and delayed evidence yield R7 remain unresolved; no storage
failover, policy learning, trust redesign, second domain or hostile isolation was
added. Earlier negative controls, source variants and result directories remain
immutable. Trust remains D and learning BLOCKED.

Cycle 6 needs a fresh protocol and measurement source before performance claims
for this variant, plus explicit production/evidence storage contracts, longer
memory/quota validation and operating-region cadence/yield requirements.
"""
    (root / "research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v2.md").write_text(report, encoding="utf-8")
    print(json.dumps({"status": summary["status"], "tests": summary["gate_tests"], "seconds": summary["gate_seconds"],
                      "csc_source_identity_sha256": summary["csc_source_identity_sha256"], "broken_hashes": broken, "source_changed": changed}))


if __name__ == "__main__":
    main()
