# CSC Cycle 5: post-measurement v3 systems re-review

**Artifact:** `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v3.md`

**Status:** Independent static review of the supplied packet, 2026-10-06. Returned as Markdown artifact text; no tools, delegation, edits, experiments, independent test execution, or hash verification performed. The v3 corrections are **implemented and reportedly locally tested**, not deployment-validated.

The two concrete v2 R2 capacity/shutdown defects are narrowly closed. The specific warm CPU-schema and utility-difference counterexamples are corrected. However, reachable **MODERATE** evidence-validation, campaign-disposition, and gate-compatibility gaps remain. No new CRITICAL authority breach or MAJOR defect is established.

**Fresh-study decision:** **Not yet adequate for an unqualified correctness-gated recommendation covering the supplied local warm/cold campaign.** The remaining corrections identified below are concrete and limited; this review does not require another general hardening exercise or resolution of the measured study’s empirical findings before a fault-focused finite study can be planned. Fresh collection requires those corrections, a compatible source-bound gate, and a separately frozen protocol. This is not deployment approval. **Trust remains D; learning remains BLOCKED.**

**Question:** Do the post-measurement v3 corrections resolve the concrete remaining v2 findings concerning warm lease shutdown, unresolved cold creation capacity, consumed worker-runtime validation and derived arithmetic, campaign cleanup and disposition, Windows descendant inspection, and preparation-gate compatibility?

**Evidence and source identity**

| Variant or artifact | Supplied evidence and scope |
|---|---|
| Immutable measured source | **86-run study**, unchanged. Its aggregate source identity is not supplied here. No correction-gate identity is substituted for it. |
| Historical precollection gate | **66 tests**, a separate historical variant. Its exact identity and execution duration are not supplied here. It does not authorize current source. |
| v1 correction | **80 tests in 30.089 seconds**; source identity `12f8d30d9bc2628cb89b5ef918d4628552d5302fb8eb77de64443c34dfc67b77`, as reported by the supplied v2 review. |
| v2 correction | **96 tests in 28.181 seconds**; manifest elapsed time **28.66800800000783 seconds**; source identity `b4d08f39e99aa5a26bcba89e4d7d4e41a1a76c3f007aaba41bc03efc60334b41`. |
| Current v3 correction | `results/cycle5-validation/post-review-hardening-20261006-v3/`; **103 tests in 39.450 seconds**, exit code 0. Manifest elapsed time is separately **40.059593600046355 seconds**. |
| v3 full source closure | `beceb6ad110922758e01377090d296571307cbcfa4ea812288d7799609d930de` |
| v3 CSC source identity | `af623503412d5fed8137ae751d9428af964e912e795eaed12b7e10dcd1cf24d3` |
| v3 manifest hash | `0af7649029952bd7fff738fa0050c3ef0a85cd840aae17b9d42d5b238c2a4603`, reported by the machine table. |
| Deterministic analysis | `research/tables/cycle5_post_review_hardening_v3.json`; analysis-script hash `151030493c15b50125002663c52835cc47c9553ab5e39504448cf482346a498b`. The later analysis script is outside the executed runtime closure. |
| Review baseline | `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v2.md` |
| Correction account | `research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v3.md` |

The v3 manifest identifies:

- `csc/branches.py`: `fb219b2732dff773327fa160cb38745a2f90e198cd179602543d93b264e4ca8a`
- `csc/compare.py`: `558cf58e768c44b79e2bad67de44c6b900a013210bcc52dec88aefe7b5aaba4f`
- `experiments/cycle5_async.py`: `e78cb364bc49cc8e4882a3c1ef6d4ed10110cc9c118f6d6b9836152a1635d7ef`

The manifest’s `analysis_script_identity_sha256` value, `0929e3321c9f17a7c3f732cfeadca9eb729e78031c3aa47c5ea3df96c3f76cbb`, identifies the archived `experiments/cycle5_hardening_v3_validation.py`. It is distinct from the later analysis-script hash above.

