# CSC Cycle 5: post-measurement v2 systems re-review

**Artifact:** `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v2.md`

**Status:** Independent static review of the supplied evidence, 2026-10-06. Returned as artifact text; no tools, delegation, edits, experiments, hash verification, or independent test execution performed. The v2 corrections are **implemented and locally tested**, not deployment-validated. Several previously identified mechanisms have narrow closure, but **remaining MAJOR implementation paths prevent general R2/R4 closure and an unconditional recommendation to begin a fresh performance campaign**. No CRITICAL authority breach is established. **Trust remains D; learning remains BLOCKED.**

**Question:** Does the final v2 correction resolve the specific ownership, shutdown, quarantine, validation, cancellation, launcher-abort, and reader-local mechanisms left by the first re-review?

**Evidence and source identity**

| Evidence | Supplied identity and scope |
|---|---|
| Final v2 full gate | `results/cycle5-validation/post-review-hardening-20261006-v2/{manifest.json,unittest.log}`. Source identity: `b4d08f39e99aa5a26bcba89e4d7d4e41a1a76c3f007aaba41bc03efc60334b41`. |
| Final v2 reported execution | **96 tests passing in 28.181 seconds**; exit code 0. Manifest elapsed time is separately **28.66800800000783 seconds**. The manifest reports `source_changed_during_gate: []`. |
| Prior full-gate variant | `results/cycle5-validation/post-review-hardening-20261006-v1/`. Prior re-review identifies source closure `12f8d30d9bc2628cb89b5ef918d4628552d5302fb8eb77de64443c34dfc67b77`, with **80 tests passing in 30.089 seconds**. This is not the final v2 identity. |
| Campaign-cleanup v2 targeted gate | `results/cycle5-post-review/campaign-cleanup-v2-20261006T144939Z/manifest.json`. Identity: `89851bd76c936986dba6b8c59f98042ae80b4c4f43319c170e7ad81873ffbc1f`; 13 tests reported passing, approximately 2.838 seconds. Its manifest contains earlier `csc/branches.py` and `csc/warm.py` hashes, so it is not the final integrated source closure. |
| Review baseline | `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview.md` and the supplied second-correction account in `research/archive/cycle5/post_collection_hardening/cycle5_post_review_campaign_hardening.md`. |
| Performance study | The immutable 86-run archive remains evidence for its original measured source only. Its exact aggregate source identity is not supplied here and is not inferred from any hardening gate. **No new performance measurements were collected.** |

The final manifest identifies `csc/branches.py` as `7043c796c749782f0ec1d8c08afcf54241e2c52b19117523ca50a6fae2c5b35c` and `csc/warm.py` as `fa6b1ca564bed1d568ac2d0c0ced762a00bb0290e2a2b6a4bd3cf77025f25929`. These distinguish the reviewed correction from the earlier runtime files in the targeted campaign gate.

The v2 `negative_validation.json` preserves prior-code failures: cleanup and malformed-runtime probes faulted while returning the worker; the mirror probe returned a reported result with nonfinite mirror norm; the enrichment probe also returned a reported result and reusable worker. These are supplied negative controls, not failures observed on the final v2 code or measurements from the main campaign. The compact enrichment output alone does not expose the relevant serialized sizes.

**Method:** Trace the supplied source through successful execution, injected corruption, partial construction, concurrent shutdown, failed termination, and launcher failure. Separate source-established paths from reported regression executions. Assess closure at the mechanism level. No unseen tests, dependencies, production-world implementation details, or execution outcomes are assumed.

**Findings and dispositions**

