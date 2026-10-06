# Cycle 5 final reviewed correctness hardening

**Status:** Implemented and locally tested after the immutable main study. The v5
source-bound gate passed **108 tests in 28.362 seconds**.
No performance, memory, storage or evidence-yield experiment was rerun.

## Evidence and method

The v4 independent review identified three bounded MODERATE paths: consumed timing
values could break reduction, cleanup-failed artifacts could enter complete-run
analysis, and checked workspace source could change before its execution copy.
The immutable correction is `results/cycle5-validation/post-review-hardening-20261006-v5`. Full closure identity:
`c3e81bb6c4148f9b899970b5e71fe8a8b77226ba862ff3b7d1fd0f767cdda4be`; CSC identity:
`ee51a6bf9f72a003844e73566ba3840b228074fe7432a3c17e5799f070039fb5`. Artifact failures: `[]`;
runtime/test/campaign changes after the gate: `[]`.

Negative controls against archived v4 show: accepted hydration values produced a
nonfinite median and returned the worker; cold string startup timing was accepted;
cleanup-failed execution was absent from failure accounting; and an altered copied
pressure helper was accepted. These are mechanism probes, not main-run frequencies.

## Corrections

All required worker timings and optional startup timing, when present, now use a
finite arithmetic envelope with ordering checks. Cold and warm paths share it;
warm reset metadata remains conditional. Extreme hydration and malformed cold
startup values are rejected before publication or lease return.

Analysis reads `execution_status.json`. A control/cleanup-failed run preserves its
artifact status and production observations but is classified
`FAILED_CONTROL_OR_CLEANUP`, excluded from completed groups/effects, and retained
in the failure table.

Preparation rehashes every required copied source against the accepted gate before
collection can start. A deterministic copy-race regression corrupts the copied
pressure helper and requires preparation to fail. Explicit current-compatible
gate, protocol and unique-directory requirements remain.

## Limits

This closes named local cooperative mechanisms only. It does not prove exhaustive
schedules, OS cleanup, hostile containment, resource isolation, memory boundedness,
storage durability or corrected-source performance. The measured source retains
R1 storage, R5 memory, R6 cadence and R7 delayed-yield findings. Trust remains D;
learning remains BLOCKED. Any Cycle 6 collection requires a separate preregistration.
