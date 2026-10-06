**Artifact:** `research/evidence/cycle5/cycle5_red_team_review.md`

**Status:** Independent post-evidence, read-only review of the supplied packet, 2026-10-06. No tools, edits, experiments, or delegation performed. Cycle 5 supports a finite local systems pilot with substantial unresolved systems limitations. **Trust remains Decision D; learning remains BLOCKED.**

**Question:** Does Cycle 5 demonstrate useful asynchronous counterfactual evidence while preserving production cadence, bounding continuous resource use, degrading gracefully, and preventing contamination across worker reuse?

**Evidence:** Embedded versions of `research/evidence/cycle5/cycle5_protocol.md`, `research/evidence/cycle5/warm_worker_correctness.md`, `research/evidence/cycle5/runtime_retention_design.md`, `research/evidence/cycle5/cycle5_failure_recovery.md`, `research/evidence/cycle5/cycle5_instrumentation_diagnostic.md`, `research/evidence/cycle5/cycle5_results_analysis.md`, `research/tables/cycle5_review_packet.json`, and the supplied runtime, storage, experiment, supplement, fault, and test source.

The packet reports 86 completed campaign runs, 41,686 branch trajectory replays without verification failures, and a 66-test frozen-source gate. Main and gate CSC source identities match exactly:

`9af9d6eb9324f34c13087cac8dcf0eddac30dd84edea1a92b6411c25010e79d8`

Different aggregate archive identities are not evidence of a runtime mismatch: the archives contain different additional material. These verification results are supplied evidence; this review did not independently recompute hashes or rerun verification.

**Method:** Static adversarial tracing of the embedded implementation, cross-checked against the reported deterministic results and preregistered definitions. Findings distinguish observed failures, source-established contract gaps, and untested failure mechanisms. Severity concerns the affected claim; an open MAJOR finding does not imply that an unobserved failure occurred during the campaign. No CRITICAL authority breach or fabricated measurement is established by this packet.

**Findings — separate decisions**

| Decision | Review verdict | Supporting evidence and boundary |
|---|---|---|
| Cadence | **Limited support; general preservation unresolved** | Normal warm runs have medians near 40.4 ms. Several seed-1501 conditions have large median and tail delays. No equivalence margin or hard real-time guarantee was established. |
| Evidence yield | **Supported in normal warm cells; fails broadly under injected delay** | Normal warm K=1 completeness is 1.0 for all seeds; warm K=2 is 0.988889–0.994444. Cold coverage is zero throughout. Moderate-delay warm coverage has median zero; severe-delay coverage is zero. |
| Continuous boundedness | **Selected count bounds supported; comprehensive boundedness unestablished** | Retained rings reach 64, tracked active tasks reach 12, and sampled pending packages remain below 16. Physical executor backlog is not measured, online memory slopes remain positive, and archival/offline memory costs grow. |
| Resource interference | **Not established as absent** | Synchronous coordinator work shares the production loop. Strong timing heterogeneity and storage tails persist under limited pressure probes. |
| Graceful degradation | **Partial worker-fault support; storage availability fails** | Physical worker deaths preserve the tested production trajectory while losing evidence. A transient CFR append failure aborts a 12-epoch run after one recorded production epoch. |
| Reuse integrity | **Supported for tested deterministic contracts; lifecycle enforcement gaps remain** | Cold/warm equivalence and contamination rejection tests are meaningful. Result validation occurs after returning a worker to the reusable pool, and the full retained transport state is not covered by the session allowlist. |

**R1 — MAJOR / open: evidence persistence can abort production, and partial finalization lacks a recovery transaction.**

**Evidence:** `PendingShadowLedger.finalize()` synchronously appends CFR, branch metrics, and lifecycle records before removing the pending package. `run_async()` propagates failures into an exception path that expires and finalizes pending packages again. The storage fault in `experiments/cycle5_faults.py` deliberately uses K=0 and fails the first CFR append; the reported result is one recorded production epoch out of 12, followed by a FAILED run.

