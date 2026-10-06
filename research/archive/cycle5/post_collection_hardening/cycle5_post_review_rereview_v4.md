**CSC Cycle 5: post-measurement v4 systems re-review**

**Artifact:** `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v4.md`

**Status:** Independent static review of the embedded packet, 2026-10-06. Returned as Markdown artifact text; no tools, delegation, file edits, tests, experiments, or independent hash verification performed. The v4 corrections are **implemented and reportedly locally tested**, not deployment-validated.

The named v3 CPU-overflow, cold CPU/metric-validation, final execution-row/campaign-verdict, and Windows wait-result counterexamples are corrected. Required campaign helper names are now included in preparation’s compatibility checks, and both supplied manifest formats are supported.

However, three bounded **MODERATE** gaps remain: consumed timing fields can still break reduction; analysis can classify a cleanup-failed condition as complete; and preparation does not compare the copied execution source with the gate. Exact triggers are specified below. No new CRITICAL authority breach or MAJOR implementation defect is established.

**Fresh-study decision:** **Not yet locally adequate for an unqualified recommendation as the correctness-gated implementation basis for the proposed finite local warm/cold Cycle 6 study.** The remaining corrections are limited to these concrete paths. Planning and preregistration can proceed, but collection should follow their correction and a new compatible gate. This review does not require resolving the measured study’s empirical findings before conducting a separately preregistered investigation.

**Trust remains D; learning remains BLOCKED.**

**Question:** Do the bounded v4 changes close the concrete v3 findings concerning finite-study CPU aggregation, common local worker validation, final-condition cleanup disposition, Windows descendant inspection, and source-bound campaign preparation, while preserving prior narrow lifecycle, arithmetic, physical-count, and reader-local closures?

**Evidence identities and variant boundaries**

| Evidence | Identity and scope |
|---|---|
| Immutable measured source | **86-run study**, unchanged and not rerun. Its aggregate source identity is not supplied. No correction-gate identity is substituted for it. |
| Historical precollection gate | **66 tests**; separate historical variant. Exact identity and duration are not supplied. |
| v1 correction | **80 tests in 30.089 seconds**; source identity `12f8d30d9bc2628cb89b5ef918d4628552d5302fb8eb77de64443c34dfc67b77`, as reported in the supplied baseline. |
| v2 correction | **96 tests in 28.181 seconds**; manifest elapsed time **28.66800800000783 seconds**; source identity `b4d08f39e99aa5a26bcba89e4d7d4e41a1a76c3f007aaba41bc03efc60334b41`. |
| v3 correction | **103 tests in 39.450 seconds**; manifest elapsed time **40.059593600046355 seconds**; full source identity `beceb6ad110922758e01377090d296571307cbcfa4ea812288d7799609d930de`. |
| v4 gate | `results/cycle5-validation/post-review-hardening-20261006-v4/`; **106 tests in 28.399 seconds**, exit code 0. Manifest elapsed time is separately **28.838843000005 seconds**. |
| v4 full source identity | `f492d4de5e959702358740ecb1d73f580e674d63234ae3a363dabd2e4f0b25fb` |
| v4 CSC source identity | `ce965b67e6f1361dfabc34be33b3abab56a5e6b1d95fe8aaeb5c5eeaf360d566` |
| v4 manifest hash | `f19d53471e2db743b18df032ac006ed5d201e7de7c17e2b7bcc8b719adf77ac6`, reported by `research/tables/cycle5_post_review_hardening_v4.json`. |
| Archived validation script | `experiments/cycle5_hardening_v4_validation.py`; hash `da5cbed5345ef86a3ce0c78f32a61648e6c5cb57a725461b6cf6da47504e70e5`. This is the manifest’s `analysis_script_identity_sha256`. |
| Later analysis script | Hash `dbc6dc23e0df95bec66d5c040c373cce28945835575e257e4aede903627f5493`; identified separately and outside the executed runtime gate. |
| Review baseline | `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v3.md` |
| Correction account | `research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v4.md` |

The v4 manifest records these relevant source hashes:

| Source | SHA-256 |
|---|---|
| `csc/branches.py` | `ebd49487a775f614659eb5c7956077faec7af66031863d0398bb4618830758e9` |
| `experiments/cycle5_async.py` | `50bb3fc995f82c459c408d8b854f8ed931ce640ccf260fedae037065f22590dc` |
| `experiments/cycle5_pressure.py` | `2f0083bf8bd4f417fee26ba984e3f2e12b295a0222c535a38a4a50c798ce1e2c` |
| `experiments/cycle5_loss.py` | `adba64d1ebc964935ea0000662ccdc781cfd91e99b6ad8e785943b6167ac91ba` |
| `experiments/replay.py` | `858dcdf9405b62267c1da52b243d5824e09b8ca770ae78f7bef9f787d8d0dec3` |

The machine table reports empty lists for broken artifact hashes, source changes during the gate, and subsequent runtime or other source changes. These are supplied results, not reviewer verification. The manifest reports Windows 11 and Python 3.14.7. The embedded log reports 106 passing tests; it supplies no corrected-source performance result.

**Method:** Trace the embedded source through validation, lease return, lifecycle recording, aggregation, cleanup disposition, source checking/copying, and Windows inspection. Assess the embedded regressions only for the conditions they establish. Preserve the v3 baseline’s qualified dispositions where the bounded changes do not undermine them. The counterexamples below are static constructions, not observed failures or estimates of their frequency.

**Preserved negative evidence**

The v4 packet reports the following controls against archived **v3**, not v4:

| Control | Reported result |
|---|---|
| CPU aggregation | Extreme finite CPU accepted as `REPORTED`; worker returned; two-value sum nonfinite. |
| Cold validation | String `cpu_ms="bad"` accepted as `REPORTED`. |
| Final cleanup disposition | Uncertain cleanup left both execution row and campaign `COMPLETE`. |
| Gate format | v3 manifest rejected with `RuntimeError:Warm correctness gate did not pass`. This was fail-closed incompatibility. |

The baseline’s v2 CPU, utility-difference, warm-lease-shutdown, and cold-capacity controls remain historical negative evidence. Earlier malformed-runtime, failed-cleanup/quarantine, mirror-divergence, and enrichment-size controls also retain their original variant attribution. None establishes occurrence rates in the immutable measured study.

**Per-finding dispositions**

| Finding | v4 disposition |
|---|---|
| R4-v3-A — CPU aggregation overflow | **Narrowly closed** for the declared finite runner contract. |
| R4-v3-B — cold CPU/schema and negative metrics bypass | **Named triggers narrowly closed.** Remaining consumed-timing defects are identified as R4-v4-A below. |
| R9-v3-A — final execution row and aggregate campaign falsely complete | **Named row/campaign trigger narrowly closed.** Analysis still disregards that failure disposition; see R9-v4-A. |
| R9-v3-B — acquired-handle `WAIT_FAILED` false-pass | **Narrowly closed.** Successful inspection requires an explicit signaled result. |
| Gate-format incompatibility | **Closed for the supplied formats**, subject to matching source hashes. |
| GATE-v3-A — pressure helper omitted from enforced set | **Named omission closed.** Copied execution source is not checked against the gate; see GATE-v4-A. |
| R2 — warm lease shutdown and unresolved cold capacity | **Prior narrow closures retained.** |
| R3 — cancelled physical backlog | **Prior physical-count closure retained.** |
| R4 — utility arithmetic and quarantine order | **Prior narrow closures retained.** |
| R9 — non-timeout launcher cleanup and malformed confirmation shape | **Prior narrow closures retained.** |
| R13 — successful-response reader locals | **Prior narrow closure retained.** |
| R1 — storage failure | **MAJOR / OPEN for the measured source.** |
| R5 — positive memory trends and offline allocation | **MAJOR / OPEN for the measured source.** |
| R6 — cadence variability | **MAJOR / OPEN for the measured source.** |
| R7 — delayed evidence | **MAJOR / OPEN for the measured source.** |

R8, R10, R11, R12, R14, and R15 retain their prior qualified dispositions without reassessment or upgrade.

**CPU aggregation: finite-study envelope established before release**

`csc/branches.py::validate_worker_result()` now requires:

```python
N = max(1, duration_epochs * max(1, shadow_count + mirror_count))
cpu_ms <= sys.float_info.max / (2 * N)
```

For validated configurations, duration is at most 100,000 epochs and the requested mirror-plus-alternative count is at most four. The scheduler plans no more than that requested count per epoch. Warmup epochs are already included in `duration_epochs`.