| Finding | Final v2 disposition |
|---|---|
| R2 — transport, creation, shutdown | **MAJOR / OPEN overall.** Ownership registration, partial-constructor cleanup, bounded cold cleanup attempts, and attempts across owned processes substantially improve. A concrete warm lease/shutdown race and continued cold spawning after unresolved cleanup remain. |
| R3 — cancelled physical backlog | **Specific count defect narrowly closed.** Cancellation does not release physical capacity before dequeue/removal. Byte and memory bounds remain unestablished. |
| R4 — validation and reuse | **MAJOR / OPEN overall.** Cleanup-failure republication, malformed `execution_ms`, the supplied mirror-coordinate overflow, and enrichment-size release defects are narrowly corrected. Runtime schema and derived arithmetic remain incomplete. |
| R9 — campaign cleanup | **Continuation-after-uncertain-cleanup mechanism narrowly closed for the exercised launcher paths.** Exceptional launcher cleanup and confirmation-record handling retain gaps. Pressure, isolation, and universal descendant cleanup remain open. |
| R13 — reader locals | **Successful-response reader-local closure retained.** Broader retained-state/reset claims remain limited. |
| R1 — storage | **MAJOR / OPEN** for the unchanged measured study. |
| R5 — memory | **MAJOR / OPEN:** positive memory growth, offline allocation, and whole-file hashing are unchanged. |
| R6 — cadence | **MAJOR / OPEN:** no new cadence measurements or operational acceptance contract. |
| R7 — delayed evidence | **MAJOR / OPEN:** no new joint cadence, capacity, and requested-set evidence-yield measurements. |

R8, R10, R11, R12, R14, and R15 retain their previous qualified dispositions; this targeted review does not reassess or upgrade them.

**R2 — supported corrections**

In `csc/branches.py`, warm construction reserves capacity before spawning. The `on_spawn` callback registers the process before helper startup and readiness work. An in-progress constructor remains represented by `constructing_workers`; registration after closure triggers abort and cleanup. Unsuccessful destruction retains ownership instead of silently removing the worker.

In `csc/warm.py`, spawning, registration callbacks, helper startup, and readiness now occur within the constructor’s cleanup-protected region. The supplied partial-constructor regression launches a real child and injects thread-start failure. The replacement-constructor regression also checks that failed replacement does not escape ownership and that a subsequent assignment can succeed.

The cold path checks closure before spawning and after registration. A child returned after the initial shutdown snapshot is therefore registered and directed into cleanup. The supplied cold and warm paused-spawn tests exercise this race with real child processes. Default `close(wait=True)` also waits for executor settlement before taking another ownership snapshot.

Manager shutdown catches failures separately for each worker/process and continues its sweeps even after executor shutdown times out. This corrects the previous “first cleanup exception prevents all later cleanup” mechanism. Cold exception cleanup now uses `communicate(timeout=5)` and retains unresolved processes.

These are bounded attempts and explicit uncertainty handling. They do not make `Popen`, OS termination, filesystem cleanup, lock acquisition, or scheduling obey a universal wall-clock deadline. A cold `kill()` exception still skips that block’s subsequent `communicate()`; ownership is retained, but not every individual cleanup step is attempted.

**New defect R2-v2-A — MAJOR: shutdown can strand a dequeued warm task without a lease token.**

**Source:** `csc/branches.py`, `BranchManager.close()` and warm `_execute()`; `csc/executor.py`, `_consume()`.

**Concrete trigger:** One warm slot, an executing task A, and a queued task B:

1. The closer executes `self.closing.set()` and is descheduled before its first `pool.shutdown(...)`.
2. A finishes. Its `finally` sees closure and does not return a worker or replacement token.
3. The executor is still open, so its consumer dequeues B.
4. B enters the unconditional `available_workers.get()` with an empty queue.
5. The closer resumes, cancels remaining queued items, aborts owned transports, and attempts its bounded executor join.

B has already been dequeued and cannot be cancelled through the queue sweep. No shutdown path wakes its lease acquisition. The join times out and reports incomplete cleanup, but B and its executor thread remain stranded. Killing the process does not release a thread blocked on this queue.

This is a concrete interleaving, not an assertion that an ordinary empty queue necessarily deadlocks. The supplied shutdown tests do not explicitly force this token-withholding/dequeue schedule.

**Required correction:** Give lease acquisition an explicit closure-aware wakeup contract, and coordinate executor dequeue shutdown with withdrawal of lease tokens. Verify this exact interleaving.