The supplied records report no source changes during the gate, no subsequent runtime/test/campaign source changes, and no broken artifact hashes. These are reported checks, not checks performed by this reviewer. The earlier 13-test campaign-cleanup gate remains a separate targeted variant, not an integrated v3 identity.

**No corrected-source performance experiment exists.** Gate durations are test-execution measurements, not cadence, throughput, evidence-yield, memory, or storage results.

**Method:** Trace only the embedded source and tests through acquisition, token return, construction, unresolved ownership, result validation, downstream arithmetic, launcher cleanup, confirmation parsing, and preparation. Distinguish source-supported invariants from schedules exercised by reported tests. Counterexamples below are static constructions, not observed v3 failures or estimates of their frequency in the measured archive.

**Preserved negative evidence**

The supplied v3 machine table records these probes against the archived **v2** source:

| Probe | Reported negative result |
|---|---|
| `runtime_cpu` | String `cpu_ms` accepted as `REPORTED`; worker returned. |
| `utility_difference` | Utilities `+1e308` and `-1e308` accepted; difference nonfinite; worker returned. |
| `warm_lease_shutdown` | Three-second watchdog expired; elapsed time approximately 3.277 seconds. |
| `cold_capacity` | Two spawns and two owned processes despite one configured slot; both assignments returned `TIMEOUT`. |

The baseline’s earlier negative controls—cleanup/malformed-runtime failures with worker return, nonfinite mirror divergence, and enrichment-size acceptance with worker reuse—also remain preserved historical evidence. They are not reassigned to v3. None of these synthetic probes establishes occurrence rates in the 86-run study.

**Per-finding dispositions**

| Finding | v3 disposition |
|---|---|
| R2-v2-A — dequeued warm task stranded without token | **Narrowly closed.** Closure and token publication share the condition boundary; acquisition checks closure and has a finite timeout. |
| R2-v2-B — unresolved cold ownership permits further creation | **Narrowly closed.** Construction reservations and owned processes constrain creation, including direct `_execute()` calls. |
| R4-v2-A — consumed runtime fields | **Exact warm CPU defect corrected; overall closure incomplete.** Cold results bypass the new schema, and finite warm CPU values can overflow downstream aggregation. |
| R4-v2-B — utility/epsilon/regret overflow | **Specific counterexample narrowly closed.** Warm metric domains and the shared utility envelope prevent the supplied path; regret arithmetic independently rejects nonfinite differences. |
| R9-v2-A — non-timeout communication cleanup | **Narrowly closed for the supplied operational failure path.** Cleanup attempts precede propagated launcher failure. |
| R9-v2-B — non-object cleanup JSON | **Shape exception corrected.** Remaining MODERATE defect: uncertain cleanup on the final condition can still produce campaign status `COMPLETE`. |
| R9-v2-C — Windows null-handle inspection | **Null-handle branch corrected.** A separate MINOR false-pass remains for a failed wait operation on an acquired handle. |
| Fresh-study compatible gate | **Explicit gate required, but incomplete compatibility coverage.** The supplied v3 manifest is not directly accepted; an executed pressure helper is outside the enforced hash set. |
| R3 — cancelled physical backlog | **Prior narrow count closure retained.** |
| R13 — successful-response reader locals | **Prior narrow closure retained.** |
| R1 — storage | **MAJOR / OPEN for the measured study.** |
| R5 — memory/offline allocation | **MAJOR / OPEN for the measured study.** |
| R6 — cadence variability | **MAJOR / OPEN for the measured study.** |
| R7 — delayed evidence | **MAJOR / OPEN for the measured study.** |

R8, R10, R11, R12, R14, and R15 retain their previous qualified dispositions. This review does not reassess or upgrade them.

**R2 — warm acquisition, shutdown, and token publication**

In `csc/branches.py`, `_acquire_worker()` checks `closing` before attempting `get_nowait()`. If no token exists, it waits on `lease_condition` only for the remaining interval to a monotonic deadline.