On the supplied asynchronous path, each completed future is processed and removed from `active`; ordinary polling does not repeatedly record its runtime. Expired work may yield a later runtime record, but does not add another assignment beyond the planned finite set. Thus the reducer’s CPU-bearing runtime count is bounded by the declared total. The synchronous per-epoch sum uses a subset of that total.

All accepted CPU values are nonnegative. Their mathematical total is at most half the maximum finite float, leaving substantial rounding headroom at the configured maximum term count. Division by 1,000 follows this bounded sum.

Warm validation occurs before `_return_worker()`. Over-envelope CPU therefore faults and removes the suspect worker from reusable circulation before lease return. Cold results use the same bound before publication. The supplied warm extreme-CPU subcase supports rejection and destruction; the cold test explicitly exercises string CPU and negative metrics, rather than a separate cold extreme-CPU fixture.

This is an arithmetic envelope for the declared finite study. It is neither a plausibility threshold for CPU consumption nor a guarantee for arbitrary extra assignments, changed configuration, repeated external `accept()` calls, or unbounded accumulation across runs. No such expanded contract is required here.

**Common cold/warm validation: named bypass corrected, consumed timing gaps remain**

The cold path now calls `validate_worker_result()` before enrichment and return. It consequently rejects the v3 string CPU and negative-metric examples before lifecycle recording. Warm-only reset/version/task-count requirements remain conditional; cold workers do not need to fabricate those metadata fields.

The shared checks cover identity, provenance, status, anchors, window, named metric domains, queue-trace coordinates, final-state validation, required timing fields, CPU envelope, counters, and reported-input consistency. Warm validation and final enriched-size checking remain inside the exclusive lease.

**R4-v4-A — MODERATE: accepted timing fields can still fail downstream reduction**

Two exact triggers remain within the consumed-runtime mechanism.

**Trigger A: cold optional startup timing bypasses validation.**

An otherwise valid cold result contains:

```python
result["runtime"]["worker_startup_ms"] = "bad"
```

`worker_startup_ms` is absent from `required_times` and is checked only when `worker_mode == "warm"`. Cold enrichment preserves the supplied value. The result can therefore be published and recorded with this string.

`experiments/cycle5_async.py::reduce_run()` unconditionally includes `worker_startup_ms` in its timing-distribution loop. `csc/runner.py::distribution()` then attempts subtraction during quantile interpolation. Even a single string sample reaches `"bad" - "bad"` and raises `TypeError`.

Cold startup timing may legitimately be absent. Its optional presence cannot safely bypass validation while the reducer consumes it.

**Trigger B: finite non-CPU timing values overflow the even-sample median.**

Two otherwise valid results contain:

```python
result["runtime"]["hydrate_ms"] = 1e308
```

Both values satisfy the finite, nonnegative timing schema. They do not violate the new CPU envelope. Warm workers can return to circulation after these results pass validation and enrichment.

For a measured runtime cohort containing these two hydration values, the timing reducer calls `statistics.median()`. Its even-sample midpoint calculation adds the values before dividing by two, producing infinity. The resulting report cannot be serialized by `canonical(..., allow_nan=False)`.

This is a separate aggregation operation from the corrected CPU sum. It does not imply that real hydration consumed that time.

**Required correction:** Validate optional consumed timing fields when present, including cold `worker_startup_ms`. Also make accepted timing distributions arithmetically safe—through a defensible pre-release envelope or finite-safe median computation for the accepted domain. Add focused cold optional-field and two-value timing regressions. These corrections do not require a general hostile-worker schema redesign.

**Final-condition cleanup: execution disposition corrected, analysis bypass remains**

`execute()` now assigns `status["status"] = "FAILED"` whenever `unsafe` is set. It writes that changed row before breaking. With no remaining conditions, the final `all(... == "COMPLETE")` expression is false, yielding `HAS_FAILED_OR_UNATTEMPTED_RUNS`.

The final-condition regression supplies exit code zero, no watchdog expiry, and `cleanup.json` containing `null`. It checks both the failed row and noncomplete campaign. The wrong-shape regressions additionally check later conditions becoming `NOT_ATTEMPTED`.

These changes close the exact v3 execution-row and aggregate-verdict counterexample.

**R9-v4-A — MODERATE: analysis can still treat the cleanup-failed final condition as complete**

**Exact trigger:**

