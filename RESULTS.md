# Results from this workspace

## Current evidence boundary

Cycle 5 performance numbers in this file come only from the immutable 86-run
archive `results/cycle5-async/local-20261006-v1/` and its pre-correction source
identity `9e473658ebd91e004e9caa9bb02971e95db98e22b76771bc45b7e9dd783b4cba`.
Post-collection v1-v5 gates, including the final 108-test v5 gate, are
current-code correctness evidence only; they do not alter the archive's cadence,
yield, memory, storage, or resource results. The historical seven-MAJOR review
findings therefore apply to the measured source. Final v5 closure found no
CRITICAL or MAJOR current-tree blocker for a future preregistered study.

The generated [matrix report](results/matrix/REPORT.md) links the experiment
interpretation to [paired summaries](results/matrix/matrix-summary.json) and
the raw per-run artifacts. The sweep executed **15 runs, 1,500 total epochs**:
five seeds for each of K=0/1/2, 100 epochs per run, 10 warmup epochs excluded from
each summary. K excludes the mirror. All results concern the software environment.

| K | Median of per-seed median epoch time (ms) | Median of per-seed median production decision time (ms) |
|---:|---:|---:|
| 0 | 1.6169 | 0.1848 |
| 1 | 135.1413 | 0.2578 |
| 2 | 145.6411 | 0.2605 |

The indexed raw summaries and their manifest hashes are the source of record for
the table. A prior version of this document reported 4.3614/169.3680/189.9336 ms
for K=0/1/2. Those figures are preserved as an unresolved provenance record: they
do not match the current indexed matrix series and must not be combined with it or
cited as the current result. See `research/evidence/cycle1/results_analysis.md`.

Every paired seed had the same workload hash and production trajectory hash across
K. Environment audit recorded zero unexpected gateway correlation/action pairs.
The median fidelity gap was 0.75 utility units for both CSC conditions; median
discounted regret was zero. These figures are actual measurements, not design
targets. A zero median does not imply that no alternative ever appeared better;
the raw records and per-run beaten rate retain that information.

The increased latency matters: this implementation does not demonstrate the
specification's production non-interference criterion. The local harness waits
for spawned shadows between logical epochs. Its performance is evidence about
this implementation, not a measurement of a warmed distributed CSC deployment.
CPU clocks on this Windows host quantize short worker execution to zero in many
samples. Those zeros mean insufficient measurement resolution, not free compute.
Python allocation peaks are not total RSS; Windows worker RSS is null.

These RSS limitations describe the historical matrix instrumentation. Cycle 5
adds Windows current working-set/process/handle sampling; current working set
and Python allocations remain different measurements.

The [validation artifact](results/validation/validation-summary.json) includes
crash, timeout, drop, duplicate, reorder, delay, model-failure, branch-budget and
capture-skip scenarios, plus two-mirror determinism, incident horizon sweeps and
no-mirror/no-sync/model-bias controls. Fault runs retained the baseline production
trajectory. Incomplete windows were excluded rather than assigned favorable scores.
Each successful branch in the fault scenarios was replayed from saved inputs.

## Preliminary all-actions reference-fidelity smoke

The [reference-fidelity analysis](research/tables/reference-fidelity-smoke.md)
summarizes eight new runs (two seeds for each horizon/service-rate cell), with
18 measured epochs per run. Its reference replays the authored `ProductionWorld`
from the captured anchor and common inputs for every action; it does not import
`ShadowWorldModel`. This provides a check independent of the SEM, not physical
or external ground truth. Median rank agreement ranged from 0.8333 to 0.9722 by
cell, while the current epsilon threshold covered selected-alternative error in
only 0.6111 to 0.7222 of epochs by cell. The result is evidence that the current
gate is not a uniform error bound, and is not evidence for policy improvement.

The immutable raw series is at
`results/reference-fidelity/all-action-smoke-20260928`; each run was verified
against its artifacts and recorded CSC source identity before analysis. The
[verification record](research/tables/reference-fidelity-smoke-replay-verification.json)
contains eight verified runs, 640 replayed trajectories, and zero mismatches.