This is an observed availability failure in the shared production-recording path, including when no shadows are requested. It cannot be discounted as an isolated shadow error or a successful graceful-degradation test merely because the test expected the abort.

The injected failure occurs **before** the underlying append. It does not test a successful CFR append followed by a failed branch-metrics append, a partial line, failed flush, disk exhaustion, or persistent failure. Because retirement occurs after several writes, exception cleanup can revisit a partially persisted package. Duplicate writes or failure during re-finalization are plausible; exact behavior also depends on the comparator, whose source is not supplied. Neither outcome is demonstrated here.

`KnowledgeStore` enforces a coordinator writer for appends and JSON replacement, which mitigates concurrent-writer races. It does not supply cross-file atomicity, fsync durability, or idempotent recovery. Cleanup failure can prevent the FAILED manifest update.

Production loss accounting has a related limitation: `reduce_run()` derives missing production epochs from CFR count. Authoritative simulation occurs before CFR persistence, so missing CFRs do not universally identify missing actuations. Preserve “recorded production epochs” as the storage-fault estimand.

**Required resolution:** Define required production durability separately from optional evidence persistence, then implement and test the chosen failure contract, partial-write recovery, and independent production-progress accounting.

**R2 — MAJOR / open: the claimed finite transport/shutdown bound omits blocking request writes.**

**Evidence:** `WarmProcess.evaluate()` performs `stdin.write()` and `flush()` before starting `_receive(shadow_timeout_s)`. Neither write has an explicit deadline. `BranchManager.close()` calls `pool.shutdown(wait=True)` before killing registered warm processes.

A live worker that stops reading its input can block a sufficiently large pipe write. The response timeout has not yet started, and shutdown waits for the executor task before reaching worker termination. This is an untested hang path; ordinary execution timeout and worker-death tests do not cover it.

`available_workers.get()` also lacks a timeout, although normal slot accounting is intended to make a token available. Replacement startup has a five-second readiness limit, but that limit is not an end-to-end assignment deadline covering every transport and cleanup operation.

The direct `Future.result()` guard establishes that production polling does not wait on an unfinished future. It does **not** establish bounded dispatch, bounded shutdown, or resource independence.

**Required resolution:** Apply a cancellable end-to-end transport deadline covering request transmission, response collection, replacement, and teardown. Shutdown must be able to terminate stuck transports before waiting indefinitely for executor settlement.

**R3 — MAJOR / open: tracked task caps do not establish a bounded physical executor queue.**

**Evidence:** `commit()` limits `ledger.active`; `expire()` cancels futures; `poll()` removes cancelled futures and releases their permits. `queued_shadow_tasks` counts only futures remaining in `ledger.active`. Submission uses `ThreadPoolExecutor` without an explicit bounded submission queue.

Cancelling a future does not establish that its submitted work item and captured request have been removed from the executor queue. Under standard executor behavior, cancelled queued work remains until a worker dequeues it. Consequently, repeated cancellation and replacement admission can retain more queued request objects than the reported active-future count.

The embedded packet does not include the Python executor implementation or measure its physical queue, so this review does not claim an observed unbounded backlog. It does establish that the displayed queue metric cannot prove the broader bound. The stalled-write path in R2 makes eventual dequeue progress especially important.

The 100-epoch saturation fixture uses `DeferredManager`, not the real executor, and cannot settle this question.

**Required resolution:** Bound actual queued work and retained request bytes, including cancelled-but-not-dequeued submissions. Measure that inventory independently of logical evidence eligibility.

**R4 — MAJOR / open: invalid worker output does not reliably destroy the worker before reuse.**

**Evidence:** In `BranchManager._execute()`, the warm worker is returned through `available_workers.put(worker)` in `finally`. Branch-identity and provenance validation occurs afterward. Numeric, trace, and input validation occurs later still in `PendingShadowLedger.valid_identity()`.

Therefore, a worker returning a structurally usable response with the wrong branch identity or provenance is already reusable when the manager detects the defect. A valid-identity response rejected by coordinator validation likewise has no demonstrated worker-quarantine path.

