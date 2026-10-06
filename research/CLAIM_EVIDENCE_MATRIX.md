# CSC evidence-to-claim matrix

**Status:** Cycle 4 reviewed synthesis plus Cycle 5 implementation/local gates;
main performance/provenance verified and independent review complete,
2026-10-06. This matrix distinguishes
local software evidence from deployment or physical validation. Historical
evidence remains immutable; reviewed Cycle 4 findings are scoped below.

| Claim | Status | Evidence | Confidence | Limitation | What would upgrade it |
|---|---|---|---|---|---|
| Branches start from equivalent captured state | ESTABLISHED LOCALLY | `tests/test_core.py`; historical matrix replay | Moderate within validated schema | Capture excludes external unmodeled state | Versioned adapter and deployed capture validation |
| Same supplied inputs are replayed | ESTABLISHED LOCALLY | `experiments/replay.py`; `results/matrix/replay-verification.json` | High for recorded local traces | Supplied exogenous futures are not generally known online | Live-input synchronization and availability study |
| Shadows cannot actuate at application boundary | ESTABLISHED LOCALLY | Gateway/identity tests in `tests/test_core.py` and `tests/test_failures.py` | Moderate | Cooperative local software; no hostile OS containment | Policy-enforcing adversarial deployment tests |
| Shadow failures preserve logical production trajectory | ESTABLISHED LOCALLY | Cycle 4 162 runs; paired seed production/workload hashes and replay | Moderate within tested configuration | Selected faults; malformed numeric guard subsequently fixed outside archive | Longer independent fault campaign and storage interruption |
| Async production does not await shadow completion | ESTABLISHED LOCALLY | `csc/pending.py`; next-epoch test; `red_team_cycle4_review.md` | Moderate/high within finite cooperative loop | Post-loop shutdown joins; coordinator storage/comparison still costs time | Continuous run with bounded history and independently timed path |
| Local cadence under slow shadows | PARTIALLY SUPPORTED | Five seed-pairs per condition; `tables/cycle4_async_tables.md` | Moderate descriptive local | No equivalence margin; mostly dropped/expired evidence; 40 ms pacing | Useful evidence yield and controlled contention at declared load |
| Mirror reproduces production uniformly | NOT ESTABLISHED | Confirmatory factorial and Cycle 3 failure analysis | Moderate for bounded rejection | Model mismatch and horizon dependence | New justified calibrated model with fresh validation |
| Alternative counterfactual trust | NOT ESTABLISHED | Decision D; `research/evidence/cycle1/reference_fidelity_analysis.md` | Moderate for failed tested gate | Authored-software outcomes, not physical futures | Independently validated useful prospective reliability |
| Divergence/horizon selector usefulness | NOT ESTABLISHED | Cycle 4 calibration: no qualifying rule; final not generated | Moderate for gate rejection; none for held-out utility | Structural abstention conflict, shuffled control comparable, epsilon post-window | New causal-timing question, independent splits and useful prospective validation |
| K overhead and scaling | PRELIMINARY | `results/matrix/REPORT.md` | Low beyond that host | K limited to two distinct alternatives; spawned workers | Larger randomized warmed-worker scaling study |
| Hostile containment | NOT ESTABLISHED | Deployment manifests only; local gateway checks | None for cluster | Manifests are not execution evidence | K3s policy/egress/secrets/device attack study |
| Physical validity | NOT ESTABLISHED | Authored J1 models only | None | No physical observations | External calibrated measurement and independent validation |
| Domain independence | NOT ESTABLISHED | `research/evidence/cycle4/domain_adapter_readiness.md` | Low structural plausibility | State/actions/metrics/replay traffic-coupled | Versioned adapter plus second-domain replication |
| Learning benefit | BLOCKED | `learning_enabled` rejected; RQ4 Decision D | None | No learner or policy-outcome experiment | Explicit future authorization and independently passed trust gate |
| Warm reset/equivalence | LOCALLY TESTED FOR DECLARED FIRST-PARTY MODEL | `research/evidence/cycle5/warm_worker_correctness.md`; final v2 66-test gate | Moderate within first-party deterministic contracts | Explicit guards plus finite contamination tests; invalid-return reuse and transport/queue lifecycle concerns require separate review | Extend reset/schema/lifecycle gate for changed models/transports |
| Warm improves complete evidence yield | SUPPORTED IN TESTED NORMAL CELLS | `research/evidence/cycle5/cycle5_results_analysis.md`; 86 verified runs | Moderate for paired local observation | Cold K1/K2 zero; warm K1 1.000/K2 median .994; delay medians zero; three units and uncontrolled host | Fresh longer operating-region replication under controlled host load |
| Hot ledger/ring retained counts are bounded | OBSERVED IN FINITE LONG PROBES | `research/evidence/cycle5/runtime_retention_design.md`; 3,000/1,000-epoch tables | Moderate for measured structures | Physical executor queue unmeasured; counts do not prove RSS plateau or indefinite memory bounds | Physical queue accounting and longer memory-allocation diagnosis |
| Continuous memory reaches stable plateau | NOT ESTABLISHED | All-online trend supplement, `research/evidence/cycle5/cycle5_results_analysis.md` | Positive late slopes observed | RSS +339.915/+265.009 bytes per epoch; Python +23.340/+191.497 bytes per epoch; finite duration | Diagnose allocations and validate stable trends in fresh longer runs |
| Production cadence robust across tested runs | NOT ESTABLISHED | Full paired per-seed timing/pressure tables | Moderate descriptive evidence | Many group medians near 40ms but severe individual timing degradation; no equivalence margin | Controlled longer cadence/tail study retaining every run |
| Shared-resource non-interference | NOT ESTABLISHED | Measured limited CPU/memory/storage pressure plus actual timing degradation | None for isolation; descriptive interference observed | One uncontrolled Windows host; stress intensity differs; causes not isolated | Verified controlled resource scheduling and stronger safe pressure |
| Graceful evidence-only degradation | PARTIALLY SUPPORTED FOR BOUNDED ADMISSION; NOT UNIVERSAL | Requested/admitted/completed K and fault tables | Moderate for fixed admission | Delay conditions reduce median admitted/completed K to zero and lose mirrors; storage fault aborts production | Deadline-aware capacity/storage contract and direct queue measures |
| Total archive storage is bounded | NOT ESTABLISHED | Append-only evidence design | None | Archive grows with epochs; no quota/export service | Declared quota/export preserving immutable research |
| Worker/delivery faults preserve trajectory | LOCALLY TESTED WITH QUALIFIERS | `research/evidence/cycle5/cycle5_failure_recovery.md`; final 12-case campaign | Moderate for tested local faults | Physical cases preserve trajectory; synthetic cases establish ledger behavior; cadence guarantee absent | Sustained failure/recovery and durable delivery study |
| Storage faults affect only evidence | REFUTED FOR TESTED IMPLEMENTATION | Transient CFR error aborts after 1/12 planned production epochs | High for injected local path | No failover; persistent errors can prevent failure manifest update | Separate production durability from bounded speculative persistence |
| Domain interface is implemented | PROPOSED ONLY | `docs/DOMAIN_INTERFACE.md`; readiness audit | Structural assessment only | State/actions/metrics/replay remain traffic-coupled | Regression-covered extraction and separate domain evaluation |
| Same-window epsilon is pre-decision | NOT ESTABLISHED; CURRENT COMPUTATION POST-WINDOW | `research/evidence/cycle5/information_timing_audit.md`; `csc/compare.py` | High for current dependency timing | Current comparison needs outcomes; historical signals require declared age/cutoff | Separate prospective causal-timing trust protocol |

