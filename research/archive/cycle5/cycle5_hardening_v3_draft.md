# Draft v3 correction plan — no frozen source changes

**Status:** Proposed only. The 96-test v2 source and every measured main/archive
remain unchanged. This note prepares concrete corrections while independent
review completes; it is not correctness or performance evidence.

## Runtime numeric contract

The v2 validator checks `execution_ms`, but `runtime.cpu_ms` can remain a string
and cause the synchronous runner's later CPU sum to fail. The correction should
declare every runtime field subsequently consumed, rather than claim that checking
one timing field validates the whole runtime object.

Required `execution_ms`, `hydrate_ms` and `cpu_ms`: numbers with exact type int or
float (exclude bool), finite, nonnegative. Required `inputs_consumed`: integer in
the assigned horizon; REPORTED output must consume that entire horizon. Required
`pid`: positive integer. Optional worker startup/dispatch/transport timings and
process CPU: finite nonnegative numbers when present; only documented unavailable
OS measurements permit null. Optional RSS/handle/task/metadata counters: exact
integers with nonnegative counters and the supported metadata version. Monotonic
timestamps need a separate schema, not an indiscriminate 'all numbers positive'
check. Parent-generated diagnostics must be validated after enrichment too.

The final verdict should determine any additional coordinator/domain integrity
mismatch (notably finite scalar values whose differences or aggregates overflow).
A proposed correction must reject overflow at the operation that can reject the
outcome before releasing its emitter. Finite individual `cpu_ms` values alone do
not prove that downstream aggregate CPU sums stay finite; extreme-value regressions
must make that boundary explicit. Domain queue/cost/throughput metrics should be
nonnegative if that is their authored contract. No numerical threshold should
be invented merely to make this gate pass or alter measured evidence deadlines.

## Lease acquisition and closure

The v2 warm path calls `available_workers.get()` without a timeout. A dispatch
already dequeued when shutdown begins can wait after another task suppresses its
token return because `closing` is set. Executor cancellation cannot remove an
already-dequeued waiter. Killing registered children does not wake that queue wait.

The minimal correction uses one manager lease condition/state boundary:

1. Acquisition checks `closing` before waiting, then waits for an available token
   **or closure** with an explicit finite acquisition deadline.
2. Claim and the final closing check occur under that same condition.
3. Return occurs under the condition and only while open; returns notify waiters.
4. Shutdown sets closure and notifies all waiters before queue cancellation,
   process termination and executor joins. A waiter awakened by closure fails
   explicitly; it cannot create a replacement or regain a reusable process.
5. An acquired None replacement token still obeys the existing construction
   reservation, child-registration callback and post-create closure check.

This is a bounded cooperative synchronization contract, not an OS real-time
deadline. A timed queue-poll alternative is smaller but needs an explicit maximum
closure wake delay and the same before/after closing checks.

## Meaningful regressions

- Inject CPU strings, bool, NaN, infinity, negative values and malformed optional
  runtime fields into a real worker's response; require rejection, irrevocable
  quarantine and no synchronous aggregation failure afterward.
- Test null only for declared unavailable OS fields and preserve valid ordinary
  cold/warm equivalence.
- Exercise extreme finite CPU/utility/distance values at their downstream
  arithmetic operations rather than assume scalar finiteness is sufficient.
- Remove the sole warm token, start a real executor dispatch waiting for it, then
  close the manager; closure must wake the task and settle executor ownership.
- Keep the manager open with no token and assert a finite acquisition timeout,
  explicit failure and no untracked replacement creation.
- Race token return, acquisition and close, checking every accepted task settles
  and no token is published after closure.
- Pause replacement construction across closure, including partial helper-start
  failure; preserve the existing real-child reaping and unresolved-ownership tests.

## Evidence and next action

Do not edit the v2 archive or claim the draft is implemented. If authorized after
the verdict, snapshot v2 before any edit, apply the smallest identified corrections,
run targeted regressions then the full suite in a new unique v3 directory, archive
the executed closure and hashes, and request independent closure judgment. Main
cadence, memory and yield results remain those of the original measured variant.