## Confirmatory reference-fidelity factorial

The [frozen design amendment](research/evidence/cycle2/confirmatory_factorial_amendment.md)
predeclared 36 horizon/demand/incident/mismatch cells with 20 seed/run units per
cell. The current gate, `estimated improvement > epsilon`, passed 15/36 cells
in its first evaluation and 13/36 cells in a disjoint held-out evaluation; only
11 cells passed in both. The calibration split selected multiplier 1.0, so no
changed replacement rule was found. The global decision is **D: counterfactual
validity is not established for policy use**.

Each of the evaluation, calibration, and held-out series has 720 runs, 2,160
anchors, and 6,480 action observations with verified hashes/source identity.
The reference does not import `ShadowWorldModel`, but is an authored-production
software reference rather than physical or factual ground truth. See the
[cross-holdout synthesis](research/tables/confirmatory-factorial-synthesis/cross-holdout-synthesis.md)
and [red-team review](research/evidence/cycle2/red_team_factorial_review.md). Learning remains
disabled.

The [matrix replay verification](results/matrix/replay-verification.json) checks
artifact hashes and reconstructs every successful matrix branch trajectory.
[Local test output](results/test-results.log) records unit, integration, gateway
attack, failure and replay tests. These are not the full A1–A14 container suite.

The matrix runtime sources are archived in `results/measured-source/csc`; their
hashes can be matched to the manifests. The current tree also includes a subsequent
container-compatibility fix: missing Git now produces `git_sha: null` rather than
aborting a run. That fix changes provenance collection only, not model transitions.

## Cycle 4 trust and local async evidence (2026-10-05)

The frozen trust study executed
`results/cycle4-trust/development-20261005-v1` and
`results/cycle4-trust/calibration-20261005-v1`: each 1,200 runs, 60 cells and
9,600 anchors. No candidate qualified. **Final seeds 841–860 were not generated;
Decision D remains.** Baseline passed 29/60 calibration cells. Predeclared q=.50
divergence passed 13/60, raising descriptive precision .9591 to .9840 while
reducing coverage .4274 to .1759. Its H<=20 version was equivalent; shorter
horizon cutoffs lost full-cell exposure. Shuffled divergence retained comparable
precision, limiting signal-specific claims. The reference is independent authored
software. Same-window epsilon and supplied future inputs limit this to post-window
common-input reliability, not validated online decision-time trust. See
[trust analysis](research/evidence/cycle4/cycle4_trust_analysis.md).

The preregistered async series `results/cycle4-async/local-20261005-v1` contains
150 primary and 12 resource-probe runs. Sync K=1/K=2 median cadence increased
from 147.027/163.376 ms normally to 266.100/280.209 ms under 120 ms shadow delay.
Async cadence remained near 40 ms; paired severe effects were .058 ms
[-.182,.174] for K=1 and -.129 ms [-.195,.211] for K=2. These are five-seed
descriptive local wall-clock decoupling results. Normal async median complete
evidence fraction was only .1 (K=1) and zero (K=2); deadlines and backpressure
discarded most evidence. No performance-equivalence threshold was invented.

All paired production/workload hashes matched, and archived verification replayed
3,964 successful branches with raw-summary matches. The current tree subsequently
rejects numeric overflow in malformed shadow output; it is locally tested, not
part of these measured archives. Local results do not establish resource isolation,
real-time safety, K3s containment or durable recovery. See [async analysis](research/evidence/cycle4/cycle4_async_analysis.md),
[reproducibility audit](research/evidence/cycle4/cycle4_reproducibility_audit.md),
[independent review](research/evidence/cycle4/red_team_cycle4_review.md) and
[executive summary](research/evidence/cycle4/CYCLE4_EXECUTIVE_SUMMARY.md).

Raw results are ignored by Git to avoid accidentally committing large experiments,
but remain in the workspace. Preserve `results/` with the source when archiving
this research run. No learning benefit, physical traffic benefit, or verified
hostile-container containment has been established.

## Cycle 5 systems work (2026-10-06; independently reviewed)

