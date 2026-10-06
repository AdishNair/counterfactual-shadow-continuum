# Cycle 4 asynchronous lifecycle, restart and artifact audit

**Status:** Implemented and locally tested, 2026-10-05; performance evidence is
reported separately in `research/evidence/cycle4/cycle4_async_analysis.md`.

**Question:** Can late, malformed, failed or duplicate shadow work change
authoritative state, bind to another epoch, resurrect expired evidence or race
artifact writes?

**Evidence/method:** `csc/pending.py`, `csc/async_runner.py`, `csc/store.py`,
`tests/test_async.py`, deterministic `experiments/cycle4_async_invariants.py`.
Machine summary: `research/tables/cycle4_async_transition_tests.json`.
14 tests pass, all 64 state pairs are checked, two deliberately weakened guards
are detected by negative tests. Original full regression suite passed 32 tests
before the five added async cases; final suite verification is recorded later.

**Final validation addendum:** The earlier machine transition snapshot above is
preserved. After the additional malformed-output and numeric-overflow guards,
the current full suite passed 54 tests, including 16 async tests, in 29.807 s.
The independent reviewer reran the numeric-overflow regression successfully.
`research/tables/cycle4_local_validation.json` records that final result and the
earlier inconclusive localhost HTTP failure during concurrent archive verification.
These later checks apply to the current tree, not the immutable measured source.

| State | Legal next state | Meaning |
|---|---|---|
| QUEUED | RUNNING, COMPLETED, FAILED, TIMED_OUT, EXPIRED, REJECTED | Admitted whole batch; coordinator may observe completion before observing running |
| RUNNING | COMPLETED, FAILED, TIMED_OUT, EXPIRED, REJECTED | Future started; transport timeout bounds local cooperative execution |
| COMPLETED | COMPLETED produces DUPLICATE audit | Idempotent; original comparison remains immutable |
| EXPIRED / DROPPED / FAILED / TIMED_OUT / REJECTED | No transition to valid evidence | Verified later arrivals create LATE audit only |
| DROPPED | Initial terminal admission outcome | Whole batch skipped on capacity exhaustion |
| DUPLICATE / LATE | Audit-only events | Never comparator inputs or actuation permissions |

Fault envelopes use existing wire statuses FAULTED/TIMEOUT; ledger states are
FAILED/TIMED_OUT. REJECTED is terminal for malformed or identity-mismatched output.
Identity comprises experiment, epoch, branch, role, action, anchor, sequence
window and input hash. Site J1 is bound through the validated immutable anchor
and J1-specific branch plan; site is explicit in the journal/comparison.
Duplicate epoch commits are rejected before a second journal entry or submission.

**Findings:** Production N+1 opens with unresolved N futures in a deterministic
integration test. Out-of-order results finalize in epoch order, preserving the
epsilon EWMA order. Every epoch journals production before shadow admission.
Incomplete alternatives suppress all regret fields. Running expired futures
retain task permits until actual settlement, so expiry cannot create an unbounded
backlog. Queue-full affects evidence availability. No ledger reference to the
world, gateway, issuer or capability exists. Only a done future has `result()`
called. Worker crash, timeout, service exception and malformed numeric output
become terminal evidence outcomes.

Poll costs are bounded by configured active-task and pending-epoch limits;
comparison/serialization remains synchronous coordinator bookkeeping and is
measured separately. It can affect cadence through storage or resource cost.
Logical absence of a shadow wait is not an absolute latency guarantee.

**Restart/shutdown:** Clean shutdown drains evidence for at most the configured
result deadline, expires unresolved evidence, cancels queued work, then joins
remaining finite-timeout transport threads after the production loop. In-flight
epochs become explicit incomplete final records. This is bounded cooperative
shutdown, not a hard OS scheduling guarantee. Queued work is discarded; no durable
queue recovery or re-dispatch is implemented. Restart uses a new immutable run
directory and experiment identity. Existing result-store paths reject reopening
for writes; read-only reopen remains possible. Old outputs fail the new identity
join. Stateless worker restart is equivalent to reexecuting its serialized request;
duplicates still cannot replace original evidence.

**Storage:** The store enforces coordinator thread ownership for append and atomic
JSON replacement. Eight concurrent writer attempts are rejected; sequential writes
produce exactly eight parseable records. Workers return data only and have no
store handle. Summaries and hashes are generated after shutdown settles workers.
JSONL writes are flushed but not `fsync` durable transactions: a sudden process or
power failure can leave a partial last line. Run manifests remain RUNNING/FAILED;
only terminal COMPLETE runs enter the timing analysis. Existing replay verifies
each final async CFR against one matching journal commit and checks source and
artifact hashes. This does not implement distributed exactly-once persistence.

**K readiness:** Admission and completion iterate the planned branch set; accounting
is parameterized by set size and K excludes mirrors. The traffic domain has only
three actions, hence at most two distinct alternatives. K>2 is rejected rather
than inventing duplicate alternatives; a larger domain action enumerator would
be required for meaningful larger-K evaluation.

**Limitations/open questions/next actions:** No hostile workers, durable restart,
coordinator kill during file replacement, real-time deadlines or resource isolation
are established. Current tests characterize new-run restart and safe stale-delivery
rejection. A longer resource-controlled lifecycle study should test interruption
and recovery before claiming a persistent service. The registered local timing
and resource microstudy is complete; see `research/evidence/cycle4/cycle4_async_analysis.md`.
The next systems study should address continuous evidence yield and retained
history, keeping systems and trust conclusions independent.