`close()` sets `closing` and calls `notify_all()` while holding that same condition. `_return_worker()` checks closure and publishes its token under the same condition.

This resolves both relevant orderings:

1. A task reaches acquisition after closure: it faults without waiting for a token.
2. A task encounters an empty token queue before closure: condition waiting releases the lock, allowing closure to set the flag and notify it. On waking, it checks closure again.

A return racing with closure either publishes before closure becomes effective or observes closure and publishes nothing. There is no check-then-publication gap allowing a token to be published after the closure boundary. Tokens already present cannot authorize another acquisition because closure is checked first.

The supplied `test_shutdown_wakes_dequeued_warm_task_waiting_for_lease` removes the token and establishes that the future has been dequeued before closing. It does not instrument the exact instant the task enters `Condition.wait()`, nor reproduce every original A/B scheduling step. Nevertheless, its setup exercises the relevant empty-token/dequeued state, and the source handles both acquisition-before-close and close-before-acquisition orderings.

`test_open_manager_warm_lease_wait_has_finite_timeout` separately supports the open-manager empty-token timeout. That timeout is a lease-acquisition bound; it is not one shared deadline covering acquisition, replacement construction, execution, and cleanup. No universal wall-clock shutdown guarantee follows.

**R2 — cold creation capacity and constructor races**

The cold path reserves `cold_constructing` under `worker_lock` before `Popen`. Concurrent creation checks count both `cold_processes` and `cold_constructing`. A returned process enters `cold_processes` before its reservation is removed.

The correction account describes an atomic replacement. More precisely, the source uses separate locked additions and decrements, creating a possible interval of **conservative double counting**, not an interval in which both representations are absent. Another dispatcher can temporarily see less capacity, but cannot use that interval to exceed the process budget.

If creation raises before returning a process, the reservation is released. If closure begins during creation, the reservation remains visible while construction is outstanding; after registration, the closing check directs the process into cleanup. Existing paused-spawn regressions support this ownership sequence.

An unresolved process remains counted after its task releases executor capacity. `admission_capacity()` incorporates that ownership, and the guard immediately before `Popen` independently enforces it. Consequently, a stale admission snapshot or direct `_execute()` call does not bypass the process budget.

`test_unresolved_cold_process_consumes_process_capacity` specifically checks zero subsequent admission and no second spawn after termination denial.

Ownership retention can conservatively block later work until cleanup resolves it. A denied `kill()` also still skips the following `communicate()` within that particular cold exception block. Neither qualification reopens the corrected accumulation defect: unresolved ownership continues to consume creation capacity.

**R4 — warm schema, quarantine, and validation order**

For local warm workers, `validate_worker_result()` and `_enrich_result()` both remain inside the exclusive lease interval.

The schema now requires finite, nonnegative numeric values for execution, hydration, CPU, worker start/completion, launch-to-entry, and startup timing. It rejects booleans as those numeric values. It also requires:

- Integer `inputs_consumed` equal to trace length and a positive integer PID.
- Metadata version 1, a positive integer completed-task count, and literal `reset_verified=True`.
- Absent/null or nonnegative integer RSS/handle counters.
- Absent/null or finite, nonnegative numeric `process_cpu_s`.
- Finite, nonnegative values for the named metrics and queue-trace coordinates.

The parent warm transport supplies the receipt timestamp and startup timing; enrichment overwrites coordinator dispatch, queue, transport, and byte-accounting fields. Final serialized-size validation remains before token return.

On validation or enrichment failure, `_execute()` clears the reusable `worker` reference before attempting destruction. Failed destruction retains ownership and quarantine while publishing a replacement token rather than the suspect worker. Replacement remains constrained by unresolved ownership.

These changes close the supplied string/negative warm `cpu_ms`, boolean input counter, negative warm metric, and extreme warm utility fixtures. Two related downstream gaps remain.

**New finding R4-v3-A — MODERATE: accepted finite warm CPU values can overflow aggregation after lease release**

