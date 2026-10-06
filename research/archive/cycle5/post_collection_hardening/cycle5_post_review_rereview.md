**Artifact:** `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview.md`  
**Status:** Independent static re-review of the supplied packet, 2026-10-06. Returned as artifact text; no tools, edits, experiments, or delegation performed. AFTER changes are implemented and locally tested, not deployment-validated. **Remaining MAJOR implementation defects prevent broad closure. No CRITICAL authority breach is established. Trust remains D; learning remains BLOCKED.**

**Question:** Do the post-review changes close R2, R3, R4, R9, and R13 for the declared Windows first-party implementation, and what still requires correction?

**Evidence:** Supplied implementation and regression sources; `research/evidence/cycle5/cycle5_red_team_review.md`; `research/archive/cycle5/post_collection_hardening/cycle5_post_review_campaign_hardening.md`; and `results/cycle5-validation/post-review-hardening-20261006-v1/{manifest.json,unittest.log}`.

The supplied manifest identifies the AFTER validation source closure as:

`12f8d30d9bc2628cb89b5ef918d4628552d5302fb8eb77de64443c34dfc67b77`

It reports no source changes during the gate. The log reports **80 tests passing in 30.089 seconds**; manifest gate elapsed time is separately 30.9605 seconds. Neither hashes nor execution were independently reproduced here.

The BEFORE probes report physical queue depth **1,000 against configured capacity 12**, an invalid worker returned reusable without destruction, and a blocked request write exceeding its **0.1-second service timeout until an external two-second watchdog**. These are meaningful negative controls for the tested mechanisms, not observations from the 86-run performance campaign.

The main archive and original review remain unchanged. Their original CSC source identity and the new validation closure identity have different scopes; neither substitutes for the other.

**Method:** Adversarial static tracing of ownership, validation, cancellation, process creation, shutdown, and exception paths. Passing tests support only their exercised conditions. Source-established defects below are distinguished from reported executions.

**Per-finding dispositions**

| Finding | AFTER disposition | Supported conclusion |
|---|---|---|
| R1 — storage | **MAJOR / OPEN** | Persistence can still abort production; partial finalization remains nontransactional. |
| R2 — transport/shutdown | **MAJOR / OPEN; tested path mitigated** | Blocked warm writes now time out and registered transports are killed before joining. Creation races and cleanup failures remain. |
| R3 — physical backlog | **Narrow closure supported** | The owned executor bounds running-plus-queued items, including cancelled items awaiting dequeue. Comprehensive retained-byte boundedness remains unestablished. |
| R4 — validation/reuse | **MAJOR / OPEN; substantial mitigation** | Tested corruptions are rejected under an exclusive lease. Cleanup exceptions and validation after release still defeat broad quarantine closure. |
| R5 — memory | **MAJOR / OPEN** | Positive trends, offline allocations, and whole-file hashing remain unresolved. |
| R6 — cadence | **MAJOR / OPEN** | No new performance evidence or cadence contract. |
| R7 — yield | **MAJOR / OPEN** | No new joint cadence/capacity/requested-set yield evidence. |
| R8 — host-time confounding | **MODERATE / OPEN** | Unchanged. |
| R9 — campaign/pressure | **MODERATE / OPEN; cleanup mitigated** | Readiness cleanup and watchdog control improve. Campaign continuation after uncertain cleanup remains possible; pressure claims remain narrow. |
| R10 — measurement semantics | **MODERATE / OPEN** | Unchanged. |
| R11 — deadline/verification | **MODERATE / MITIGATED** | Preserve original qualified disposition. |
| R12 — semantic supplements | **MODERATE / MITIGATED** | Preserve original qualified disposition. |
| R13 — retained reuse state | **MODERATE / MITIGATED; reader-local subfinding narrowly closed** | Successful-response reader locals are cleared. Broader retained-state/reset coverage remains limited. |
| R14 — `Counters` retention | **MINOR / narrow closure retained** | GC-zero results address only the specific class-survival hypothesis. |
| R15 — duration/specification | **MODERATE / OPEN** | No longevity, infinite-duration, specification, or deployment upgrade. |

**R2 — what improved and what still fails**

`WarmProcess.evaluate()` now shares a deadline between writer completion and response receipt. Its real-process unread-pipe regression is meaningful: a child acknowledges readiness, never reads, receives a large assignment, and is killed following timeout. The manager shutdown regression also demonstrates killing an already-registered transport before waiting for its executor task.

