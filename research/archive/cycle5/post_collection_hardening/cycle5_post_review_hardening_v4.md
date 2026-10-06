# Cycle 5 final post-review hardening

**Status:** Implemented and locally tested after the immutable Cycle 5 measurements.
The final source-bound gate passed **106 tests in 28.399 seconds**.
No performance, memory, storage or evidence-yield run was repeated.

## Question, evidence and method

The v3 independent re-review narrowly closed the two R2 lifecycle mechanisms and
the utility-difference counterexample, while identifying bounded gaps in CPU
aggregation, cold-response validation, final-condition cleanup disposition,
Windows exit inspection and readiness-gate compatibility. The immutable final
gate is `results/cycle5-validation/post-review-hardening-20261006-v4`. Full closure identity:
`f492d4de5e959702358740ecb1d73f580e674d63234ae3a363dabd2e4f0b25fb`; CSC identity:
`ce965b67e6f1361dfabc34be33b3abab56a5e6b1d95fe8aaeb5c5eeaf360d566`. Artifact hash failures: `[]`;
runtime/test/campaign changes after the gate: `[]`.

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