This contradicts the broad frozen contract that integrity failures destroy the process before another assignment. The gate covers malformed **assignments**, session contamination, crashes, timeouts, and oversized transport responses. Synthetic malformed-result tests verify coordinator rejection, not destruction of the emitting worker.

There is no evidence that such an output occurred in the main campaign, and this is not evidence of contamination in accepted results. It is an unenforced failure-containment requirement.

**Required resolution:** Keep workers quarantined until required output validation completes, with an explicit destruction policy for integrity failures. Test replacement after wrong-identity, wrong-provenance, and malformed valid-identity output.

**R5 — MAJOR / open: positive memory trends and offline costs prevent a continuous-memory plateau claim.**

**Evidence:** The all-epoch supplement reports:

| Run | Coordinator RSS slope, bytes/epoch | RSS second-half slope | Python current slope, bytes/epoch | Python current second-half slope |
|---|---:|---:|---:|---:|
| 3,000-epoch normal | 559.572 | 339.915 | 94.415 | 23.340 |
| 1,000-epoch saturation | 766.558 | 265.009 | 234.603 | 191.497 |

These are positive finite-duration trends, including the second halves. They do not prove a leak, but they do not establish a plateau either. The frozen warmup-excluded estimates also remain positive and must remain visible alongside the corrected all-epoch estimand.

Normal-run worker RSS has a negative all-epoch slope but a positive second-half slope. It spans 91 launches and 88 recycles; changing process membership and lifetime reset complicate interpretation. Saturation has one worker, no recycle, and positive worker RSS slopes. Its approximately 40-second duration does not exercise the 60-second lifetime limit.

The normal run reports `offline_summary_rss_bytes = 512155648`, approximately 512 MB in decimal units. Source shows this is a sample **after** summary computation, not an independently sampled maximum. `offline_summary_python_peak_bytes` is cumulative since `tracemalloc.start()`; the peak is not reset at the offline boundary.

`KnowledgeStore.close()` subsequently hashes artifacts using whole-file `read_bytes()`. That additional archive-size-dependent allocation and time occur after the reported summary measurements.

**Required resolution:** Establish byte inventories and phase-specific memory measurements, include final archive hashing, and investigate trends over longer preregistered durations. Preserve count bounds as a narrower result.

**R6 — MAJOR / open: median-over-seed summaries conceal substantial cadence failures.**

**Evidence:** In `cycle5_review_packet.json`, seed 1501 has:

| Cell | Run median interval, ms | Run p99, ms |
|---|---:|---:|
| K0 CPU | 88.437 | 261.226 |
| Cold K1 normal | 129.592 | 424.079 |
| Warm K1 moderate delay | 291.317 | 826.038 |
| Warm K1 CPU | 250.180 | 661.959 |
| Warm K2 storage | 291.945 | 800.589 |

Warm K2 storage also has a seed-1502 p99 of 67.781 ms. The storage concern is therefore not confined to the most heterogeneous seed block.

`run_async()` performs polling, validation, comparison, flushed storage, audit writes, OS sampling, and artifact stat calls on the coordinator loop. These affect subsequent starts even though the required production-path timer ends earlier. `barrier_ms = 0` is assigned, not a measured bound on all blocking operations.

The long-run minimum measured intervals exceed 40 ms. This supports descriptive strict-target overruns, not a violated physical actuation contract, which was never established. Relative-start pacing allows cumulative drift.

Normal warm cadence is encouraging within the tested environment. General cadence preservation and timing equivalence remain unsupported. Production trajectory equality cannot close this issue.

**Required resolution:** Report all run-level timing values prominently and preregister an operational cadence/drift contract before another preservation claim.

**R7 — MAJOR / open: bounded overload often preserves production by providing no usable evidence.**

**Evidence:** All cold cells have zero accepted counterfactual coverage. Warm moderate-delay completeness is `[0.211111, 0, 0]` for K=1 and `[0.116667, 0, 0]` for K=2. Every warm severe-delay cell has zero coverage. Long saturation records 1,733 dropped and 1,207 expired branches, with zero complete evidence.

