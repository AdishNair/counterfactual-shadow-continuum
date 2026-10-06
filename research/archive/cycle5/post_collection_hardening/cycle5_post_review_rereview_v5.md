**CSC Cycle 5: post-measurement v5 systems re-review**

**Artifact:** `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v5.md`

**Status:** Independent static review of the embedded packet, 2026-10-06. Returned as complete Markdown text; no tools, delegation, file edits, tests, experiments, or independent hash verification performed. V5 is **implemented and reportedly locally tested**, not deployment-validated.

V5 narrowly closes the three MODERATE implementation findings in `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v4.md`: consumed timing arithmetic and optional cold startup validation, analysis disposition for cleanup-failed complete artifacts, and compatibility between gated source and copied execution source. No remaining material trigger is established within these three reviewed paths. One **MINOR, nonblocking regression-coverage limitation** remains.

**Fresh-study decision:** V5 is locally adequate as the correctness-gated implementation basis for a **separately preregistered finite local warm/cold Cycle 6 systems study**, within the qualifications below. This is not evidence of corrected-source performance or approval of an existing Cycle 6 protocol.

**Trust remains D; learning remains BLOCKED.**

**Question**

Do the embedded v5 changes close the three exact v4 findings while preserving the prior narrow R2, R3, R4 utility/quarantine, R9, and R13 closures, without upgrading the immutable measured study’s empirical findings?

**Evidence identities and variant boundaries**

All identities and execution results below are supplied evidence.

| Variant | Reported evidence and identity |
|---|---|
| Immutable measured study | **86 runs**, unchanged and not rerun. Its aggregate source identity is not supplied. No correction identity is substituted for it. |
| Historical precollection gate | **66 tests**; separate historical variant. Exact identity and duration are not supplied. |
| v1 correction | **80 tests in 30.089 seconds**; source identity `12f8d30d9bc2628cb89b5ef918d4628552d5302fb8eb77de64443c34dfc67b77`. |
| v2 correction | **96 tests in 28.181 seconds**; manifest elapsed time **28.66800800000783 seconds**; source identity `b4d08f39e99aa5a26bcba89e4d7d4e41a1a76c3f007aaba41bc03efc60334b41`. |
| v3 correction | **103 tests in 39.450 seconds**; manifest elapsed time **40.059593600046355 seconds**; source identity `beceb6ad110922758e01377090d296571307cbcfa4ea812288d7799609d930de`. |
| v4 correction | **106 tests in 28.399 seconds**; manifest elapsed time **28.838843000005 seconds**; full source identity `f492d4de5e959702358740ecb1d73f580e674d63234ae3a363dabd2e4f0b25fb`; CSC identity `ce965b67e6f1361dfabc34be33b3abab56a5e6b1d95fe8aaeb5c5eeaf360d566`. |
| v5 gate | `results/cycle5-validation/post-review-hardening-20261006-v5/`; **108 tests in 28.362 seconds**, exit code 0, `gate_passed=true`, manifest status `COMPLETE`. Manifest elapsed time is separately **28.767470599967055 seconds**. |
| v5 full source identity | `c3e81bb6c4148f9b899970b5e71fe8a8b77226ba862ff3b7d1fd0f767cdda4be` |
| v5 CSC source identity | `ee51a6bf9f72a003844e73566ba3840b228074fe7432a3c17e5799f070039fb5` |
| v5 manifest hash | `5e0c0a051d5fcf7698a959a47576d111cf88abe6b0e815044ba3b1c489e177f1`, reported in `research/tables/cycle5_post_review_hardening_v5.json`. |
| Archived v5 validation script | `experiments/cycle5_hardening_v5_validation.py`; hash `f9ce2359d5c28522e097bc77d28b34da14a373aa00dc10768c7aab4ec5348362`, recorded as the manifest’s `analysis_script_identity_sha256`. |
| Separately reported analysis script | Hash `3abb16a9e02404bde9851cdf81c14b8eacfbae8c4c696d0c9c46df3386eed377` in the machine table. This is distinct from the archived validation script and is not substituted for its executed identity. |

The principal changed sources have these reported v5 hashes:

| Source | SHA-256 |
|---|---|
| `csc/branches.py` | `848e1a78733876e31c7099759fcae17984699e39c8396174cf3868d15e5b43ed` |
| `experiments/cycle5_async.py` | `92feca26906e6e99342f6c83c5557589c74129d4338fe524616a409b15729a28` |
| `tests/test_cycle5_hardening.py` | `ede320f85d4b4fecc87794d888fe05992e81b285cff8b93a903d4705730a82ea` |
| `tests/test_cycle5_campaign_cleanup.py` | `7d56aa1a5a0b34674f1f5653cb364876a9f112fac4556b439870b0b57e3b697f` |