This does not establish a complete assignment or shutdown deadline. Serialization precedes the transport clock; replacement readiness, validation, and cleanup have separate costs. The test’s two-second assertion is not proof of an exact 150 ms end-to-end bound.

Concrete remaining defects in `csc/branches.py` and `csc/warm.py`:

- **Cold creation can escape the shutdown snapshot.** An executor item can be dequeued before cancellation, then enter the cold path after `close()` snapshots `cold_processes`. That path neither checks `closing` nor checks it when registering the new process. The shutdown kill sweep misses it.
- **Warm creation is not fully owned during construction.** `_new_worker()` correctly checks closure before construction and again before registration. However, the child and I/O threads are created inside `WarmProcess.__init__()` before its readiness `try`. A failure after spawning but before entering that `try`, such as thread-start failure, lacks explicit process cleanup. Construction in progress is also absent from the manager’s shutdown snapshot.
- **Cleanup stops at the first exception.** An exception from one `worker.abort()` prevents subsequent workers from being attempted. Executor shutdown timeout skips the later `_discard_worker()` sweep. The cold exception path retains an unbounded second `communicate()` and removes the process from tracking even if termination fails.

`available_workers.get()` still has no timeout or closure wakeup. Normal slot/token accounting does not itself establish a reachable empty-token deadlock, so this review does not assert one merely from that call. Nevertheless, shutdown and lease acquisition should have an explicit shared state contract.

**Required correction:** Make creation, registration, and closure ownership consistent; explicitly clean partially constructed workers; attempt cleanup of every owned process despite individual failures; preserve unresolved handles and report incomplete cleanup. Bound cleanup attempts without claiming that software can force an OS operation to succeed.

**R3 — narrow closure is justified**

In `csc/executor.py`, submission checks and increments `inflight` under the same condition lock used for dequeue and shutdown. Cancellation alone does not release capacity. A dequeued item retains its permit through completion or cancellation recognition; queued shutdown cancellation removes the item before releasing its permit.

This addresses the original cancelled-but-not-dequeued accumulation mechanism. The regression holds one actual executor thread busy, cancels the remaining submissions, rejects 1,000 replacement submissions, and verifies eventual capacity recovery. Its evidence is substantially stronger than the earlier `DeferredManager` fixture.

The count bound also survives the ordinary cancel/dequeue race structurally: the item either remains queued or is owned by a consumer; neither path frees capacity merely because `Future.cancel()` succeeds.

`BranchManager.launch()` additionally rejects oversized serialized assignments before submission. This supports a bounded submitted-assignment inventory, but it is not measured aggregate Python memory or a complete byte-budget implementation. Serialization occurs before rejection, dispatch metadata is added afterward, and transport buffers, decoded objects, results, and exception state have additional costs.

**Disposition:** Close the specific physical executor count defect for AFTER. Retain byte accounting and R5 separately. Add concurrent cancellation/dequeue/shutdown coverage without pretending the current single-worker test exercised every interleaving.

**R4 — two source defects prevent closure**

The new lease-held validator is a substantial improvement. The five corruption cases use real worker processes and verify destruction and replacement, although `evaluate()` itself is patched. They establish manager disposition for those injected results.

Two remaining mechanisms invalidate the broader assertion that integrity failure always destroys the emitter before reuse:

1. **Cleanup failure republishes the suspect worker.** In `_execute()`, the exception handler calls `_discard_worker(worker)` before assigning `worker = None`. If `worker.close()` raises, that assignment is skipped. The `finally` block then puts the same worker back into `available_workers` whenever the manager is not closing. This includes termination permission errors and cleanup timeouts. It can therefore republish an invalid live worker, or a dead worker whose cleanup failed.

   Quarantine must be irrevocable independently of cleanup success. Remove the lease from reusable circulation first; track unsuccessful destruction separately.

2. **The lease ends before all rejection-producing work finishes.** `validate_worker_result()` checks that `runtime` is a dictionary, but not that `execution_ms` is numeric. A result containing a string there passes this check, is released, then faults during transport-overhead subtraction. The worker is retained despite emitting a malformed result.

   There is also a concrete coordinator-only validation gap: a mirror trace with both queue coordinates near `1.7e308`, otherwise valid fields, and an ordinary valid final state passes the finite-component checks. Against ordinary production coordinates, its two-dimensional divergence overflows to infinity. `PendingShadowLedger.valid_identity()` rejects it after the worker has been released. No quarantine feedback exists.

   Runtime enrichment can likewise move a response across the coordinator’s body-size threshold after lease-held validation.