A 600 ms injected service delay already exceeds the 300 ms acceptance deadline. That condition demonstrates behavior under infeasible service, not useful evidence delivery. Moderate delay leaves nominal room for individual tasks but does not establish sufficient sustained capacity for the requested branch arrival rate.

The two nonzero moderate-delay results occur in runs with much slower production cadence. Slower request arrival is a plausible contributor to improved coverage; these observations cannot be presented as evidence of useful yield at the intended pacing target.

Mirror-first, fixed-order admission is explicit and reproducible. It also creates action-dependent exposure under pressure. Aggregate completeness does not establish fair or representative counterfactual availability.

**Required resolution:** Evaluate a declared capacity/admission policy jointly on production cadence, requested-set coverage, evidence age, and per-action exposure. Never improve reported completeness by switching to admitted-work denominators.

**R8 — MODERATE / open: independent run starts and paired seeds do not remove host-time confounding.**

**Evidence:** `registry()` randomizes conditions within seed blocks, but completes seed 1501 before 1502 and 1503. Long runs occur afterward. Fresh coordinators remove some process-history dependencies; they do not reset host activity, filesystem cache, thermal state, or background scheduling.

Large cadence excursions cluster in seed 1501. The pressure measurements also vary substantially. These observations justify retaining all paired values and questioning causal attribution; they do not identify a cause.

The phrase “three independent paired seed/run units” is appropriate for avoiding epoch pseudoreplication, but does not establish exchangeable timing conditions across runs. Cold/warm comparisons test whole runtime configurations, including prestarted warm workers, not an isolated process-start component.

**Required resolution:** Use balanced condition ordering across time blocks, repeated baseline sentinels, and achieved-load measurements aligned to production. Do not retrospectively remove the early block or fit away its negative results.

**R9 — MODERATE / open: pressure probes establish activity, not resource exhaustion or isolation.**

**Evidence:** One unpinned CPU process runs on a 12-logical-CPU host, achieving 0.299–0.984 CPU seconds per wall second. Memory pressure holds 64 MiB and touches one byte per page. Storage pressure repeatedly flushes an approximately 4 MiB file without fsync.

These are legitimate bounded workload probes. They do not establish whole-host CPU saturation, memory scarcity, physical disk saturation, or scheduler isolation. A page-touch round is not a full-byte sweep of 64 MiB; flushed logical write throughput is not physical-device throughput.

`verify()` checks positive operations, touch rounds, or bytes and a bounded file size. Those checks cannot establish sustained stress throughout measured production.

There is also a source-level failure-path gap: pressure readiness occurs before `run_one()` enters its `try/finally`. Campaign fallback requests shutdown, but lacks a universal process handle for forced cleanup. The outer run subprocess has no timeout. These did not produce a reported main-run failure, but they weaken the campaign’s failure-containment contract.

**Required resolution:** Define achieved pressure and liveness over the production interval, introduce controlled safe intensity levels, and ensure helper cleanup on readiness and coordinator failure.

**R10 — MODERATE / open: several measurement fields are narrower than their names suggest.**

**Evidence:** In `run_async()`, `comparison_ms` and `reset_ms` are assigned zero, while `branch_creation_ms` aliases total evidence bookkeeping. `epoch_ms` and `coordinator_cpu_ms` exclude subsequent resource sampling and resource-record append. Windows coordinator process CPU includes executor-thread work and is not exclusive production-thread CPU.

`PendingShadowLedger.finalize()` timestamps comparison before CFR and branch-metrics writes. The reducer’s during-production count uses the later `FINALIZED` audit timestamp, which is a useful distinction, but comparison age is not durable availability latency.

`WarmProcess.startup_ms` starts after process creation and reader-thread startup. It is readiness-wait timing rather than total constructor cost. The separate pool-initialization duration provides broader coverage.

Windows working-set RSS is not exclusive allocated memory. Summing worker RSS can include shared pages. Short CPU observations remain quantized, and killed/expired workers without results leave CPU accounting incomplete. Keeping total CPU efficiency null is correct.

**Required resolution:** Rename measured components precisely, use null for unavailable component timings, and distinguish validation, comparison, publication, and durability timestamps.