The manifest reports Windows 11 and Python 3.14.7, with `source_changed_during_gate=[]`. The machine table reports empty broken-artifact and subsequent runtime/other-source change lists. Its before/after snapshots distinguish correction variants; they are not evidence that the runtime changed during the passing gate.

The correction account is `research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v5.md`. The review baseline is `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v4.md`. The embedded `unittest.log` supplies the 108-test result. **No corrected-source performance run exists.**

**Method**

Trace each v4 counterexample through the embedded validation, lease return, lifecycle recording, reduction, execution disposition, analysis selection, and preparation paths. Distinguish source-established behavior from the narrower assertions exercised by the embedded regressions. Retain prior qualified closures unless the bounded changes provide a concrete reason to reopen them.

No failure frequency, unseen coverage, independent identity verification, or research measurement is inferred. Arithmetic reasoning below concerns the supplied acceptance envelope, not observed timing plausibility.

**Dispositions**

| Finding | v5 disposition |
|---|---|
| R4-v4-A — optional cold startup and timing median overflow | **Narrowly closed** for the named consumed timing fields and reduction operations. |
| R9-v4-A — cleanup-failed complete artifacts enter complete-run analysis | **Narrowly closed** on the supplied campaign execution-to-analysis path. |
| GATE-v4-A — checked workspace source differs from copied execution source | **Narrowly closed** for the named check-to-copy interleaving. |
| R2 — warm lease shutdown and unresolved cold capacity | **Prior narrow closures retained.** |
| R3 — cancelled physical backlog | **Prior physical-count closure retained.** |
| R4 — utility arithmetic, CPU aggregation, validation/quarantine ordering | **Prior narrow closures retained.** |
| R9 — launcher cleanup, malformed confirmation, final campaign verdict, Windows wait inspection | **Prior narrow closures retained.** |
| R13 — successful-response reader locals | **Prior narrow closure retained.** |
| V5-T1 — focused regression coverage | **MINOR, nonblocking.** The embedded tests cover less integration than requested in v4. |
| R1, R5, R6, R7 | **MAJOR / OPEN for the immutable measured source**, unchanged. |

R8, R10, R11, R12, R14, and R15 retain their prior qualified dispositions without reassessment or upgrade. No new CRITICAL, MAJOR, or MODERATE finding is established within this review’s scope.

**R4-v4-A: optional cold startup and timing arithmetic**

The cold optional-field trigger is closed in `csc/branches.py::validate_worker_result()`.

An otherwise valid cold result with `runtime["worker_startup_ms"]="bad"` now reaches the presence-based startup check. Its type fails independently of `worker_mode`. On the cold path, validation occurs after decoding and before enrichment, status publication, and return. `_execute()` converts the validation exception into a coordinator-created `FAULTED` envelope; the rejected startup value does not enter lifecycle timing distributions.

Cold startup remains optional. If absent, the validator permits absence, and `reduce_run()` supplies `None` through `r.get(name)`; the campaign distribution wrapper filters it out. Warm startup and reset metadata remain required under the separate warm-only condition.

The non-CPU timing-overflow trigger is also closed. Required timings and optional startup, when present, must be finite, nonnegative numbers no greater than:

```python
sys.float_info.max / 4
```

Consequently, the v4 `hydrate_ms=1e308` example is rejected. The validator also requires hydration not to exceed execution time and model completion not to precede worker start.

For accepted values in this nonnegative envelope, the two central samples used by the baseline’s even-sample median add to at most half the maximum finite float. The identified addition-before-division overflow therefore cannot recur. Ordered interpolation differences remain within the envelope, with ample arithmetic headroom. This establishes safety for the named distribution operations; it does not establish a bound for arbitrary sums or products added later.

The worker-controlled timing fields consumed by the campaign timing loop are covered: startup, launch-to-entry, hydration, and execution. Queue wait, dispatch roundtrip, and transport overhead are assigned by coordinator enrichment. They are not preserved arbitrary worker values on this path.

Warm validation and enriched-size checking still occur before `_return_worker()`. Rejection clears the reusable worker reference before destruction is attempted. Thus the extreme hydration example cannot return its suspect worker to circulation.

The CPU aggregation envelope remains separately enforced using the declared finite assignment count. The new timing envelope only narrows acceptance; it does not remove the v4 CPU accumulation bound.

This closure concerns finite arithmetic and publication ordering. It establishes neither realistic timing telemetry nor improved cadence or evidence yield.

**R9-v4-A: cleanup failure now reaches analysis disposition**

