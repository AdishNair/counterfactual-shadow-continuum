# Cycle 5 continuous asynchronous systems results

**Status:** Locally tested finite preregistered systems pilot. Derived deterministically from archived raw artifacts; deployment validation is absent.

**Question:** Can a bounded local asynchronous runtime maintain production cadence while generating comparable counterfactual evidence during continuous operation?

**Evidence:** `results\cycle5-async\local-20261006-v1\analysis.json`; source/config/protocol/environment archives and per-run artifacts accompany the series. Machine tables: `research/tables/cycle5_runs.json`, `cycle5_groups.json`, `cycle5_warm_cold_paired_effects.json`, `cycle5_runs.csv`, `cycle5_epochs.csv`. See `cycle5_verification.json` for deterministic replay/provenance verdict.

**Method:** 84 factorial runs, 28 cells, three paired seeds; 200 epochs and 20 excluded warmups. Main runs execute sequentially in independently started coordinators using archived source. All nonzero modes retain the same 300 ms evidence deadline, 40 ms pacing target, 3 slots, 12 active-task capacity, mirror-first admission. Long runs separately test 3,000 epochs normal and 1,000 epochs one-slot severe delay. Quantities are descriptive, with three independent seed/run units; epochs are repeated dependent observations.

## Production and evidence by condition

| Mode | Condition | Cadence p50 ms, median over seeds | Run p95 ms, median over seeds | Run p99 ms, median over seeds | Complete fraction median [range] | Raw record-status PARTIAL fraction median | Complete evidence/sec median | Expired branches | Dropped branches |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|
| k0 | normal | 40.398 | 40.637 | 40.878 | unavailable | unavailable | 0.000 | 0 | 0 |
| k0 | cpu | 40.462 | 40.692 | 40.764 | unavailable | unavailable | 0.000 | 0 | 0 |
| k0 | memory | 40.353 | 40.592 | 40.732 | unavailable | unavailable | 0.000 | 0 | 0 |
| k0 | storage | 40.345 | 40.619 | 40.903 | unavailable | unavailable | 0.000 | 0 | 0 |
| cold1 | normal | 40.509 | 40.692 | 42.119 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 732 | 348 |
| cold1 | moderate | 40.463 | 40.628 | 41.091 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 704 | 376 |
| cold1 | severe | 40.393 | 40.619 | 40.857 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 579 | 501 |
| cold1 | cpu | 40.350 | 40.615 | 43.858 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 731 | 349 |
| cold1 | memory | 40.355 | 40.632 | 41.816 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 596 | 484 |
| cold1 | storage | 40.397 | 41.092 | 43.829 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 724 | 356 |
| cold2 | normal | 40.505 | 40.793 | 41.675 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 863 | 757 |
| cold2 | moderate | 40.421 | 40.631 | 43.214 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 565 | 1055 |
| cold2 | severe | 40.345 | 40.628 | 40.797 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 829 | 791 |
| cold2 | cpu | 40.516 | 40.999 | 41.829 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 604 | 1016 |
| cold2 | memory | 40.335 | 40.767 | 44.058 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 616 | 1004 |
| cold2 | storage | 40.392 | 41.458 | 45.995 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 876 | 744 |
| warm1 | normal | 40.395 | 40.638 | 40.723 | 1.000 [1.000,1.000] | 0.000 | 24.616 | 0 | 0 |
| warm1 | moderate | 40.391 | 40.687 | 41.807 | 0.000 [0.000,0.211] | 0.000 | 0.000 | 683 | 300 |
| warm1 | severe | 40.387 | 40.619 | 40.696 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 557 | 523 |
| warm1 | cpu | 40.475 | 40.667 | 46.676 | 1.000 [0.722,1.000] | 0.000 | 24.558 | 89 | 0 |
| warm1 | memory | 40.373 | 40.616 | 40.675 | 1.000 [1.000,1.000] | 0.000 | 24.723 | 0 | 0 |
| warm1 | storage | 40.326 | 40.676 | 42.358 | 1.000 [0.950,1.000] | 0.000 | 24.678 | 7 | 8 |
| warm2 | normal | 40.389 | 40.692 | 42.555 | 0.994 [0.989,0.994] | 0.000 | 24.516 | 0 | 12 |
| warm2 | moderate | 40.337 | 40.748 | 41.882 | 0.000 [0.000,0.117] | 0.000 | 0.000 | 885 | 634 |
| warm2 | severe | 40.358 | 40.621 | 40.708 | 0.000 [0.000,0.000] | 0.000 | 0.000 | 574 | 1046 |
| warm2 | cpu | 40.422 | 40.684 | 40.768 | 0.989 [0.989,0.994] | 0.000 | 24.399 | 0 | 15 |
| warm2 | memory | 40.365 | 40.756 | 43.290 | 0.956 [0.956,0.994] | 0.000 | 23.491 | 20 | 30 |
| warm2 | storage | 40.381 | 45.684 | 67.781 | 0.950 [0.606,0.983] | 0.006 | 22.770 | 171 | 24 |