**New defect R2-v2-B — MAJOR: unresolved cold processes do not constrain later cold creation.**

**Source:** `csc/branches.py`, cold `_execute()` and `admission_capacity()`.

**Concrete trigger:** A cold request times out, its process remains live, and `kill()` raises `PermissionError`. The process stays in `cold_processes`, but `_execute()` returns a terminal envelope and releases its executor permit. A subsequent assignment can spawn another process without checking unresolved cold ownership. Repeated failures can therefore accumulate live owned processes beyond the configured worker slots.

Retaining handles is an improvement, but it does not itself prevent additional exposure. The warm path has an unresolved-capacity guard; the cold path has no equivalent. The supplied failed-termination regression checks retained ownership for one attempt, not repeated admission.

**Required correction:** Stop further cold creation, or reserve capacity for unresolved processes, until ownership is resolved. This requires fail-closed admission, not a guarantee that the OS will honor termination.

**R4 — irrevocable quarantine and the specific v1 failures**

The previous cleanup-exception republication bug is corrected. Warm `_execute()` now saves `suspect`, clears `worker`, and only then attempts destruction. Cleanup failure leaves a quarantined owned worker and publishes a `None` replacement token rather than the suspect worker. `_new_worker()` counts unresolved owned workers against capacity.

`test_failed_destruction_never_republishes_corrupt_lease` supports this disposition: failed destruction does not return the corrupt worker or create another worker over the unresolved slot. Quarantine here means exclusion from reuse; it does not mean confirmed termination.

Both `validate_worker_result()` and `_enrich_result()` now execute while the warm lease remains exclusive. The exact prior failures are addressed:

- `execution_ms` must be an actual integer or float, finite, and nonnegative.
- The supplied `1.7e308` mirror-coordinate pair is rejected by the conservative norm check.
- Final serialized size is checked after runtime enrichment, before release.
- The post-release identity/provenance checks repeat conditions already checked under the lease.

For mirror coordinates, the envelope argument is valid under its stated premise: production coordinates are nonnegative and bounded by anchor queues plus the window’s arrivals. Under that premise, each absolute production-minus-mirror coordinate is bounded by the corresponding maximum used in the check. The supplied packet does not include `csc/world.py` source, so this review does not independently establish that premise for every future world implementation.

**New defect R4-v2-A — MODERATE: other consumed runtime numerics remain unvalidated.**

**Source:** `csc/branches.py`, `validate_worker_result()`; `experiments/cycle5_async.py`, `reduce_run()`.

**Concrete trigger:** An otherwise valid reported warm result contains numeric valid `execution_ms` but `runtime["cpu_ms"] = "bad"`.

The validator accepts it; enrichment does not consume or reject `cpu_ms`; the worker returns to circulation. The runtime can be recorded in lifecycle evidence. Later, `reduce_run()` executes:

```python
sum(r.get("cpu_ms", 0) for r in runtimes)
```

and raises `TypeError`. A finite negative CPU value also passes and can distort accounting.

Thus the specific execution-time subtraction defect is closed, but “all consumed runtime fields validated before release” is not supported. The supplied corruption tests cover string/negative `execution_ms`, not this field.

**Required correction:** Define and validate the runtime fields consumed by recording and reduction, including allowed absence, nullability, numeric types, finiteness, and domain restrictions.

**New defect R4-v2-B — MAJOR: finite individual utilities can overflow during comparison after release.**

**Source:** `csc/branches.py`, `validate_worker_result()`; `csc/pending.py`, `valid_identity()`; `csc/compare.py`, `OutcomeComparisonEngine.compare()` and `RegretCalculator.calculate()`.

**Concrete trigger:** A configuration accepted by `Config.validate()` has `queue_weight=1e306` and zero other utility weights. Production has `mean_queue=100`, giving finite utility approximately `-1e308`. An otherwise matching corrupt mirror reports `mean_queue=-100`, giving finite utility approximately `+1e308`, with ordinary finite trace coordinates and valid final state.