Every timing/yield/resource number below belongs to the immutable measured source.
Post-measurement review prompted separate current-tree queue/validation/transport
corrections whose 80-test local gate passed; independent re-review supports narrow
physical-count/reader-local closure but leaves transport and quarantine blockers;
they have no main performance
evidence and do not change the archived result interpretation.

**Question:** Can continuous local async CSC sustain comparable evidence while
preserving production cadence under finite workers/hot state and controlled
shared-resource pressure? The [preregistered protocol](research/evidence/cycle5/cycle5_protocol.md)
freezes the main 84-run pilot and 3,000/1,000-epoch probes. All **86 runs** completed
and verified against source/config/workload/artifact identities, including
**41,686 accepted-branch replays with zero mismatch**. Main production/workload
hashes matched within each seed; no production epoch was missing, and no
production error or unauthorized mutation was observed. These are software
trajectory checks, not timing equivalence or external traffic validity.

The [deterministic analysis](research/evidence/cycle5/cycle5_results_analysis.md) compares three
independent paired runs per cell, each with 180 measured epochs:

| Normal load | Cold complete fraction | Warm complete fraction | Warm complete age, median over run medians |
|---|---:|---:|---:|
| K=1 | 0.000 in every run | 1.000 in every run | 41.630 ms |
| K=2 | 0.000 in every run | median 0.994; range 0.989–0.994 | 42.141 ms |

Normal warm K=1 had no drops/expiry; warm K=2 had 12 dropped branches and no
expiry across the three measured cohorts. Warm K=1/K=2 produced about 24.6/24.5
complete records per second during production. Moderate delay yielded median
complete fraction zero, with one seed reaching 0.211/0.117; severe delay yielded
zero in all warm runs. Fixed mirror-first admission reduced median admitted and
completed K to zero under these delay conditions. Even mirrors could be lost;
preserving cadence alone did not guarantee an evidence stream.

Typical condition-median cadence remained around 40.3–40.5 ms, but aggregation
hides large failures: normal cold K=1/K=2 seed 1501 had run medians
129.592/146.090 ms. Storage warm K=2 seed 1501 had median 291.945 ms and p99
800.589 ms; the condition median of run p99 values was 67.781 ms. Its complete
fraction ranged 0.606–0.983 and partial fraction reached 0.172. The uncontrolled
host and three run units limit causal attribution; resource non-interference and
robust cadence across all tested runs are not established. CPU pressure used one
process, memory touched at most 64 MiB, and storage used flushed, non-fsync file
rewrites. These probes were measured but do not establish whole-host saturation.

The long-normal 3,000-epoch probe retained measured-cohort completeness 0.999;
the one-slot severe 1,000-epoch probe retained zero. Hot completed/duplicate rings
capped at 64 and pending epochs at 8 observed. Measured-cohort RSS minimum/end
was 34.777/37.816 MiB normally and 34.043/35.562 MiB under saturation. Positive
second-half RSS slopes were 0.332/0.241 KiB per epoch; Python current allocation
slopes were 23.44/186.14 bytes per epoch. Count boundedness was observed,
but a memory plateau or indefinite bounded memory was not established. Archives
ended near 125.186/15.321 MiB and grew linearly. Exact offline summaries load
finite histories after production, outside the hot-state claim.

Those frozen trend tables exclude the first 20 warmups. The independently hashed
supplement restores the preregistered all-online state cohort: RSS second-half
slopes **339.915/265.009 bytes per epoch**, Python current second-half slopes
**23.340/191.497 bytes per epoch** for normal/saturated probes. Both cohorts
retain positive slopes; neither establishes a plateau. Post-production exact
summary RSS sampled after reduction reached **512,155,648 bytes (488.430 MiB)**;
this is not an independently sampled RSS peak. Measured ledger/ring caps do not
directly measure the physical executor queue. The proposed OS-sampling cache
explanation was falsified by a separate 110-call diagnostic; that does not prove
general leak freedom (`results/cycle5-validation/os-metrics-cache-20261006-v2`).