Production paired hash cardinalities: `[{'seed': 1501, 'production_hashes': 1, 'workload_hashes': 1}, {'seed': 1502, 'production_hashes': 1, 'workload_hashes': 1}, {'seed': 1503, 'production_hashes': 1, 'workload_hashes': 1}]` (one per seed is agreement within this authored software environment). Missing production epochs: 0; failed manifests: 0; observed unauthorized mutations: 0.

Strict 40 ms start-interval overruns and cumulative schedule drift are recorded separately in machine tables. The pacing loop sleeps relative to each preceding start, so drift can accumulate despite stable medians. No externally required hard deadline or equivalence margin was predeclared; interval jitter is not a guarantee of missed real-world actuation.

## Cold versus warm evidence yield

| K | Condition | Paired complete-fraction gains (three seeds) | Paired cadence changes ms (three seeds) |
|---:|---|---|---|
| 1 | normal | [1.0, 1.0, 1.0] | [-89.1972, -0.0912, -0.1633] |
| 1 | moderate | [0.211111, 0.0, 0.0] | [89.4737, -0.11545, 0.0109] |
| 1 | severe | [0.0, 0.0, 0.0] | [-0.07195, -0.00565, 0.0736] |
| 1 | cpu | [0.722222, 1.0, 1.0] | [52.9542, 0.12435, 0.10955] |
| 1 | memory | [1.0, 1.0, 1.0] | [0.04485, -0.0387, 0.04475] |
| 1 | storage | [0.95, 1.0, 1.0] | [-236.4272, -0.0717, -0.0627] |
| 2 | normal | [0.988889, 0.994444, 0.994444] | [-105.7004, 0.09855, -0.15465] |
| 2 | moderate | [0.116667, 0.0, 0.0] | [231.2085, -0.0846, -0.094] |
| 2 | severe | [0.0, 0.0, 0.0] | [-102.9456, 0.0408, -0.01025] |
| 2 | cpu | [0.988889, 0.988889, 0.994444] | [-0.03145, -0.0405, -0.0937] |
| 2 | memory | [0.955556, 0.955556, 0.994444] | [23.9796, 0.0082, 0.0329] |
| 2 | storage | [0.605556, 0.95, 0.983333] | [66.21595, -0.01105, -0.0468] |

Comparison age from production commit includes dispatch, queueing, worker execution, coordinator polling and ordered epoch finalization. Worker-stage distributions and comparison waiting after last accepted branch are retained per run. Accepted branch completion is distinguished from complete requested mirror-plus-alternative epoch evidence and late physical worker returns. K0 has no counterfactual denominator.

## Continuous hot state and archival growth

| Run | Measured epochs | Complete fraction | Cadence median ms | RSS min/end/max MiB | RSS second-half slope KiB/epoch | Python current second-half slope bytes/epoch | Max pending | Max completed retained | Max duplicate cache | Max queue | Archive end MiB |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| long-normal | 2980 | 0.999 | 40.365 | 34.777/37.816/37.816 | 0.3317714989981809 | 23.438241142466012 | 8 | 64 | 64 | 9 | 125.18589115142822 |
| long-saturation | 980 | 0.000 | 40.378 | 34.043/35.562/35.562 | 0.24066174743734536 | 186.1444155816338 | 8 | 64 | 64 | 11 | 15.321456909179688 |