Negative metric values are not rejected. Both individual utility checks pass; the mirror-coordinate envelope passes; enrichment passes; the worker is released. Comparison then computes:

```python
epsilon = abs(mirror_utility - real_utility)
```

which overflows to infinity. An alternative with the same utility exposes the corresponding regret subtraction. Canonical persistence rejects the nonfinite derived result, providing a path from accepted worker corruption into coordinator failure.

This is a source-level arithmetic counterexample, not an observed measurement. It does not reopen the exact two-coordinate overflow regression; it demonstrates a remaining derived-numeric gap.

**Required correction:** Enforce metric domains and ensure downstream derived arithmetic cannot introduce nonfinite values. If an integrity decision requires production context, preserve the lease through that decision or establish an equivalent conservative pre-release bound. Deadline expiry should remain separate from emitter corruption.

**R3 — physical count closure remains supported**

In `csc/executor.py`, admission and `inflight` accounting share the condition lock. Calling `Future.cancel()` does not remove an item or free capacity. Dequeued work retains its permit until completion or cancellation recognition; shutdown releases queued permits only while removing those items.

The supplied regression holds a real executor thread busy, cancels the remaining submissions, rejects 1,000 readmissions, and checks capacity recovery. The added concurrent submission/cancellation/shutdown test exercises additional schedules. Neither test exhausts possible interleavings, but the source supports the relevant count invariant.

This closure concerns executor work items. It does not bound live processes after failed cleanup, serialized/transient allocation, exception state, transport buffers, retained results, or aggregate Python/OS memory. Pre-submission size rejection also occurs after serialization.

**R9 — actual launcher abort is materially stronger**

`run_one()` separates `run_succeeded` from `cleanup_confirmed`. Normal runtime return and pressure-helper reaping are required before confirmation. The ownership record is replaced atomically. Stop-file failure and termination permission errors no longer prevent subsequent pressure-helper escalation and wait attempts.

For ordinary confirmation dictionaries, `execute()` stops after any nonzero child exit, absent/false confirmation, or watchdog/control failure. A pressure `final.json` cannot authorize another condition.

The real-child regression exercises the actual `execute_child()` boundary: a subprocess writes false ownership confirmation and an application final marker, exits nonzero, and the launcher marks the next condition `NOT_ATTEMPTED`. Preparation and analysis remain mocked. This supports the specific cross-process continuation fix without constituting a full campaign rerun.

The Windows watchdog regression also launches a disposable parent/descendant pair. Its evidentiary limitation is identified below.

**New defect R9-v2-A — MODERATE: non-timeout communication failure bypasses launcher cleanup.**

**Source:** `experiments/cycle5_async.py`, `execute_child()`.

**Concrete trigger:** After `Popen` succeeds, the initial `proc.communicate(timeout=timeout)` raises `OSError` rather than `TimeoutExpired`, while the coordinator or descendants remain alive.

Only `TimeoutExpired` enters tree termination and bounded reaping. The exception instead reaches `execute()`, which stops the campaign, but `execute_child()` performs no cleanup attempt for its still-owned process. Campaign abort is preserved; cleanup-attempt coverage is incomplete.

**Required correction:** Protect the full post-spawn ownership interval with cleanup handling for communication failures, preserving the initiating error and cleanup uncertainty. Add a regression that checks both abort and owned-process cleanup attempts.

**New defect R9-v2-B — MINOR: valid JSON with the wrong confirmation shape bypasses explicit remaining-run disposition.**

**Source:** `experiments/cycle5_async.py`, `execute()` ownership-record parsing.

**Concrete trigger:** `cleanup.json` contains `[]` or `null`. JSON parsing succeeds, but `.get(...)` raises `AttributeError`, outside the caught exceptions.

The campaign stops, so this is not unsafe continuation. However, later rows are not explicitly recorded as `NOT_ATTEMPTED`, and normal campaign finalization is bypassed. The claim that every malformed confirmation follows the documented disposition path is therefore too broad.

