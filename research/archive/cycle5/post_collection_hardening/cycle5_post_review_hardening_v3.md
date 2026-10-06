# Cycle 5 third post-review hardening

**Status:** Implemented and locally tested after the immutable main measurements.
The source-bound v3 gate passed **103 tests in 39.450 seconds**.
This is correctness evidence only; no cadence, yield, memory or storage experiment
was rerun.

## Question, evidence and method

The second independent re-review identified two remaining MAJOR runtime paths:
a dequeued warm task could wait forever for a lease token during closure, and
unresolved cold processes did not consume later creation capacity. It also found
incomplete runtime/derived-numeric validation and three qualified campaign cleanup
paths. The correction is archived at `results/cycle5-validation/post-review-hardening-20261006-v3`.

The gate copied the complete CSC, tests and experiments Python closure, ran the
full suite, and hashed every source and artifact. Full closure identity:
`beceb6ad110922758e01377090d296571307cbcfa4ea812288d7799609d930de`; CSC identity:
`af623503412d5fed8137ae751d9428af964e912e795eaed12b7e10dcd1cf24d3`. Broken artifact hashes:
`[]`. Runtime/test/campaign source changes after the gate: `[]`.
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