Full-state OLS slopes per epoch/per second, second-half slopes, first/last-quarter means, worker counts/RSS, handles and every 100 epoch evidence/loss fraction remain in JSON. RSS is instantaneous working set on Windows, not an exclusive allocation ownership measure. Python current and peak are distinct. Online hot history is count bounded; append-only archived research evidence grows. Full-run exact summary generation occurs after production stops and loads the run history; its RSS/time are a separate offline limitation, not a continuously retained production structure.

## Resource pressure and graceful degradation

| Mode | Load | Paired cadence change from normal ms (three seeds) | Requested K median | Admitted K median across runs | Completed K median across runs | Median complete age ms |
|---|---|---|---:|---:|---:|---:|
| k0 | normal | [0.0, 0.0, 0.0] | 0.0 | 0.0 | 0.0 | unavailable |
| k0 | cpu | [48.0185, 0.0635, 0.1104] | 0.0 | 0.0 | 0.0 | unavailable |
| k0 | memory | [-0.0661, -0.0453, 0.01685] | 0.0 | 0.0 | 0.0 | unavailable |
| k0 | storage | [-0.05335, -0.05295, 0.02695] | 0.0 | 0.0 | 0.0 | unavailable |
| cold1 | normal | [0.0, 0.0, 0.0] | 1.0 | 0.0 | 0.0 | unavailable |
| cold1 | moderate | [72.25155, -0.04505, -0.1295] | 1.0 | 0.0 | 0.0 | unavailable |
| cold1 | severe | [-89.1736, -0.11565, -0.1701] | 1.0 | 0.0 | 0.0 | unavailable |
| cold1 | cpu | [67.6342, -0.15805, -0.17415] | 1.0 | 0.0 | 0.0 | unavailable |
| cold1 | memory | [-89.2166, -0.15295, -0.18105] | 1.0 | 0.0 | 0.0 | unavailable |
| cold1 | storage | [147.2676, -0.11115, -0.13485] | 1.0 | 0.0 | 0.0 | unavailable |
| cold2 | normal | [0.0, 0.0, 0.0] | 2.0 | 0.0 | 0.0 | unavailable |
| cold2 | moderate | [-105.70785, 0.08255, -0.0833] | 2.0 | 0.0 | 0.0 | unavailable |
| cold2 | severe | [-2.73435, -0.0218, -0.15975] | 2.0 | 0.0 | 0.0 | unavailable |
| cold2 | cpu | [-105.68065, 0.179, 0.01095] | 2.0 | 0.0 | 0.0 | unavailable |
| cold2 | memory | [-105.6999, -0.00425, -0.17245] | 2.0 | 0.0 | 0.0 | unavailable |
| cold2 | storage | [79.63905, 0.0537, -0.123] | 2.0 | 0.0 | 0.0 | unavailable |
| warm1 | normal | [0.0, 0.0, 0.0] | 1.0 | 1.0 | 1.0 | 41.63009999319911 |
| warm1 | moderate | [250.92245, -0.0693, 0.0447] | 1.0 | 0.0 | 0.0 | 285.56290004053153 |
| warm1 | severe | [-0.04835, -0.0301, 0.0668] | 1.0 | 0.0 | 0.0 | unavailable |
| warm1 | cpu | [209.7856, 0.0575, 0.0987] | 1.0 | 1.0 | 1.0 | 41.6925499739591 |
| warm1 | memory | [0.02545, -0.10045, 0.027] | 1.0 | 1.0 | 1.0 | 41.61044998909347 |
| warm1 | storage | [0.0376, -0.09165, -0.03425] | 1.0 | 1.0 | 1.0 | 42.38764999900013 |
| warm2 | normal | [0.0, 0.0, 0.0] | 2.0 | 2.0 | 2.0 | 42.140699981246144 |
| warm2 | moderate | [231.20105, -0.1006, -0.02265] | 2.0 | 0.0 | 0.0 | 288.8231999822892 |
| warm2 | severe | [0.02045, -0.07955, -0.01535] | 2.0 | 0.0 | 0.0 | unavailable |
| warm2 | cpu | [-0.0117, 0.03995, 0.0719] | 2.0 | 2.0 | 2.0 | 42.20329999225214 |
| warm2 | memory | [23.9801, -0.0946, 0.0151] | 2.0 | 2.0 | 2.0 | 42.0814499957487 |
| warm2 | storage | [251.5554, -0.0559, -0.01515] | 2.0 | 2.0 | 2.0 | 43.00619999412447 |

