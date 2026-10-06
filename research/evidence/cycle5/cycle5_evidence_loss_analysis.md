# Cycle 5 evidence loss analysis

**Status:** Implemented deterministic read-only decomposition of immutable Cycle 4 archives; Cycle 5 attribution is reported in its own results tables.

**Question:** Why did logical async decoupling yield little complete comparable evidence?

**Evidence:** `results\cycle4-async\local-20261005-v1`; `research\tables\cycle5_cycle4_loss.json` and epoch-level CSV. Method: exclude each run's declared warmups; classify every unavailable branch from its terminal status and failure flags; retain overlapping loss reasons per epoch rather than force a misleading single cause.

| Track | Mode | Condition | Runs | Median complete epoch fraction | Accepted branch fraction | Branch loss counts | Incomplete epoch reason sets |
|---|---|---|---:|---:|---:|---|---|
| micro | async2 | cpu | 3 | 0.000 | 0.000 | {'deadline_expiry': 36, 'queue_admission_failure': 54} | {'deadline_expiry': 12, 'queue_admission_failure': 18} |
| micro | async2 | memory | 3 | 0.000 | 0.022 | {'deadline_expiry': 34, 'queue_admission_failure': 54} | {'deadline_expiry': 12, 'queue_admission_failure': 18} |
| micro | async2 | normal | 3 | 0.000 | 0.033 | {'deadline_expiry': 33, 'queue_admission_failure': 54} | {'deadline_expiry': 11, 'queue_admission_failure': 18} |
| micro | async2 | occupancy | 3 | 0.100 | 0.067 | {'queue_admission_failure': 81, 'deadline_expiry': 3} | {'queue_admission_failure': 27, 'deadline_expiry': 1} |
| primary | async1 | crash | 5 | 0.100 | 0.080 | {'deadline_expiry': 62, 'queue_admission_failure': 30} | {'deadline_expiry': 32, 'queue_admission_failure': 15} |
| primary | async1 | moderate | 5 | 0.000 | 0.000 | {'deadline_expiry': 66, 'queue_admission_failure': 34} | {'deadline_expiry': 33, 'queue_admission_failure': 17} |
| primary | async1 | normal | 5 | 0.100 | 0.090 | {'deadline_expiry': 61, 'queue_admission_failure': 30} | {'deadline_expiry': 31, 'queue_admission_failure': 15} |
| primary | async1 | saturation | 5 | 0.100 | 0.100 | {'queue_admission_failure': 90} | {'queue_admission_failure': 45} |
| primary | async1 | severe | 5 | 0.000 | 0.000 | {'deadline_expiry': 50, 'queue_admission_failure': 50} | {'deadline_expiry': 25, 'queue_admission_failure': 25} |
| primary | async1 | timeout | 5 | 0.100 | 0.080 | {'deadline_expiry': 62, 'queue_admission_failure': 30} | {'deadline_expiry': 32, 'queue_admission_failure': 15} |
| primary | async2 | crash | 5 | 0.000 | 0.000 | {'deadline_expiry': 60, 'queue_admission_failure': 90} | {'deadline_expiry': 20, 'queue_admission_failure': 30} |
| primary | async2 | moderate | 5 | 0.000 | 0.000 | {'deadline_expiry': 60, 'queue_admission_failure': 90} | {'deadline_expiry': 20, 'queue_admission_failure': 30} |
| primary | async2 | normal | 5 | 0.000 | 0.000 | {'deadline_expiry': 60, 'queue_admission_failure': 90} | {'deadline_expiry': 20, 'queue_admission_failure': 30} |
| primary | async2 | saturation | 5 | 0.000 | 0.040 | {'queue_admission_failure': 135, 'deadline_expiry': 9} | {'queue_admission_failure': 45, 'deadline_expiry': 3} |
| primary | async2 | severe | 5 | 0.000 | 0.000 | {'deadline_expiry': 60, 'queue_admission_failure': 90} | {'deadline_expiry': 20, 'queue_admission_failure': 30} |
| primary | async2 | timeout | 5 | 0.000 | 0.000 | {'deadline_expiry': 60, 'queue_admission_failure': 87, 'shutdown': 3} | {'deadline_expiry': 20, 'queue_admission_failure': 29, 'shutdown': 1} |

Normal async1: median across run medians of dispatch nonexecution time = 151.284 ms, worker execution = 0.468 ms, hydration = 0.110 ms. The large nonexecution component motivates reuse, but is not an identified startup-only measurement.

Normal async2: median across run medians of dispatch nonexecution time = 169.769 ms, worker execution = 0.498 ms, hydration = 0.109 ms. The large nonexecution component motivates reuse, but is not an identified startup-only measurement.

**Findings:** Whole-batch queue admission and deadline expiry account for the recorded loss; branch completion alone does not imply a full mirror-plus-all-requested-alternatives comparison. Coordinator-observed RUNNING, comparison serialization order and late successful outcomes must retain their timing/provenance distinction.

**Limitations:** Archive has no process-ready timestamp: dispatch nonexecution includes process launch, Python imports, serialization, transport and scheduler delay; cannot causally partition worker startup. RUNNING is coordinator observation of a thread future, not subprocess start or execution start. Reported branches are accepted before epoch deadline; lifecycle late successful results are distinct from usable comparable evidence. No archived result-store/flush timing, OS worker RSS or reliable shared resource contention measurements.

**Open questions / next actions:** Measure warm/cold dispatch stages directly without enlarging the 300 ms deadline; preserve cold baseline; record every requested/admitted/completed alternative count and measure bounded history during continuous operation.

## Cycle 5 completed-run loss decomposition