**Path:** `csc/branches.py::validate_worker_result()` → warm `_execute()` lease return → `csc/pending.py::accept()` lifecycle recording → `experiments/cycle5_async.py::reduce_run()`.

**Exact trigger:** Two otherwise valid warm results each contain:

```python
runtime["cpu_ms"] = 1e308
```

Each value is numeric, finite, and nonnegative. Both responses pass validation, are enriched successfully, and can return their workers to circulation. The reducer subsequently executes:

```python
worker_cpu = sum(r.get("cpu_ms", 0) for r in runtimes) / 1000
```

The sum overflows before division. The report contains nonfinite `accepted_or_late_worker_cpu_s`; `execute()` subsequently passes that report to `canonical()`, whose `allow_nan=False` rejects it.

The synchronous runner has the corresponding per-epoch summation in `worker_cpu_ms`.

This is a remaining corruption-to-accounting-failure path after lease release. It is not a claim that a real worker consumed that CPU time. The supplied fault model already includes corrupt worker numerics; individual finiteness alone does not establish aggregate arithmetic safety.

**Required correction:** Establish a defensible pre-release CPU accounting envelope for the declared finite study, or an equivalent contract that makes downstream aggregation safe. Merely allowing a downstream exception after worker reuse would not establish the stated quarantine property. Add a focused regression for accepted-field aggregation overflow.

**New finding R4-v3-B — MODERATE: local cold results bypass the new runtime schema and metric domains**

**Path:** Cold `csc/branches.py::_execute()` → identity/provenance checks → `_enrich_result()` → `csc/pending.py::valid_identity()` and lifecycle recording → `experiments/cycle5_async.py::reduce_run()`.

**Exact trigger:** A cold child exits successfully and emits an otherwise valid matching result with finite `execution_ms` and:

```python
runtime["cpu_ms"] = "bad"
```

Only the warm branch invokes `validate_worker_result()`. Cold enrichment does not consume or reject `cpu_ms`; the pending ledger does not validate runtime fields. The string therefore reaches the same reducer summation that motivated R4-v2-A and raises `TypeError`.

The same bypass leaves cold metric-domain checks incomplete. For example, a finite negative `mean_queue` can pass the pending ledger when the configured weights keep utility inside the new envelope.

The cold child has already exited, so reusable-worker quarantine is not the issue on this route. The defect is accepting malformed local worker evidence into recording and reduction.

**Required correction:** Apply the common consumed-runtime and metric-domain contract to cold results before publication. Keep warm-only reset/reuse metadata separate rather than requiring cold workers to fabricate warm metadata. This finding does not require expanding the review into hostile HTTP-service isolation.

**R4 — utility, epsilon, regret, and production failure**

`utility()` now rejects nonfinite results and magnitudes above `sys.float_info.max / 4`. Warm validation invokes it before release; comparison invokes the same function before accepting any utility.

This closes the supplied `+1e308` versus `-1e308` counterexample through two mechanisms: negative warm metrics are rejected, and utilities of those magnitudes exceed the shared arithmetic envelope even on paths without the warm domain check.

The envelope provides headroom for mirror differences, signed regret, and subtraction of epsilon. `finite_difference()` independently rejects overflow, and `RegretCalculator.calculate()` uses it for both regret subtraction and discounted subtraction. No remaining utility/epsilon/regret counterexample is established within these accepted bounds.

An invalid production utility is excluded and comparison returns `None`. The supplied runners then fail the run; this is **fail-closed accounting**, not successful continuation under every configuration accepted by `Config.validate()`. Future protocol preflight must respect the arithmetic envelope.

The conservative mirror-coordinate check remains under the warm lease. Its production-envelope premise remains qualified because `csc/world.py` source is not embedded, despite its supplied hash. No broader world-model guarantee is inferred.

The later identity/provenance checks and utility calculation repeat conditions already covered under the warm lease. They do not reopen the specific warm release-order defects. The CPU aggregation finding is a distinct downstream arithmetic operation not bounded by those checks.

**R9 — non-timeout launcher cleanup**

