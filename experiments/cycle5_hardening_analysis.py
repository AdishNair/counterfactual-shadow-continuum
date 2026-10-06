"""Generate the post-review artifact from immutable negative/gate evidence."""
import hashlib
import json
from pathlib import Path
import re

from csc.contracts import canonical, digest


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "results/cycle5-validation/post-review-hardening-20261006-v1"
    manifest = json.loads((directory / "manifest.json").read_text())
    broken = [name for name, expected in manifest["artifact_hashes"].items()
              if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected]
    changed = [name for name, expected in manifest["after_source_hashes"].items()
               if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected]
    if broken or changed or manifest["status"] != "COMPLETE":
        raise ValueError(f"validation mismatch: artifacts={broken}, source={changed}")
    log = (directory / "unittest.log").read_text()
    match = re.search(r"Ran (\d+) tests in ([\d.]+)s", log)
    if not match or "\nOK\n" not in log:
        raise ValueError("gate did not pass")
    negatives = {row["mode"]: row for row in manifest["negative_probes"]}
    physical = json.loads(negatives["physical"]["stdout"])
    invalid = json.loads(negatives["invalid"]["stdout"])
    blocked = json.loads(negatives["blockedpipe"]["stdout"])
    csc_hashes = {name: value for name, value in manifest["after_source_hashes"].items() if name.startswith("csc/")}
    summary = {"status": "LOCALLY_TESTED_POST_MEASUREMENT", "gate_tests": int(match[1]), "gate_seconds": float(match[2]),
               "validation_path": directory.relative_to(root).as_posix(), "broken_artifact_hashes": broken,
               "source_changes_after_gate": changed, "source_identity_sha256": manifest["source_identity_sha256"],
               "csc_source_identity_sha256": digest(csc_hashes), "negative_physical_queue": physical,
               "negative_invalid_reuse": invalid, "negative_blocked_pipe": blocked,
               "negative_blocked_pipe_watchdog_expired": negatives["blockedpipe"]["watchdog_expired"],
               "analysis_script_identity_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "manifest_sha256": hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest(),
               "performance_claim": "No post-hardening main or long-run performance measurement"}
    machine = root / "research/tables/cycle5_post_review_hardening.json"
    machine.write_bytes(canonical(summary))
    report = f"""# Cycle 5 post-review runtime hardening

**Status:** Implemented and locally tested **after** main performance measurement.
All {summary['gate_tests']} regression tests passed in {summary['gate_seconds']:.3f}
seconds. Archived main, fault and earlier gate evidence remains immutable. No new
main performance campaign ran; prior cadence, yield and memory numbers belong to
the measured earlier source variant.

## Question, evidence and method

Can three independently reviewed runtime contract gaps be corrected without
changing production authority, evidence deadlines, trust or learning? The gaps
are unbounded physical executor backlog despite tracked task caps, return of an
invalid warm worker before response validation, and blocking request writes that
precede the response timeout and prevent ordinary executor shutdown.

Evidence: `{summary['validation_path']}/negative_validation.json`, `unittest.log`,
`manifest.json`, and separate `before/` and `after/` source snapshots. The after
archive contains all `csc/*.py`, `tests/*.py` and `experiments/*.py` source in the
executed regression closure. Configuration, seed, environment, script identity
and artifact hashes are included. Deterministic verification/reporting is
`experiments/cycle5_hardening_analysis.py`; machine findings are
`research/tables/cycle5_post_review_hardening.json`. Artifact verification found
zero broken hashes and zero source changes after the gate.

The full closure identity is `{summary['source_identity_sha256']}`; the CSC-only
identity is `{summary['csc_source_identity_sha256']}`. Neither replaces the main
measurement source identity.

## Before-variant negative validation

| Finding | Observed archived-source behavior |
|---|---|
| Physical backlog | With configured tracked capacity {physical['configured_cap']} and one blocked dispatch thread, {physical['submitted_cancelled']} tiny cancelled submissions left {physical['physical_queue_depth']} physical executor work items. This is a controlled queue probe, not an observed main-run backlog measurement. |
| Invalid worker reuse | A wrong-epoch result was FAULTED but the same worker returned to the pool: returned={str(invalid['invalid_worker_returned_to_pool']).lower()}, destroyed={str(invalid['worker_destroyed']).lower()}. |
| Blocking write | A real worker acknowledged READY then stopped reading. A 1 MiB request with {blocked['service_timeout_s']} second service timeout did not return before the external two-second watchdog; the owned helper/child process tree was terminated. |

These observations confirm the specific reviewed paths rather than inferring
their occurrence from source inspection. They do not establish that those paths
were exercised in the archived main campaign.

## Implemented changes and locally tested behavior

`csc/executor.py` replaces the unbounded private executor with a fixed-worker FIFO.
Its physical running-plus-queued count is at most `max_pending_shadow_tasks`.
Cancelling a queued Future does not release its physical permit: the item must
actually be dequeued or removed during shutdown. Submission rejects immediately
when full, and coordinator admission checks physical capacity in addition to the
ledger cap. Mirror-first priority remains unchanged. New resource fields expose
physical queue, inflight, running and available-capacity counts. These fields were
not present in the measured main archive.

The physical regression blocks one worker, fills all 12 permits, cancels the 11
queued Futures, and tries 1,000 resubmissions. Every extra submission is rejected,
queue depth remains 11 and inflight remains 12. Releasing the worker drains the
cancelled items and restores admission.

Warm process leases now remain exclusive until response body/schema, branch
identity, provenance, anchor/window, finite metrics/trace, final-state validity,
input hash/sequence and virtual-actuation bounds have been checked. Corrupt output
throws inside the lease guard and destroys the process before reuse. Tests inject
wrong identity, wrong provenance, NaN metrics, wrong input hash and wrong schema;
each original process is destroyed and a replacement completes the next request.
The coordinator independently retains its comparison identity checks.

Warm transport uses one bounded writer queue/helper and an absolute deadline
shared by request write/flush and response collection. A real READY-but-not-reading
worker times out on a 1 MiB write, is killed, and both helpers settle. Shutdown
marks the pool closing, removes queued work and kills registered transports before
joining dispatch workers; the regression closes a blocked writer before its
five-second service timeout and verifies termination.

The parent reader explicitly deletes consumed frame/output locals after enqueue.
A live-thread frame check confirms no previous `line` or `value` local remains
while waiting for another response. Assignment wire size is checked before
physical queue submission; a deliberately oversized request becomes an explicit
fault without entering that queue.

## Retained byte inventory and scope

| Location | Bound and semantics |
|---|---|
| Physical scheduler work items | At most configured task capacity, each with assignment wire size at most `max_result_bytes`; Python object overhead is additional and not a fixed RSS proof. |
| Warm writer pending queue | At most one framed request, body at most `max_result_bytes` plus newline. |
| Warm writer active frame | One bounded request; helper releases body/view references after completion. Caller serialization can temporarily coexist with the framed copy. |
| Warm response reader | Reads at most `max_result_bytes` plus one sentinel byte before decoding; frame and decoded object can temporarily coexist. |
| Warm response queue | At most one decoded result/error; after enqueue the reader releases its preceding frame/result locals. |
| Assigned model state and result | Domain horizon/schema bounds plus wire bound; leases and hot result retention remain finite. These do not prove hostile-input or process RSS isolation. |
| Archived research evidence | Still append-only and grows with execution; no total disk quota was added. |

## Review disposition and limitations

R2 transport, R3 physical queue and R4 invalid reuse have implementation corrections
and targeted local regressions in this **new variant**. The test evidence supports
those specific corrected paths; it does not close performance/generalization
concerns in the measured earlier variant. Parent-reader retention R13 is likewise
corrected and locally checked.

Readiness has its separate five-second bound; process waits, helper joins and
executor joins have explicit limits. These are cooperative local operation bounds,
not an absolute OS scheduling or hard real-time guarantee. Token availability
depends on the fixed-slot lease invariant. OS process creation, termination and
underlying host failure remain outside an adversarial isolation claim. Cold and
HTTP transport retain their documented post-capture/body limitations.

Storage availability R1, long-run memory R5, cadence R6 and pressure-dependent
yield R7 remain open. No production/evidence persistence failover, resource quota,
policy learning or trust redesign was added. Positive measured memory slopes,
timing heterogeneity and failed delayed-evidence conditions remain negative or
inconclusive evidence. Trust stays Decision D; learning stays BLOCKED.

## Next actions

Use a separately preregistered Cycle 6 study to measure the hardened physical
queue and transport behavior, archive quotas, production/evidence storage failure
contracts, longer memory trends and workload-qualified cadence/yield operating
regions. Do not use passing regressions as a substitute for those measurements.
"""
    (root / "research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening.md").write_text(report, encoding="utf-8")
    print(json.dumps({"status": summary["status"], "tests": summary["gate_tests"],
                      "seconds": summary["gate_seconds"], "csc_source_identity_sha256": summary["csc_source_identity_sha256"],
                      "broken_hashes": broken, "source_changes_after_gate": changed}))


if __name__ == "__main__":
    main()