**R11 — MODERATE / mitigated: requested-work and deadline semantics are substantially defensible, but verification is narrower than the headline.**

**Evidence:** `accept()` validates results and checks the clock before accepting them; equality with the deadline expires. `poll()` reads results only after `future.done()`. Expired running work retains its tracked permit until settlement. The main reducer uses complete requested epochs, not admitted epochs, and K=0 completeness is null.

Full comparison ages exceeding 300 ms are not automatically deadline violations: ordered finalization can occur after timely branch acceptance. Conversely, worker return before 300 ms is insufficient if coordinator validation occurs too late.

The supplied `verify()` replays **traces** of REPORTED comparable branches, including production. It does not replay wall-time behavior, independently reconstruct every acceptance decision, or independently validate every derived metric and comparison. Regenerating summaries with the same reducer checks reproducibility, not semantic correctness of that reducer.

The 41,686 replay count therefore supports deterministic trace agreement and archival consistency within the implemented checks. It is not 41,686 independent reset, deadline, or resource-isolation tests.

**Remaining action:** Add independent lifecycle/deadline and schema-consistency checks in the next verifier while preserving the present verification result at its actual scope.

**R12 — MODERATE / mitigated: postcollection semantic corrections are justified, but the frozen interpretations must remain explicit.**

**Evidence:** Frozen `reduce_run()` counts `record_status == "PARTIAL"`. The supplement instead counts any accepted comparable nonproduction evidence without a complete requested set. Warm K2 storage seed 1501 has semantic partial fraction 0.172222, which the raw status interpretation does not adequately describe.

Frozen resource trends slice away warmups before fitting. `hot_state_all_epochs()` restores the preregistered all-online-epoch estimand. Neither correction changes the original experiment, acceptance deadline, complete-epoch numerator, or measured duration.

Both corrections are supported by the supplied source and improve interpretation. They do not justify rewriting the frozen analysis. The compact review packet uses `partial_fraction` for semantic values while the frozen analysis uses that name differently; consumers must not treat identically named fields as interchangeable.

**Remaining action:** Use explicit field names and supplement identity in downstream reporting. Retain both partial measures and both resource cohorts.

**R13 — MODERATE / mitigated: tested reuse integrity is meaningful, but does not cover all retained state.**

**Evidence:** `WarmSession` checks a persistent-attribute allowlist, bounded assignment metadata, empty buffers, and unchanged environment; it rehydrates task state and resets global RNG. `execute_shadow()` creates task-local model, synchronization, actuator, and trace objects. The gate compares deterministic cold/warm outcomes across actions, regimes, and incidents, and tests contamination destruction and replacement.

The worker-loop correction explicitly deletes `result` and `line`. That specific worker-loop retention defect is **closed-with-evidence** in the supplied source and reported v2 gate.

However, `WarmProcess._read()` retains its previous `line` and `value` locals while blocking for the next response. This is parent-side transport retention, outside `WarmSession.__dict__`. It is bounded per reader and does not demonstrate model contamination, but it must be included in retained-byte accounting rather than covered by an unrestricted “no previous task record survives” claim.

The deterministic model does not exercise stochastic transition-state contamination. Environment equality and an object allowlist do not inspect arbitrary module globals or future adapter caches. Those limits remain real even if all current tests pass.

**Remaining action:** Preserve the tested first-party reuse claim, resolve R4, inventory transport retention, and extend the reset contract before introducing stochastic or stateful adapters.

**R14 — MINOR / closed-with-evidence for the narrow hypothesis: the proposed indefinitely retained `Counters` classes were not observed.**

**Evidence:** The postcollection diagnostic reports zero surviving target-class weak references after explicit collection in both measured blocks. The v4 mechanism check corrects the earlier attribute-lookup limitation. `os_metrics.py` confirms that a new ctypes `Counters` class is created on every call.

This closes the specific prediction that those observed classes survive collection indefinitely. It does not establish general leak freedom: residual traced allocation rises from 992 to 26,078 bytes, the probe covers only 110 measured calls, and forced collection is not normal production GC behavior.

