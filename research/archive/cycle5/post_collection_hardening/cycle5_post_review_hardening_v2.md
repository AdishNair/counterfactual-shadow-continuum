# Cycle 5 second post-review hardening

**Status:** Implemented and locally tested after main measurement. The new full
gate passed 96 tests in 28.181 seconds.
The 80-test source archive, first independent re-review and all main results are
preserved. No main performance study was rerun or reinterpreted as the new source.

## Question, evidence and method

The first independent re-review retained R2/R4 as MAJOR because destruction errors
could republish suspect workers, rejection-producing enrichment occurred after
lease release, and child creation/cleanup had ownership gaps. The question is
whether those named paths can be corrected and regression-tested while preserving
negative measurement evidence, production authority, trust D and blocked learning.

Raw immutable evidence is `results/cycle5-validation/post-review-hardening-20261006-v2/`: BEFORE source is the
80-test post-review variant; AFTER includes all CSC, test and experiment Python
files executed by this gate. Manifests preserve config hash, seed, factors,
environment, script identity, source and artifact hashes. There are zero broken
artifact hashes and zero CSC/test source changes after the gate. Unrelated offline
experiment scripts changed afterward: `['experiments/cycle5_delivery_audit.py']`. The immutable gate manifest
reports no source changes during execution. Full archived closure identity:
`b4d08f39e99aa5a26bcba89e4d7d4e41a1a76c3f007aaba41bc03efc60334b41`; CSC-only identity:
`1c7544c0bbfee91e99adcfb8a8e595c14c4781dd7d6a5f8b0c9e85d1279e718e`.

`experiments/cycle5_hardening_rereview_analysis.py` deterministically verifies and
generates this artifact and `research/tables/cycle5_post_review_hardening_v2.json`.

## Preserved BEFORE negative findings

| Before-80-gate source probe | Outcome | Worker republished | Additional observation |
|---|---|---|---|
| cleanup | FAULTED | True | Synthetic cleanup denied |
| runtime | FAULTED | True | String execution timing |
| mirror | REPORTED | True | Mirror norm overflowed to infinity |
| enrichment | REPORTED | True | Body limit crossed by enrichment |

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