The ordinary triggering path remains reachable: `run()` can finish its production artifacts before `run_one()` fails during pressure cleanup. Complete production artifacts and unsuccessful campaign-condition cleanup can therefore coexist.

V5 now handles that combination through the following path:

1. `execute()` obtains a nonzero launcher result or an absent, malformed, or false ownership confirmation.
2. It sets the execution row to `FAILED`, records `unsafe_to_continue`, and writes the changed row to `execution_status.json` before leaving the loop.
3. `analyze()` reduces the run artifacts, then reads execution statuses and finds the failed row by `run_id`.
4. It preserves the reducer’s prior status as `artifact_status`, sets the condition status to `FAILED_CONTROL_OR_CLEANUP`, and retains the execution disposition.
5. Its `valid` list excludes that condition; its failure list includes it.

This applies to the final condition even when all earlier conditions completed normally. The campaign manifest also remains noncomplete because the final execution row is failed.

Production observations, hashes, and reduced measurements remain in the run result as qualified evidence. A cleanup failure does not fabricate a production failure: the separate artifact and execution dispositions retain that distinction.

Completed groups and their reference populations use `valid`; failed conditions cannot supply either side of the warm/cold paired effects. Missing pairs receive `UNAVAILABLE_FAILED_PAIR`. The nonempty failure list causes `render()` to issue its failure notice, `document()` to produce the incomplete-study document, and `figures()` to reject complete-study figures.

This closes the exact v4 analysis bypass when reduction succeeds, as stipulated by that finding. It does not establish general recovery from damaged artifacts, a missing execution-status file, or interruption before failure disposition is persisted. Those broader guarantees are not inferred, and no additional material trigger within the named path is established.

**GATE-v4-A: copied source is compared with the accepted gate**

`prepare()` retains its explicit passing-gate requirement, required-source coverage check, and workspace hash comparison. After copying, it now compares every required file’s recorded destination hash with the accepted gate:

```python
copied_mismatches = [
    name for name in required
    if hashes.get(name) != gate["source_hashes"].get(name)
]
```

For the exact v4 interleaving, the workspace pressure helper passes the initial check, changes before copying, and produces a different destination hash. The new comparison raises `RuntimeError` before preparation writes successful preregistration metadata or returns.

`execute()` calls `prepare()` before entering its launch loop and does not convert this preparation failure into permission to collect. No condition launches through that path. A partially populated new directory may remain; it is not a successfully prepared campaign.

The required set still includes current top-level CSC and test Python files and the named campaign, pressure, loss, replay, and package helpers. A required file skipped because it disappeared also lacks a matching copied hash and fails the comparison.

The deterministic regression changes the destination pressure helper inside the patched copy operation. The subsequent destination hash differs, and preparation must reject it. This exercises the pertinent copied-byte mismatch without relying on scheduling luck.

The implementation hashes destinations during copying and compares those recorded hashes after the copy loop. This closes the named checked-versus-copied mismatch. It does not make the archive immutable against later modification or establish hostile filesystem containment.

Both supplied passing-gate formats remain supported, subject to source compatibility. Historical protocol-file existence checks still do not establish an independently reviewed Cycle 6 preregistration.

**V5-T1 — MINOR: regression coverage is narrower than the v4 request**

The supplied tests support the corrections, but two coverage qualifications remain:

- The hydration subcase injects one extreme result and asserts rejection and worker removal. It does not exercise a two-value timing distribution through real reduction. It also violates the new hydration/execution relationship, so its general rejection assertion does not independently isolate the arithmetic-envelope rule.
- `test_analysis_excludes_cleanup_failed_complete_artifact()` runs real `analyze()` disposition and selection logic but mocks `reduce_run()`. The final-condition execution test still mocks `analyze()`. No embedded test combines final-condition execution failure, real artifact reduction, and downstream output guards.

These are exact limitations of the shown fixtures. They do not demonstrate a surviving material implementation defect: the acceptance bound and execution-to-analysis path can be traced directly in the supplied source. They therefore do not reopen the three MODERATE findings or block the bounded fresh-study decision.

When extending these regressions, add a distribution-boundary case and a complete-artifact cleanup-failure integration case. Any test/source revision requires its own compatible gate; no unseen test coverage is credited to the current 108-test result.

**Prior narrow closures remain intact**

**R2:** Warm acquisition, closure, and token publication continue to share `lease_condition`. Closure wakes waiters, acquisition checks closure first, and lease waiting has a finite timeout. Cold capacity still includes constructing and unresolved owned processes immediately before spawning. The timing changes do not weaken these orderings.

**R3:** Cancellation alone does not release physical executor capacity. Capacity is released after physical consumption or removal during shutdown. This remains a task-count invariant, not a byte or memory bound.