The diagnostic does not explain the main cadence excursions or negate R5. No general memory claim is upgraded.

**R15 — MODERATE / open: fixed short durations prevent specification and longevity claims.**

**Evidence:** The factorial contains 200 epochs per run, below the protocol’s cited 500-epoch condition standard. Long tests contain 3,000 and 1,000 epochs, with evidence summaries excluding the first 20.

There is no supplied evidence of post-hoc duration selection: durations are fixed in the protocol and `configuration()`. Nevertheless, emphasizing the favorable long-normal result while ignoring zero-yield saturation or positive memory slopes would be selective interpretation.

Neither long run evaluates **>=10,000 consecutive epochs at >=90% completeness**. Three thousand epochs cannot be extrapolated into that result. The single host, authored traffic model, and cooperative processes also provide no physical-traffic, container, hostile-isolation, deployment, or full-specification validation.

**Limitations of this review:** The review is independent reasoning over an embedded packet, not independent execution. Complete raw traces, the full 66-test suite, comparator, contracts, world model, pressure-helper implementation, and verification dependencies are not all embedded. Reported archive verification is accepted at its documented scope. Source-derived failure mechanisms are not retroactively labeled observed campaign failures. No new statistical estimates, causal corrections, or literature claims were generated.

**Open questions:**

- How much of the early timing heterogeneity comes from coordinator work, host scheduling, storage, worker startup, or instrumentation?
- How many request bytes remain in executor queues after cancellation, and what happens when a live worker stops reading?
- Can malformed output trigger quarantine before the emitting worker serves another assignment?
- What causes the positive coordinator and saturation-worker memory trends?
- Which production records are mandatory for safe continuation, and what evidence loss is acceptable during storage failure?
- What requested-set yield remains attainable at the intended cadence under achievable service capacity and controlled contention?

**Next actions — precise Cycle 6 systems recommendation:**

Choose **production-path fault containment and bounded evidence transport** as Cycle 6’s primary systems objective. Longer runs alone would leave source-established lifecycle defects unresolved.

1. **Implement under a new source identity:** bounded physical submission queues and byte budgets; cancellable request/response transport; shutdown that can terminate stuck workers; validation-before-reuse quarantine; and a declared separation between required production persistence and optional evidence persistence. Any evidence spool must have a byte cap, explicit drop accounting, and a recovery contract.

2. **Gate the actual failure paths:** live worker stops reading; cancelled submissions remain queued; replacement readiness fails; invalid output has valid assignment identity; CFR succeeds but a subsequent append fails; write/flush partially fails; storage fails persistently; pressure readiness and cleanup fail. Check production progress, retained bytes, terminal loss classification, worker disposition, shutdown completion, and immutable archive consistency separately.

3. **Preregister confirmation before outcomes:** use fresh seeds, balanced time blocks, baseline sentinels, and pressure measurements covering production. Retain normal warm K=1/K=2, K0, and relevant cold controls. Include moderate overload, infeasible-delay loss behavior, and storage pressure. Define acceptable cadence/drift and evidence-loss behavior before collection; do not invent margins from Cycle 5.

4. **Then test duration and memory:** use at least the cited 500-epoch condition standard for retained performance cells and a separately declared >=10,000-consecutive-epoch test for the >=90% completeness specification. Measure all online epochs, physical queue bytes, process lifetime, archive growth, shutdown, offline summary, and final hashing. Evaluate the combined cadence/yield/resource contract, not completeness alone.

5. **Preserve all Cycle 5 evidence:** keep the frozen source, raw archives, failed validation attempts, negative storage result, original reducers, and hashed supplements. New fixes require a new correctness gate and immutable experiment series.

Cycle 5 warrants continued systems engineering and narrowly scoped confirmation. It does not warrant promotion to resource independence, general graceful degradation, continuous memory stability, production timing equivalence, or deployment readiness. **Trust remains D; learning remains BLOCKED.**

## Final closure judgment (frozen v5 source)