1. Earlier conditions complete normally.
2. The final condition has otherwise complete run artifacts, including `summary.json` and a run `manifest.json` with `status="COMPLETE"`.
3. Its ownership confirmation is absent, malformed, or false.
4. Reduction otherwise succeeds.

`execute()` now correctly marks the final execution row `FAILED` and the campaign noncomplete. But `analyze()` does not read `execution_status.json`. `reduce_run()` derives its status from the run manifest alone:

```python
status = "COMPLETE" if manifest["status"] == "COMPLETE" else "FAILED_WITH_SUMMARY"
```

The final condition consequently enters `valid`, contributes to groups and paired effects, and is absent from `failed_or_unattempted_runs`. If every run manifest is complete, that failure list is empty despite the campaign’s cleanup failure. Subsequent `render()`, `document()`, and `figures()` rely on this list for their incomplete-study guards.

This trigger also has an ordinary source path: `run()` can finish and close its run manifest before pressure cleanup fails in `run_one()`. The completed production artifact remains evidence, but it does not establish successful campaign-condition cleanup.

The final-condition test mocks `analyze()` to return `{}`, so it does not test this disposition boundary.

**Required correction:** Propagate execution/ownership failure into the analysis condition disposition. Preserve complete production outputs as qualified observations, while retaining the failed condition in failure accounting and preventing unconditional complete-study output. Add a final-condition regression using the real disposition/reduction path. No measured archive should be rewritten.

**Windows descendant inspection: explicit signaled wait closes the false-pass**

The revised disposable test opens a synchronization handle after the descendant PID is published and before joining the launcher thread. Handle acquisition must succeed. It subsequently requires:

```python
kernel.WaitForSingleObject(handle, 5000) == 0
```

Timeout, `WAIT_FAILED`, and every other nonzero result fail the assertion. The previous “anything except timeout means exited” inference is gone. Holding the acquired handle also avoids relying on a fresh post-cleanup PID lookup.

The test’s intended pre-cleanup ordering uses a one-second PID-publication deadline and a two-second launcher timeout. It does not independently assert a nonsignaled pre-cleanup wait state or synchronize cleanup on successful acquisition. Therefore the strongest supported description is acquisition before the test waits for launcher completion, with explicit exit inspection on that handle. This qualification does not reopen the named failed-wait false-pass or require another correction for it.

The reported Windows gate supports this finite disposable test. It establishes no universal descendant-termination or OS kill guarantee.

**Readiness formats and dependency coverage: named corrections established**

`prepare()` accepts either literal `gate_passed=True` or `status="COMPLETE"`, together with exit code zero. The supplied v4 manifest meets both passing forms. Historical manifests still need matching current source hashes; format acceptance does not authorize old source.

The enforced set now includes all current top-level CSC and test Python files plus:

- `experiments/__init__.py`
- `experiments/cycle5_async.py`
- `experiments/cycle5_pressure.py`
- `experiments/cycle5_loss.py`
- `experiments/replay.py`

The named v3 pressure-helper change before preparation is therefore rejected. The supplied campaign imports and known helper launches reveal no further omitted repository Python helper in this bounded path.

The embedded format regression demonstrates acceptance of a matching `status="COMPLETE"` fixture and rejection when no explicit gate is supplied. It does not independently demonstrate changed-helper rejection or frozen-copy compatibility; those require source reasoning here.

**GATE-v4-A — MODERATE: checked workspace source can differ from copied execution source**

**Exact trigger:**

1. `prepare()` successfully hashes `ROOT/experiments/cycle5_pressure.py` against the gate.
2. That file changes after the verification loop and before its `shutil.copy2()` call.
3. Preparation copies the changed helper into `series/source`.
4. Collection reaches a pressure condition.

The copy loop computes the copied file’s hash and records it in `meta["source_hashes"]`, but never compares that hash with `gate["source_hashes"]`. `execute()` launches the archived campaign from `series/source`, and `run_one()` launches the archived pressure helper. The executed helper can consequently differ from the correctness-gated version.

This is a concrete check-to-copy interleaving, not an allegation that the supplied v4 gate or source actually changed. It directly limits the baseline’s requirement to check frozen collection source against the gate.

**Required correction:** Compare each required copied source hash with the accepted gate before authorizing collection. A mismatch must fail preparation without launching conditions. Add a deterministic changed-between-check-and-copy regression. Merely recording both identities does not establish compatibility.

Preparation still checks historical protocol-path existence rather than establishing a reviewed Cycle 6 protocol. Separate preregistration remains necessary even after source compatibility is corrected.