Achieved cpu pressure (15runs): median0.942, range[0.299,0.984] CPU seconds per wall second. Full process liveness/intensity logs are immutable. This deliberately safe pressure does not establish host saturation or isolation.

Achieved memory pressure (15runs): median133.911, range[72.433,146.095] full 64 MiB page-touch rounds per second. Full process liveness/intensity logs are immutable. This deliberately safe pressure does not establish host saturation or isolation.

Achieved storage pressure (15runs): median411.927, range[89.523,474.827] MiB written per second through Python flushed rewrites. Full process liveness/intensity logs are immutable. This deliberately safe pressure does not establish host saturation or isolation.

Total CPU efficiency unavailable (null): observed coordinator + accepted/late worker CPU excludes killed/expired workers without output; Windows CPU quantization. Components retained separately.

Serialized complete CFR bytes/record and observed transport bytes/complete record have separate units/denominators. Per-worker-slot evidence is not unique-process efficiency; launch/recycle counts identify warm reuse.

## Findings, limitations and next actions

The tables preserve zero-coverage conditions, all paired effects, requested-versus-admitted work, expiry/drops, evidence time and bounded-state trends. Classification against high/moderate/low thirds is descriptive only. Cycle4 provides historical context: its different short runs and whole-batch admission cannot serve as an isolated worker-reuse control. The concurrent Cycle5 cold modes provide that control.

10,000 consecutive epochs at >=90% completeness not evaluated by this 200-epoch factorial / 3000-epoch longest pilot

linear-interpolated per-run p50/p95/p99; 180 measured epochs gives <2 observations in p99 tail; tail descriptive

Limits: cooperative Windows processes; synthetic authored traffic; one host; three main seeds; bounded gentle contention; no hostile-container or Kubernetes isolation; no physical traffic ground truth; no hard real-time guarantee; no universal K scaling beyond two meaningful alternatives. Finite memory slopes and count caps cannot prove all future execution bounded without archival quota/rotation. Review may identify further limitations.

Open questions/next actions: independently challenge warm reset and lifecycle evidence; evaluate positive RSS slopes versus allocator behavior; audit narrow operating cells with fresh preregistered longer runs, stronger controlled contention and startup/backpressure telemetry before expanding domain or infrastructure claims. Trust remains Decision D; learning remains BLOCKED; no selector retuned.

## Postcollection measurement clarifications

**Status:** Independently hashed deterministic derived supplement; frozen source, raw outcomes and original analysis remain unchanged. Supplement identity: `experiments/cycle5_compact.py` / `research/tables/cycle5_reviewer_brief.json`. No deadline, cohort, threshold or duration changed.

The frozen partial-fraction field counts raw `record_status == PARTIAL`. That label omits some mirror-only/alternative-only evidence. The following semantic partial measure counts epochs with any accepted comparable nonproduction branch but without the full originally requested mirror-plus-K set. Both measures remain visible; complete-epoch completeness is unchanged.