**Status:** CLOSED after an independent read-only judgment of the exact v5 source-bound gate, `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v5.md`. The delivery audit is `VERIFIED`: all 86 scheduled archive runs are present, the factor grid is exact, and required hashes/provenance artifacts pass. The performance archive was not rerun or modified.

### Final finding disposition

| Finding set | Final closure classification | Disposition |
|---|---|---|
| Any result-invalidating or future-experiment-unsafe defect | **CRITICAL: none** | No Cycle 5 headline is invalidated. |
| Current-tree defect that blocks a separately preregistered Cycle 6 study | **MAJOR: none** | v1-v5 source-specific gates resolved the reviewed lifecycle, validation, timing, analysis, and source-copy paths. This is not a new performance result. |
| R1 storage availability; R5 memory trend/offline cost; R6 cadence heterogeneity; R7 delayed-yield collapse | **MODERATE** | Immutable measured limitations. They require explicit Cycle 6 measurement and must not be converted into stability, isolation, or bounded-memory claims. |
| R8 host/order limits; R9 campaign scope; R10 timing/resource semantics; R11 verifier scope; R12 frozen-analysis naming/cohort boundary; R13 retained-state scope; R15 duration/specification gap | **MODERATE** | Documented limits or future hardening. They do not invalidate the recorded finite results. |
| R14 specific `Counters` cache hypothesis | Closed for its narrow hypothesis | It neither proves general leak freedom nor changes R5. |
| V5-T1 hydration/cleanup integration coverage | **MINOR** | Document only; no Cycle 5 patch. The gate's reducer/mocks do not exercise the strongest multi-value integration relationship. |

R2/R3/R4 and the later bounded lifecycle findings are **resolved only for the current v5 correctness-gated source**, through their named negative controls and the v1-v5 gates. They remain historically relevant defects of the pre-correction measured source and are not evidence about v5 production cadence, memory, storage, or yield.

### Evidence boundary and final verdict

- **Measured archive:** `results/cycle5-async/local-20261006-v1/`, pre-correction source `9e473658ebd91e004e9caa9bb02971e95db98e22b76771bc45b7e9dd783b4cba`. It supports normal-cell warm evidence-yield improvement, finite logical trajectory checks, bounded retained record counts, and the negative results below.
- **Post-collection defects:** source review found transport, queue, reuse, cleanup, analysis, and provenance paths after archive collection. These did not alter archival files or measured conclusions.
- **Later gates:** v1-v5 gates, ending in v5 source `c3e81bb6c4148f9b899970b5e71fe8a8b77226ba862ff3b7d1fd0f767cdda4be`, establish only tested current-code behavior. The v5 gate is 108 tests / 28.362 seconds.
- **Measured negative results:** delayed conditions collapsed complete evidence yield; retained counts were capped but positive RSS/Python slopes prevent a bounded-process-memory claim; a transient storage append error stopped production after 1/12 epochs; production timing has severe individual excursions; and resource non-interference was not established.

Warm workers materially improved complete evidence in normal cells (cold K=1/K=2: zero; warm K=1: 1.000; warm K=2: median 0.994), but that improvement disappears at median delay pressure. Production trajectory hashes matched within the measured paired units, while cadence was not robust across every run. Warm-worker reset/recycle/replacement gates passed only for the declared first-party deterministic model. Hot retained counts were bounded in the finite probes; process memory was not demonstrated bounded. Fixed bounded admission reduced requested work under pressure, but loss of mirrors, zero median delay yield, and storage-triggered production abort mean general graceful degradation is not established.

Cycle 5 is therefore **CLOSED**. The exact Cycle 6 research objective is: **preregister and run a fresh controlled-host systems experiment from the v5 source that measures production-path fault containment, physical queue/byte bounds, storage persistence failure/recovery, hot RSS/Python trends, cadence tails, and requested/admitted/completed K under normal, delay, worker-capacity, and safe resource pressure.** It must preserve immutable evidence, use fresh seeds and declared durations (including the cited 500-epoch condition and separately declared 10,000-epoch continuous standards), and must not retune trust or implement learning. Trust remains **Decision D**; learning remains **BLOCKED**.