**Required correction:** Validate every result field consumed afterward, define size limits consistently around enrichment, and resolve the integrity-check mismatch between manager and coordinator before permitting reuse. If coordinator context is necessary, retain quarantine through that decision or establish an equivalent safe check before release. Deadline expiry alone should remain distinct from emitter corruption.

**R9 — cleanup improvements do not fully enforce campaign abort**

Moving readiness inside `run_one()`’s `try/finally` fixes the original readiness-cleanup omission. Bounded waits, escalation, and an outer watchdog improve failure control. The eight mocked tests demonstrate those control-flow branches; they do not prove Windows descendant termination.

A remaining source-level gap contradicts the broad “unconfirmed reaping prevents another condition” claim:

`stop_pressure()` propagates failure into the run subprocess, but `execute()` does not distinguish uncertain cleanup from an ordinary nonzero run exit. For a pressure run, its fallback may continue when `final.json` exists. That file is an application acknowledgment, not proof that the process was reaped. For a nonpressure run, a nonzero exit has no corresponding cleanup-confirmation gate. Forced tree cleanup is invoked on watchdog expiry, not every exit with uncertain ownership.

Termination permission errors can also interrupt escalation or direct-child reaping. Reporting failure is appropriate; it must be accompanied by attempts to clean other owned resources and an explicit campaign-stop decision, without attempting to bypass permissions.

**Required correction:** Propagate cleanup certainty separately from run success. Abort on unresolved ownership regardless of marker files. Add an integrated launcher test demonstrating that uncertain cleanup prevents the next condition, plus a disposable real Windows process-tree test. Preserve the limitation that OS termination failure cannot be converted into proof of cleanup.

The original pressure-intensity, sustained-liveness, exhaustion, and isolation questions remain open.

**R13 — reader-local closure is appropriately narrow**

`WarmProcess._read()` deletes `line` and `value` after successful enqueue, before its next blocking read. The regression inspects the actual reader frame after consumption and checks that the response queue is empty. Together these support closure of the specific successful-response idle-local retention defect.

They do not establish that every prior-task object disappears across fault paths, queued responses, exception tracebacks, incomplete cleanup, or other holders. Nor do they validate arbitrary module globals, stochastic adapters, or future caches. R4 remains relevant to reuse integrity; R5 remains relevant to retained bytes.

**Authority and permission boundary**

The supplied changes introduce no demonstrated production actuator capability into shadow requests. `execute_shadow()` still rejects production identity, and shadow output remains estimated. Validation gaps affect evidence integrity and lifecycle containment; this packet does not establish unauthorized authoritative mutation.

Minimal environments and temporary working directories do not remove the subprocess’s inherited OS-account permissions. Scope remains cooperative first-party Windows execution, not hostile-code containment. Cleanup permission failures require quarantine and explicit incomplete-cleanup reporting, not stronger isolation claims.

**Remaining must-fix decision and next actions**

No new CRITICAL finding is established. **R2 and R4 remain MAJOR implementation blockers**, alongside the unchanged R1 storage failure contract. R5, R6, and R7 remain MAJOR unresolved claims requiring measurements and operational criteria, not closure through correctness tests.

Before another campaign:

1. Correct cleanup-exception quarantine, validation after lease release, process-creation/shutdown ownership, and cleanup that stops at the first error.
2. Gate malformed runtime fields, mirror divergence overflow, result-size enrichment, failed destruction, failed replacement construction, concurrent dequeue/close, and partial-constructor cleanup.
3. Make uncertain cleanup stop the whole campaign; verify that behavior across the actual launcher boundary.
4. Resolve R1 with independent production-progress accounting and partial/persistent storage-failure tests.
5. Freeze a fresh source/gate/protocol identity before collecting performance evidence. Preserve the old review, source, negative controls, failed attempts, and all existing result directories.

**Limits:** This is independent reasoning over supplied excerpts and reported results. The complete 80-test suite and all dependencies were not supplied. No new measurements or hash verification were performed. The unchanged 86-run archive supports only its original finite conclusions. **No performance, memory-plateau, infinite-bound, resource-isolation, or deployment claim is upgraded.**