`execute_child()` now protects the post-spawn communication interval with `except BaseException`. An initial `OSError` enters `cleanup_owned_child()` before a launcher error is propagated.

That helper attempts tree/group termination, parent kill as needed, bounded communication, and—if communication remains broken—a separate kill and bounded wait. Recorded cleanup errors preserve uncertainty. For an ordinary initiating exception, the raised `RuntimeError` retains its cause and reaches the campaign’s abort path.

The supplied non-timeout regression checks cleanup attempts after an injected pipe error. Together with the source and campaign-abort regressions, this closes the named R9-v2-A omission. It does not establish successful termination under every OS failure. The reported gate is Windows-local; this particular test’s mocks do not establish equivalent non-Windows execution coverage.

**R9 — malformed cleanup JSON and remaining campaign disposition**

The new `isinstance(confirmation, dict)` guard correctly handles `[]`, `null`, and strings without calling `.get()` on them. Missing, invalid, false, or wrong-shaped confirmation enters the ordinary uncertain-cleanup path. The supplied tests show later conditions marked `NOT_ATTEMPTED`.

A separate final-condition defect remains.

**New finding R9-v3-A — MODERATE: uncertain cleanup on the final condition can leave the campaign marked `COMPLETE`**

**Path:** `experiments/cycle5_async.py::execute()` status construction, unsafe-abort block, and final `meta.update()`.

**Exact trigger:**

1. Previous conditions have status `COMPLETE`.
2. The final coordinator returns code 0 without watchdog expiry.
3. Its cleanup record is non-object JSON, absent, or explicitly unconfirmed.
4. Analysis otherwise succeeds.

The current row is initially assigned `status="COMPLETE"` from exit code and watchdog status. Cleanup uncertainty sets `unsafe_to_continue`, but does not change that status. Because this is the last condition, no `NOT_ATTEMPTED` row is appended. The final expression therefore sees every row as `COMPLETE` and writes:

```python
meta["status"] = "COMPLETE"
```

Campaign continuation is stopped correctly. The defect is a false overall completion disposition despite explicit cleanup uncertainty. Earlier uncertain rows also retain the misleading row-level `COMPLETE` status, although subsequent `NOT_ATTEMPTED` rows usually prevent the aggregate error.

**Required correction:** Make cleanup/control failure affect the current row’s terminal status and the aggregate campaign verdict. Add a final-condition regression; the supplied two-condition malformed-shape tests do not cover this boundary.

**R9 — Windows descendant inspection**

The null-handle branch now requires Windows error 87 rather than silently passing. Access denial or another `OpenProcess` error therefore fails the inspection assertion. This closes the precise v2 null-handle gap.

**New finding R9-v3-B — MINOR: an acquired-handle wait failure is treated as exit**

**Path:** `tests/test_cycle5_campaign_cleanup.py::test_real_windows_owned_tree_timeout_terminates_descendant()`.

**Exact trigger:** `OpenProcess` succeeds, but `WaitForSingleObject(handle, 0)` returns `WAIT_FAILED` rather than a signaled or timeout result.

The test defines:

```python
alive = kernel.WaitForSingleObject(handle, 0) == 258
```

It consequently accepts every non-timeout return as proof that the process is not alive, including inspection failure.

**Required correction:** Assert the signaled result explicitly for the successful-handle branch and report other returns as failed or inconclusive inspection. This is a test-evidence defect, not proof that the supplied disposable descendant survived. Its correction would still not establish universal Windows descendant termination.

**Fresh-study gate — explicit requirement and compatibility limits**

`prepare()` now requires an explicit gate path, a passing flag, exit code 0, and matching hashes for current top-level CSC modules, test modules, and `experiments/cycle5_async.py`. It fails before creating the series when those checks fail. Historical gates are no longer implicitly selected.

The supplied v3 manifest lacks `gate_passed: true`. Consequently, it is **not directly consumable as the readiness manifest required by this implementation**. That is a fail-closed integration prerequisite, not evidence of unsafe authorization. Do not edit the immutable v3 manifest to make it pass; preserve it and issue an appropriate new readiness artifact.