| Mode | Condition | Any accepted but incomplete requested-set evidence (seeds 1501, 1502, 1503) |
|---|---|---|
| cold1 | normal | 0.000000, 0.000000, 0.000000 |
| cold1 | moderate | 0.000000, 0.000000, 0.000000 |
| cold1 | severe | 0.000000, 0.000000, 0.000000 |
| cold1 | cpu | 0.000000, 0.000000, 0.000000 |
| cold1 | memory | 0.000000, 0.000000, 0.000000 |
| cold1 | storage | 0.000000, 0.000000, 0.000000 |
| cold2 | normal | 0.000000, 0.000000, 0.000000 |
| cold2 | moderate | 0.000000, 0.000000, 0.000000 |
| cold2 | severe | 0.000000, 0.000000, 0.000000 |
| cold2 | cpu | 0.000000, 0.000000, 0.000000 |
| cold2 | memory | 0.000000, 0.000000, 0.000000 |
| cold2 | storage | 0.000000, 0.000000, 0.000000 |
| warm1 | normal | 0.000000, 0.000000, 0.000000 |
| warm1 | moderate | 0.116667, 0.000000, 0.000000 |
| warm1 | severe | 0.000000, 0.000000, 0.000000 |
| warm1 | cpu | 0.061111, 0.000000, 0.000000 |
| warm1 | memory | 0.000000, 0.000000, 0.000000 |
| warm1 | storage | 0.016667, 0.000000, 0.000000 |
| warm2 | normal | 0.000000, 0.000000, 0.000000 |
| warm2 | moderate | 0.155556, 0.000000, 0.000000 |
| warm2 | severe | 0.000000, 0.000000, 0.000000 |
| warm2 | cpu | 0.000000, 0.000000, 0.000000 |
| warm2 | memory | 0.000000, 0.005556, 0.000000 |
| warm2 | storage | 0.172222, 0.005556, 0.000000 |

Frozen resource trend tables exclude the first 20 warmups. The preregistered online-state estimand includes all epochs; the independently hashed supplement below restores that all-epoch estimand, while retaining frozen estimates. All-state plots already include all epochs.

| Run | All online epochs | RSS maximum MiB | RSS all-epoch slope bytes/epoch | RSS second-half slope bytes/epoch | Python current all-epoch slope bytes/epoch | Python current second-half slope bytes/epoch |
|---|---:|---:|---:|---:|---:|---:|
| long-1510-warm2-long-normal | 3000 | 37.816406 | 559.572129 | 339.915183 | 94.414899 | 23.340010 |
| long-1511-warm2-long-saturation | 1000 | 35.562500 | 766.557836 | 265.008787 | 234.603082 | 191.496683 |

Positive finite-duration slopes do not establish an indefinitely stable memory plateau. Structural count caps, small observed RSS ranges, Python allocations and archival growth are separate findings. Main source-archive identity: `9e473658ebd91e004e9caa9bb02971e95db98e22b76771bc45b7e9dd783b4cba`; gate source identity: `8b0f3c5ba078379cc32c5dea4f8c80eb6802df4d3941b36f3a1fb66bca1f2e03`; exact CSC subclosure match: `True`.

Figure caption clarification: K excludes the mirror from the alternative count. Complete evidence in every coverage figure requires the mirror and all K requested alternatives; the words "mirror excluded" in the frozen plot title refer only to K counting. The run-order figure exposes heterogeneous early timing; no fitted correction or selective exclusion is applied.

## Evidence age and offline reduction details

The exact seed distributions and per-action exposure counts remain in the reviewer packet; means cannot replace requested-set completeness.

| Normal mode | Complete evidence-age medians by seed (ms) |
|---|---|
| warm1 | 43.137900, 41.585250, 41.630100 |
| warm2 | 42.277550, 42.140700, 42.067900 |

| Long run | Complete / measured requested epochs | Complete age p95 / p99 ms | Offline summary RSS MiB | Requested / expired / dropped branches |
|---|---|---|---:|---|
| long-1510-warm2-long-normal | 2978 / 2980 | 126.14812500250991 / 165.76785797427874 | 488.429688 | 8940 / 1 / 3 |
| long-1511-warm2-long-saturation | 0 / 980 | None / None | 94.582031 | 2940 / 1207 / 1733 |