**Status:** Read-only deterministic derived analysis of the completed immutable Cycle 5 campaign. Epoch table: `research/tables/cycle5_epoch_loss.csv`; machine group counts and method identity: `research/tables/cycle5_loss_groups.json`. This appendix does not modify Cycle 4 findings.

Every requested epoch (including separately marked warmups) has branch terminal statuses, observed reason counts, complete versus partial requested-set evidence, requested/admitted/completed K, and resource state. Headline groups below exclude declared warmups. Counts distinguish physical worker-return telemetry, timely accepted comparable branches, and complete comparable epochs. K excludes mirrors.

| Track | Mode | Condition | Measured epochs | Accepted / requested branches | Complete epochs | Partial requested-set epochs | Branch loss reason counts |
|---|---|---|---:|---|---:|---:|---|
| factorial | cold1 | cpu | 540 | 0 / 1080 | 0 | 0 | {'expiry:deadline': 731, 'queue_admission_failure:queue_full': 349} |
| factorial | cold1 | memory | 540 | 0 / 1080 | 0 | 0 | {'expiry:deadline': 596, 'queue_admission_failure:queue_full': 484} |
| factorial | cold1 | moderate | 540 | 0 / 1080 | 0 | 0 | {'expiry:deadline': 704, 'queue_admission_failure:queue_full': 376} |
| factorial | cold1 | normal | 540 | 0 / 1080 | 0 | 0 | {'expiry:deadline': 732, 'queue_admission_failure:queue_full': 348} |
| factorial | cold1 | severe | 540 | 0 / 1080 | 0 | 0 | {'expiry:deadline': 579, 'queue_admission_failure:queue_full': 501} |
| factorial | cold1 | storage | 540 | 0 / 1080 | 0 | 0 | {'expiry:deadline': 724, 'queue_admission_failure:queue_full': 356} |
| factorial | cold2 | cpu | 540 | 0 / 1620 | 0 | 0 | {'expiry:deadline': 604, 'queue_admission_failure:queue_full': 1016} |
| factorial | cold2 | memory | 540 | 0 / 1620 | 0 | 0 | {'queue_admission_failure:queue_full': 1004, 'expiry:deadline': 616} |
| factorial | cold2 | moderate | 540 | 0 / 1620 | 0 | 0 | {'expiry:deadline': 565, 'queue_admission_failure:queue_full': 1055} |
| factorial | cold2 | normal | 540 | 0 / 1620 | 0 | 0 | {'expiry:deadline': 863, 'queue_admission_failure:queue_full': 757} |
| factorial | cold2 | severe | 540 | 0 / 1620 | 0 | 0 | {'expiry:deadline': 829, 'queue_admission_failure:queue_full': 791} |
| factorial | cold2 | storage | 540 | 0 / 1620 | 0 | 0 | {'queue_admission_failure:queue_full': 744, 'expiry:deadline': 876} |
| factorial | warm1 | cpu | 540 | 991 / 1080 | 490 | 11 | {'expiry:deadline': 89} |
| factorial | warm1 | memory | 540 | 1080 / 1080 | 540 | 0 | {} |
| factorial | warm1 | moderate | 540 | 97 / 1080 | 38 | 21 | {'expiry:deadline': 683, 'queue_admission_failure:queue_full': 300} |
| factorial | warm1 | normal | 540 | 1080 / 1080 | 540 | 0 | {} |
| factorial | warm1 | severe | 540 | 0 / 1080 | 0 | 0 | {'queue_admission_failure:queue_full': 523, 'expiry:deadline': 557} |
| factorial | warm1 | storage | 540 | 1065 / 1080 | 531 | 3 | {'expiry:deadline': 7, 'queue_admission_failure:queue_full': 8} |
| factorial | warm2 | cpu | 540 | 1605 / 1620 | 535 | 0 | {'queue_admission_failure:queue_full': 15} |
| factorial | warm2 | memory | 540 | 1570 / 1620 | 523 | 1 | {'expiry:deadline': 20, 'queue_admission_failure:queue_full': 30} |
| factorial | warm2 | moderate | 540 | 101 / 1620 | 21 | 28 | {'expiry:deadline': 885, 'queue_admission_failure:queue_full': 634} |
| factorial | warm2 | normal | 540 | 1608 / 1620 | 536 | 0 | {'queue_admission_failure:queue_full': 12} |
| factorial | warm2 | severe | 540 | 0 / 1620 | 0 | 0 | {'expiry:deadline': 574, 'queue_admission_failure:queue_full': 1046} |
| factorial | warm2 | storage | 540 | 1425 / 1620 | 457 | 32 | {'expiry:deadline': 171, 'queue_admission_failure:queue_full': 24} |
| long | warm2 | long-normal | 2980 | 8936 / 8940 | 2978 | 1 | {'queue_admission_failure:queue_full': 3, 'expiry:deadline': 1} |
| long | warm2 | long-saturation | 980 | 0 / 2940 | 0 | 0 | {'expiry:deadline': 1207, 'queue_admission_failure:queue_full': 1733} |

Limitations: Physical returns mean lifecycle delivered worker-runtime envelope; this is not a count of all subprocess computations that may finish without accepted output. Terminal flags establish observed queue/deadline loss, not a causal startup/scheduler/storage allocation. Startup-only cause remains unknown. Loss categories can overlap within an epoch; every incomplete nonzero-K epoch retains its full reason set. K0 is excluded from evidence-loss denominators.

No incomplete requested epoch was discarded or recoded as success because fewer alternatives were admitted. Any accepted-but-incomplete mirror/alternative subset is scientifically partial even when the original raw `record_status` label differs. The frozen raw partial-label metric remains unchanged in the main archive.