No systems success upgrades a counterfactual-validity claim, and no trust result
establishes resource isolation. Unsupported claims are research gaps, not hidden
positive results.

## Cycle 5 final closure boundary

**A. Immutable measured archive.** All timing, evidence-yield, resource, replay, and failure claims in this matrix come solely from the 86-run archive at `results/cycle5-async/local-20261006-v1/`, collected with source identity `9e473658ebd91e004e9caa9bb02971e95db98e22b76771bc45b7e9dd783b4cba`.

**B. Defects discovered after collection.** The original read-only review retained R1-R7 for that source: storage can abort production; transport/queue/reuse paths needed correction; memory did not plateau; cadence was heterogeneous; and delayed conditions collapsed yield. These are not retroactively erased.

**C. Later current-code gates.** Successive v1-v5 gates repaired narrowly scoped source paths. The final v5 gate passed 108 tests in 28.362 seconds at `results/cycle5-validation/post-review-hardening-20261006-v5/` (full identity `c3e81bb6c4148f9b899970b5e71fe8a8b77226ba862ff3b7d1fd0f767cdda4be`). Its independent judgment found no CRITICAL, MAJOR, or MODERATE issue in that bounded scope; one MINOR integration-coverage limitation remains. These are current-code correctness tests, not new performance evidence.

**D. Closure classification.** No CRITICAL finding invalidates a Cycle 5 measured conclusion. No MAJOR implementation defect prevents this v5 tree from serving as the starting source for a separately preregistered Cycle 6 study. R1/R5/R6/R7 and the physical-queue/durability questions remain MODERATE empirical limitations for future measurement; they cannot support production, memory, storage, or resource-independence claims. The v5 integration-coverage gap is MINOR and documented only.

The matrix therefore treats archive-supported results and current-code-only properties separately. Trust remains Decision D and learning remains BLOCKED.