Offline summary RSS is measured after the live production loop and after full history is loaded for exact reduction. It materially exceeds hot runtime RSS in the long normal run; bounded hot state is not a claim that end-of-run reduction or archival storage stays bounded.

## Independent review and subsequent source boundary

The original independent review, `research/evidence/cycle5/cycle5_red_team_review.md`, found no established CRITICAL authority breach and seven MAJOR findings for the frozen measured source. They cover storage availability/partial persistence, transport/shutdown, cancelled physical queue accumulation, validation before reuse, memory/offline costs, production cadence and pressure-dependent evidence yield. All remain part of the measured-source assessment. Finite retained ledger counts cannot establish physical queue or byte bounds, and identical production trajectory hashes cannot establish timing equivalence.

The first post-measurement correction passed 80 tests but independent `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview.md` identified further cleanup/creation and validation-after-release defects. That review narrowly supports the cancelled physical-count fix and successful-response reader-local clearing. A separate v2 correction passed 96 tests in 28.181 seconds at `results/cycle5-validation/post-review-hardening-20261006-v2/`, including real Windows cleanup, creation/shutdown races, cleanup-error quarantine, malformed/runtime/overflow/body checks, and generic distinct-choice K=5 accounting. The synthetic accounting test introduces no traffic K>2 claim. Source identity and negative controls remain in that immutable validation archive.

Final independent v2 re-review is separate from the measurement review. These correctness tests and fixes do not change any archived main completeness, cadence, memory, storage or replay result. No corrected-source performance campaign was run. Storage availability, positive memory trends, variable cadence and zero-yield delayed conditions still determine the next systems study; trust remains Decision D and learning remains BLOCKED.

Subsequent independent v3 review confirmed narrow closure of the warm lease-shutdown and unresolved-cold-capacity mechanisms, while finding bounded downstream CPU, cold-validation, final-cleanup-disposition and gate-compatibility gaps. The final v4 correction passed 106 tests in 28.399 seconds at `results/cycle5-validation/post-review-hardening-20261006-v4/`; preserved v3 negative controls reproduce each corrected path. Its full source identity is `f492d4de5e959702358740ecb1d73f580e674d63234ae3a363dabd2e4f0b25fb`. Final v4 independent judgment is recorded separately and cannot upgrade the immutable performance study.

The v4 review found three further bounded timing/analysis/source-copy paths. Final v5 passed 108 tests in 28.362 seconds at `results/cycle5-validation/post-review-hardening-20261006-v5/`. Independent v5 review found no remaining CRITICAL, MAJOR or MODERATE issue in that bounded correction scope and retained one MINOR integration-test limitation. It judges v5 suitable only as the correctness-gated basis for a separately preregistered finite study. This disposition does not change any result above or close measured-source R1/R5/R6/R7.


## Final closure interpretation

The immutable 86-run archive is the sole source of all performance claims in this report. Its source identity is `9e473658ebd91e004e9caa9bb02971e95db98e22b76771bc45b7e9dd783b4cba`; verified delivery found all scheduled runs, exact factor coverage, and valid required provenance artifacts. No performance run was repeated.

Post-collection v1-v5 work repaired source-level lifecycle, validation, timing, cleanup, analysis, and provenance defects. The final v5 gate (`results/cycle5-validation/post-review-hardening-20261006-v5/`) passed 108 tests in 28.362 seconds, and its independent judgment found no CRITICAL, MAJOR, or MODERATE defect in that bounded scope. That evidence applies only to the current code. It cannot improve the archive's measured cadence, evidence yield, memory, storage, resource, or failure estimates.

Final classification: **CRITICAL none; MAJOR none blocking a separately preregistered Cycle 6 start; MODERATE** storage isolation, physical queue/byte accounting, memory plateau, cadence robustness, delay-yield collapse, host/measurement/verifier/duration limits; **MINOR** one v5 hydration/cleanup integration-coverage gap. The archive preserves its negative findings: delay collapses coverage, positive RSS/Python slopes prevent a bounded-memory claim, storage failure can abort production, and broad graceful degradation is not established. Trust remains Decision D and learning remains BLOCKED.