**R4 utility and quarantine:** `compare.py` retains the maximum-float/4 utility envelope and explicit finite-difference checks. Invalid production utility does not establish successful continued accounting. Warm validation/enrichment failure clears the reusable reference before destruction; failed destruction retains quarantine and ownership, constraining replacement. The CPU closure remains limited to the declared finite runner contract.

**R9:** Post-spawn communication failures still enter owned cleanup before ordinary launcher failure propagates. Non-object confirmation JSON remains uncertain cleanup. Unsafe final conditions still produce failed execution rows and noncomplete campaign verdicts. The Windows disposable test still requires successful handle acquisition and an explicit signaled wait result of zero; `WAIT_FAILED` cannot pass. Its pre-cleanup synchronization qualification from v4 remains unchanged. None of these mechanisms guarantees OS cleanup success.

**R13:** `WarmProcess._read()` still deletes `line` and `value` before the next blocking read on its successful-response path. This remains a reader-local closure; retained queues, tracebacks, caches, and unresolved ownership are outside it.

**Preserved negative evidence**

The v5 packet attributes these controls to archived **v4**, not v5:

| Control | Reported archived-v4 result |
|---|---|
| Timing arithmetic | Extreme hydration accepted as `REPORTED`, worker returned, median nonfinite. |
| Cold optional startup | String startup accepted as `REPORTED`. |
| Analysis disposition | Cleanup-failed condition reported `COMPLETE`, with zero failed conditions. |
| Copy compatibility | Altered copied pressure helper accepted. |

The v4 review’s archived-v3 CPU, cold-validation, final-cleanup, and gate-format controls retain their attribution. The gate-format result remains fail-closed incompatibility. Historical v2 CPU, utility-difference, warm-lease-shutdown, and cold-capacity controls, and earlier malformed-runtime, quarantine, mirror-divergence, and enrichment-size controls, remain negative evidence for their original variants.

These probes establish mechanisms, not their occurrence rates in the immutable 86-run study.

**Authority, empirical findings, and limits**

No reviewed v5 change adds a production actuator capability to shadows. `execute_shadow()` rejects production identity, and accepted nonproduction outcomes require `ESTIMATED` provenance. Production remains authoritative only within the declared software test environment. Mirrors remain non-actuating same-action estimates; `K` counts distinct alternative actions and excludes mirrors.

| Immutable measured-study finding | Unchanged disposition |
|---|---|
| R1 — storage failure | **MAJOR / OPEN.** No storage-durability result follows from these corrections. |
| R5 — positive memory trends and offline allocation | **MAJOR / OPEN.** Full-history allocation and whole-file hashing remain limitations; count bounds do not establish a memory plateau. |
| R6 — cadence variability | **MAJOR / OPEN.** No corrected-source cadence or continuity measurement exists. |
| R7 — delayed evidence | **MAJOR / OPEN.** Late physical completion is not timely complete requested-set evidence. |

The 108-test gate is supplied local correctness evidence, not reviewer execution. Its duration measures test execution, not production performance. The full suite and every dependency are not embedded; exhaustive schedules and unseen coverage are not inferred.

This review establishes no hostile containment, resource isolation, universal OS termination guarantee, memory plateau, byte bound, storage durability, sustained liveness, host saturation, deployment validation, or corrected-source performance improvement. CPU accounting still excludes killed workers that return no telemetry.

**Open questions and next actions**

1. Preserve all measured runs, historical correction variants, gates, negative controls, and reviews without rewriting them.
2. Separately preregister Cycle 6’s finite question, configurations, warm/cold comparisons, environment, duration, stopping rules, and unique output directory.
3. Freeze the collection source and compatible correctness gate. Source changes for Cycle 6 require a new compatible gate.
4. Predeclare storage-failure accounting, cadence criteria, memory and offline-allocation measurements, requested-set evidence yield, and cleanup/control-failure dispositions. Preserve failed units and qualified production observations without substitution.
5. Address the MINOR regression-coverage limitation when extending the relevant tests. No additional implementation correction is required by an established material trigger in this bounded review.
6. Use Cycle 6 to investigate the open empirical findings. Do not describe collection as confirmation that post-measurement corrections improved performance.

**Decision**

V5 closes the three exact v4 MODERATE implementation findings on the supplied paths and preserves the prior narrow closures. It is **locally adequate as a correctness-gated implementation basis for a separately preregistered finite Cycle 6 systems study**. The regression-coverage limitation is nonblocking. The immutable measured study’s R1, R5, R6, and R7 findings remain open. **Trust D; learning BLOCKED; no deployment approval.**