**Prior narrow closures remain intact**

**R2:** Warm closure, acquisition, and token publication continue to share `lease_condition`. Closure wakes empty-token waiters; acquisition checks closure first and has a finite lease timeout. CPU/schema changes do not alter those orderings. Cold reservations and retained unresolved ownership still constrain creation immediately before `Popen`, including direct `_execute()` calls. Registration-before-reservation-release can conservatively double-count capacity, but does not create an uncounted ownership interval.

**R3:** `BoundedExecutor` still releases capacity upon physical completion or removal during shutdown, rather than cancellation alone. The supplied before/after manifest hashes for `csc/executor.py` agree. This remains a count invariant, not a byte or memory bound.

**R4 utility and quarantine:** `compare.py` retains the maximum-float/4 utility envelope and explicit finite-difference checks. No bounded v4 change undermines the supplied utility/epsilon/regret closure. Invalid production utility still fails accounting rather than establishing successful continuation. Warm validation/enrichment failures still clear the reusable worker reference before destruction; destruction failure retains quarantine and ownership, constraining replacement. The timing defects above limit the completeness of pre-release validation, not that quarantine ordering.

**R9 cleanup:** Post-spawn communication exceptions still enter owned cleanup before ordinary launcher failure propagates. Non-object cleanup JSON still becomes uncertain cleanup rather than a `.get()` exception. These mechanisms retain uncertainty; they do not guarantee successful cleanup under every OS failure.

**R13:** `WarmProcess._read()` still deletes `line` and `value` before the next blocking read on the successful-response path. Its source hash is unchanged across the supplied v4 manifest snapshots. Tracebacks, queues, caches, unresolved workers, and other retained objects remain outside this closure.

**Authority and detailed limits**

No bounded v4 change shown here adds a production actuator capability to shadows. `execute_shadow()` rejects production identity, and accepted nonproduction evidence must retain `ESTIMATED` provenance. Production remains authoritative only within the declared software test environment. Mirrors are same-action estimates; `K` counts distinct alternative actions and excludes mirrors.

The supplied 106-test result and hash checks are reported evidence. The complete test suite and every dependency are not embedded. No unseen coverage, exhaustive schedule exploration, or independent verification is inferred. Gate durations measure test execution, not production cadence, throughput, memory, storage, or evidence yield.

The following empirical findings remain unchanged for the immutable 86-run source:

| Finding | Preserved limitation |
|---|---|
| R1 | Storage failure remains OPEN; correctness changes establish no storage durability. |
| R5 | Positive memory trends, offline full-history allocation, and whole-file hashing remain OPEN; count bounds establish no memory plateau. |
| R6 | Cadence variability remains OPEN; no corrected-source cadence or continuity result exists. |
| R7 | Delayed evidence remains OPEN; late physical completion is not timely complete requested-set evidence. |

This review establishes no hostile containment, resource isolation, universal OS kill success, memory/byte bound, storage durability, sustained liveness, saturation, resource non-interference, or corrected-source performance claim. Finite-safe CPU accounting also does not recover CPU consumed by killed workers without returned telemetry.

**Open questions and next actions**

1. Close R4-v4-A’s two consumed-timing triggers and add focused regressions.
2. Carry cleanup/control failure into analysis and complete-study output guards, preserving qualified production observations and failed-condition accounting.
3. Verify the copied required execution source against the accepted gate before collection.
4. Preserve all existing runs, gates, source snapshots, reviews, and negative controls. These corrections require a new identity and compatible local gate.
5. Separately freeze the Cycle 6 protocol, configuration, execution source, gate, and unique output directory. Predeclare storage-failure accounting, cadence and memory criteria, requested-set evidence yield, and incomplete-run dispositions.
6. Use Cycle 6 to investigate the still-open empirical findings. Do not describe it as confirmation that post-measurement corrections improved performance.

**Decision:** V4 closes the named v3 counterexamples in CPU accounting, cold CPU/metric validation, execution-row/campaign cleanup verdicts, and Windows wait inspection. The remaining exact timing, analysis-disposition, and copied-source compatibility paths prevent a complete correctness-gated recommendation for fresh collection. Resolve those bounded defects before using the implementation as the basis of the separately preregistered finite Cycle 6 study. **Trust D; learning BLOCKED; no deployment approval.**