**New finding GATE-v3-A — MODERATE: enforced compatibility omits an executed campaign helper**

**Path:** `experiments/cycle5_async.py::prepare()` required hash set and source copying → `run_one()` pressure-process launch.

**Exact trigger:** After obtaining an otherwise accepted gate, only `experiments/cycle5_pressure.py` changes. All required CSC, test, and `cycle5_async.py` hashes still match.

`prepare()` accepts the gate, copies the changed helper into the series, and `run_one()` executes it. The gate can therefore authorize a campaign containing executed pressure source different from the gated version.

The supplied v3 full manifest already records that helper’s hash, but `prepare()` does not enforce it. This is a compatibility-check gap, not evidence that the current supplied helper actually changed.

**Required correction:** Include the known executed campaign dependencies in the enforced compatibility set, including the pressure helper and relevant imported campaign support code. Check the frozen collection source against that gate. Merely archiving a new helper hash records the discrepancy without establishing that it was correctness-gated.

A compatible gate also does not itself establish a newly reviewed protocol. `prepare()` checks the existence of historical protocol/review paths; separate preregistration remains necessary.

**R3 and R13 — prior narrow dispositions retained**

No v3 change shown here undermines R3’s physical work-item count invariant. Cancellation alone does not release a permit; dequeue/completion or physical removal during shutdown does. The supplied executor source and reported unchanged before/after hash support retaining that disposition without expanding it into a byte or memory bound.

No v3 change undermines R13’s successful-response reader-local disposition. `WarmProcess._read()` still deletes `line` and `value` before its next blocking read, and the supplied frame-inspection regression remains present. Fault tracebacks, queues, unresolved workers, caches, and other retained objects remain outside that closure.

**Authority and limitations**

No supplied v3 change establishes a new production actuator capability for shadows. `execute_shadow()` rejects production identity, and accepted nonproduction outcomes retain `ESTIMATED` provenance. The findings concern lifecycle control, evidence integrity, and research authorization checks; no CRITICAL unauthorized authoritative mutation is demonstrated.

Production remains authoritative only within the declared software test environment. Mirrors remain same-action estimates; `K` counts distinct alternatives and excludes mirrors.

All executions and hashes are supplied evidence. The complete 103-test source set and all dependencies are not embedded. No coverage of unseen tests, all concurrency schedules, or all OS error combinations is inferred.

This review establishes no hostile isolation, universal kill guarantee, memory/byte bound, storage durability, sustained liveness, saturation, resource non-interference, or corrected-source performance result. The unchanged measured study retains **R1 storage, R5 positive memory growth/offline allocation and whole-file hashing, R6 cadence variability, and R7 delayed evidence as OPEN**.

**Next actions**

1. Close the two concrete R4 paths: safe CPU aggregation under the pre-release contract, and common validation of local cold results before publication.
2. Make uncertain cleanup change the current condition and campaign completion verdict; cover the final-condition case.
3. Require a signaled Windows wait result before claiming descendant exit in the disposable test.
4. Complete readiness compatibility checks for known executed campaign dependencies.
5. Preserve all existing runs, gates, reviews, and negative controls. Corrections require a new source identity and a new compatible local gate.
6. Before collection, separately freeze the finite study protocol, source, gate, and unique output directory. Predeclare storage-failure accounting, cadence and memory criteria, requested-set evidence yield, and incomplete-run dispositions.
7. Treat the future study as an investigation of the still-open empirical findings, not confirmation that v3 repairs improved performance.

**Decision:** The v3 corrections materially resolve the named R2 mechanisms and the specific utility-overflow defect. Remaining concrete MODERATE paths prevent complete R4 and fresh-study gate closure, while a campaign can still falsely report completion after final-condition cleanup uncertainty. Address those bounded defects before recommending the implementation as the correctness-gated basis for the proposed fresh local warm/cold study. **Trust D; learning BLOCKED.**