**Required correction:** Validate the decoded record’s type before field access and route invalid shapes through the ordinary uncertain-cleanup abort path.

**New test defect R9-v2-C — MINOR: failure to acquire a descendant handle can pass without proving exit.**

**Source:** `tests/test_cycle5_campaign_cleanup.py`, `test_real_windows_owned_tree_timeout_terminates_descendant()`.

**Concrete trigger:** `OpenProcess(...)` returns a null handle. The test performs no assertion in that branch and does not inspect the Windows error.

An already-exited process can produce this outcome, but a handle-access failure is not equivalent to confirmed exit. The reported pass does not reveal which branch occurred.

**Required correction:** Distinguish confirmed absence from inability to inspect the process, or acquire a suitable process handle before triggering cleanup. Retain the current result as evidence that the disposable test passed its assertions, not proof that every successful gate observed a signaled descendant handle.

R9 consequently has narrow closure for the original marker-authorized continuation defect, while cleanup certainty remains qualified. No pressure saturation, sustained-liveness, exhaustion, resource-isolation, crash-recovery, or universal Windows tree-termination claim is closed.

**R13 — successful-response reader-local closure retained**

`WarmProcess._read()` deletes `line` and `value` after enqueue and before its next blocking read. The supplied regression inspects the actual reader frame after response consumption and checks that the response queue is empty. This continues to support closure of the specific successful-response idle-local retention defect.

Fault-path tracebacks, queued responses, unresolved workers, arbitrary module globals, caches, stochastic adapters, and other holders remain outside that closure. Neither this regression nor the full-suite count establishes a memory plateau.

**Authority and scope**

The supplied correction does not establish a new production actuator capability for shadows. `execute_shadow()` continues to reject production identity, and accepted nonproduction outcomes must retain `ESTIMATED` provenance. The new defects concern lifecycle containment, evidence integrity, and failure handling; no CRITICAL unauthorized authoritative mutation is demonstrated.

Production remains authoritative only within the declared software test environment. Minimal environments and temporary directories do not remove inherited OS-account permissions. The reviewed scope remains cooperative first-party execution.

**Limitations**

All execution results and hashes are supplied evidence. The full 96-test source set and all dependencies are not embedded, and no tests were independently rerun. The gate cannot establish coverage of every failure or concurrency schedule. Earlier review findings and newer passing tests do not combine into complete hostile-process safety.

The unchanged measured study retains **R1 storage, R5 positive memory growth/offline allocation, R6 cadence variability, and R7 delayed evidence as OPEN**. No performance, memory/byte boundedness, longevity, recovery, saturation, resource-isolation, or deployment claim is upgraded.

**Open questions and next actions**

1. Correct and explicitly test the warm token-withdrawal/dequeue shutdown race.
2. Prevent new cold creation while unresolved live cold ownership consumes the allowed process budget.
3. Complete the consumed runtime schema and derived-numeric checks, including the concrete CPU-field and utility-difference counterexamples.
4. Cover non-timeout launcher communication failure, malformed confirmation shapes, and inconclusive Windows handle inspection.
5. Preserve the existing gates, reviews, negative controls, and all result directories. Any correction requires a new source identity and fresh local gate.
6. Before fresh performance collection, freeze a new protocol and compatible preparation gate. The supplied `prepare()` still references the historical runtime gate; its compatibility with the final v2 source is not established here. Do not rewrite that historical gate to authorize new source.
7. Predeclare storage-failure accounting and acceptance criteria for cadence, retained memory, requested-set evidence yield, and incomplete runs. A fault-focused study may investigate these open mechanisms, but must not present them as already resolved.

**Fresh-study decision:** The corrections provide substantial local support for several specific mechanisms and a stronger basis for preparing a new systems study. They are **not yet sufficient for an unconditional fresh performance-campaign readiness recommendation**, given the remaining MAJOR ownership and validation paths. After those paths are corrected and locally gated, a fresh predeclared finite systems study would be appropriate to investigate the still-open empirical questions. That would remain research validation, not deployment approval. **Trust D; learning BLOCKED.**