The final source-bound local gate passed **66 tests in 141.372 seconds** at
`results/cycle5-gate/runtime-20261006-v2/`. The independent fault script's
**12 behavior checks passed** at
`results/cycle5-validation/faults-20261006T135732Z-3827f22a`. Physical processing
death and deliberate loss of a real completed result before coordinator acceptance
preserved all 12 production epochs, paired trajectory/workload hashes and accepted
trajectory replay. Evidence loss remained explicit. This is replacement behavior,
not durable exactly-once recovery or a cadence guarantee.

The fault study also has a negative finding: one transient CFR append error
aborted the authoritative run after **1 of 12** planned production epochs, with a
FAILED partial archive. Storage failure is not safely isolated to evidence.
Prior validation attempts/source variants are preserved; invalid pre-deadline
FAILED-count assertions were corrected without changing the evidence deadline.
See [failure and recovery](research/evidence/cycle5/cycle5_failure_recovery.md).

The deterministic [historical loss decomposition](research/evidence/cycle5/cycle5_evidence_loss_analysis.md)
preserves Cycle 4's poor yield. Warm reuse materially improved normal-load yield
within this paired pilot; delay-pressure failures and positive memory trends
remain limitations. The 200-epoch factorial/3,000-epoch longest probe does not
evaluate the specification's 10,000 consecutive epochs at at least 90% completeness.
Total CPU efficiency remains unavailable because failed/expired worker CPU
is incomplete and Windows short samples are quantized. Append-only disk evidence
grows with time. The [independent review](research/evidence/cycle5/cycle5_red_team_review.md)
reports no CRITICAL authority/fabrication finding and seven MAJOR issues for the
pre-correction measured source:
storage availability/partial-write recovery, blocking transport/shutdown,
physical cancellation queues, invalid-output worker reuse, positive memory
trends/offline cost, cadence heterogeneity and delay-coverage collapse.
Current-tree fixes for three lifecycle/transport defects passed 80 source-bound
tests in 30.089 seconds; independent re-review narrowly closes the physical count
mechanism and reader locals but keeps R2/R4 MAJOR and R9 MODERATE/open. Further
corrections passed a fresh **96-test gate in 28.181 seconds** at
`results/cycle5-validation/post-review-hardening-20261006-v2/`; later reviews and
the v5 gate supersede it only for current-source correctness. Campaign v2 has 13 checks including disposable actual
Windows tree cleanup and abort before the next condition on false cleanup
certainty. They do not revise
the measured archive. See [post-review hardening](research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening.md).

Successive independent reviews retained the physical-count/quarantine/reader-local
corrections and exposed bounded warm-lease, cold-capacity, arithmetic, cleanup,
analysis and source-copy defects. The final v5 correction passed **108 tests in
28.362 seconds** at `results/cycle5-validation/post-review-hardening-20261006-v5/`.
The [v5 independent re-review](research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v5.md) found no
remaining CRITICAL, MAJOR or MODERATE issue within that bounded scope and retained
one MINOR integration-test limitation. These source paths were not reported
failures in the 86-run campaign and do not change any measured number. V5 has no
corrected-source cadence, memory, storage or yield result.
Trust stays **Decision D**,
learning stays **BLOCKED**, and physical validity, hostile containment, real-time
guarantees and domain independence remain unestablished.


## Cycle 5 final closure

Cycle 5 is **CLOSED**. The immutable 86-run archive remains the sole performance source; the delivery audit verified all scheduled runs and required provenance. It supports normal-cell warm-worker evidence-yield improvement, but also preserves the delay-yield collapse, severe cadence outliers, positive memory slopes, and storage append failure that stopped production after 1/12 epochs. Named hot retained counts were capped; process memory was not demonstrated bounded.

Post-collection source fixes were validated only by v1-v5 gates. The final v5 gate passed 108 tests in 28.362 seconds and its independent bounded-scope review retained one MINOR integration-coverage limitation, with no CRITICAL/MAJOR/MODERATE current-tree finding. These tests do not revise archived performance. The repository is an adequate correctness-gated starting point for a separately preregistered Cycle 6 systems study, not a claim of resource non-interference, durable storage recovery, physical validity, hostile containment, or deployment readiness. Trust remains **Decision D** and learning remains **BLOCKED**.
