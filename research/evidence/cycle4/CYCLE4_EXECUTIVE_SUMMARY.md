# Cycle 4 executive summary

**Status:** Completed, independently reviewed local research cycle, 2026-10-05.
Historical experiment series are preserved. The trust track and async track
answer separate questions; success in either does not compensate for the other.

## Four decisions

1. **Counterfactual trust: D.** No frozen selector qualified in calibration;
   final seeds 841–860 were not generated. No prospective held-out support for
   divergence or horizon was established.
2. **Local async decoupling: supported within the tested finite cooperative
   implementation.** Production does not await earlier shadow completion and
   measured cadence stayed near its 40 ms pacing target across delays. Evidence
   yield was poor. Resource independence and real-time safety remain unestablished.
3. **Learning: BLOCKED.** The trust gate failed, and the timing amendment also
   prevents an online decision-time trust claim. No learner was implemented.
4. **Cycle 5: a bounded systems experiment on warmed/reusable workers, continuous
   evidence yield and controlled resource contention.** The goal is useful
   evidence coverage at preserved production cadence, with finite retained
   history and declared interruption/restart behavior. A new trust experiment
   requires a separate prospective design; no more Cycle 4 tuning is permitted.

## Trust outcome and scope

The protocol was frozen in Cycle 3. Precollection review identified a scientific
timing defect: epsilon uses the realised production utility of the same H-tick
window, available only after the initial action. The experiment also supplies
the future exogenous window to all branches. Before generating outcomes, the
claim was narrowed to prospective fresh-seed **post-window common-input evidence
selection**, with selectors, factors, splits and gate preserved. This cannot
validate a signal available before the action being evaluated.

The source-isolated reference was independently implemented with stdlib-only
dependencies. Bidirectional transition/metric mutation and serialization tests
checked independence from SEM outcomes; selector features excluded reference
labels and mismatch names. The authoring specification and keyed PRNG semantics
remain shared. It is an authored-software reference, not physical truth.

Two immutable series executed from the frozen archive:

- `results/cycle4-trust/development-20261005-v1`: seeds 801–820, 1,200 runs,
  60 cells, eight anchors/run. Only feature computation and contracts were validated.
- `results/cycle4-trust/calibration-20261005-v1`: seeds 821–840, the same exact
  grid and counts. The global nearest-rank quantile grid and qualification logic
  were applied once. No one of 17 candidate records passed every cell.
- Final held-out seeds 841–860: **NOT GENERATED**, as required after no selection.
  This is not an observed final failure and cannot be reported as replication.

The baseline passed 29/60 calibration cells. The predeclared q=.50 divergence
display passed 13/60; adding H<=20 was equivalent. Descriptive pooled coverage
fell from .4274 to .1759 while precision increased from .9591 to .9840; abstention
rose from .5726 to .8241. Complete per-cell/run summaries and seed bootstrap
intervals, with undefined precision retained, are linked in
[trust analysis](cycle4_trust_analysis.md). Global precision does not override
the all-cell exposure and error conditions.

Some failure was structural: 12 cells have known unsupported incident semantics,
so every family abstains and cannot satisfy exposure. A binding h=2/6 cutoff
likewise loses entire longer-horizon cells. These constraints were documented
before outcomes, not repaired afterward. Empirical errors under rate mismatch
also remain. D rejects these global candidates under this frozen protocol; it
does not prove all divergence information or every uncertainty method useless.

Divergence therefore has **no supported prospective held-out incremental value**
beyond mirror epsilon. Horizon likewise has no supported incremental value:
h=20 is nonbinding and lower cutoffs fail the declared coverage objective. Higher
calibration precision alone is insufficient because recommendations become sparse.
Neither result supports a causal explanation of error.

## Negative controls, robustness and oracle

The predeclared controls ran on calibration after its fixed selection procedure.
Shuffled divergence retained coverage .1861 and precision .9916 versus original
q=.50 .1759 and .9840. Its usefulness did not degrade as hoped, limiting claims
that this particular trajectory-distance signal contributes beyond epsilon and
condition-dependent filtering. Constant zero divergence reproduced baseline.
Constrained label permutation reduced mean run precision from .4191 to .2299;
this supports association in the combined selection machinery, not a separate
divergence effect or a confirmatory significance claim.

The q=.50 display covered only .0291 of H=20 decisions, versus baseline .4944.
NS_GREEN dominated accepted actions; per-seed instability, undefined runs and
all factor strata remain visible in
[robustness diagnostics](../../figures/cycle4-trust-v1/robustness.md).
No new selector was created from these observations.

The reference-only oracle found genuinely better alternatives at .5796 of
anchors. Opportunity lost by abstention was .1682 for baseline and .4065 for
q=.50. This shows the software environment contains opportunities while selection
can miss many. Oracle fields never entered CSC inputs or actuation. Choice-value
loss of the model-selected alternative is not measured performance of a deployed
policy. Detailed oracle definitions are in the trust analysis and machine tables.

## Async architecture and local experiment

The new selectable async coordinator journals production, attempts whole-batch
bounded admission and proceeds. A coordinator-owned ledger joins completed work
to immutable epoch/anchor/action/input/branch identity, rejects malformed or
misassociated output and finalizes comparisons in epoch order. Full queues drop
shadows; deadlines expire evidence. Running expired futures retain permits until
settlement, preventing an apparently freed queue from growing without bound.
Late or duplicate results cannot replace comparisons or actuate. The original
synchronous mode remains default and reproducible.

The preregistered immutable series
`results/cycle4-async/local-20261005-v1` has 150 primary runs: five paired seeds
for K=0, sync K=1/K=2, async K=1/K=2 under normal, moderate, severe, timeout,
crash and saturation conditions. Twelve additional runs cover CPU-heavy,
memory-heavy, high-occupancy and normal async load. Each run has 12 epochs,
two excluded warmups, H=6 and a 40 ms pacing probe. The 300 ms deadline and
capacity settings were fixed before measurement.

Normal sync K=1/K=2 cadence was 147.027/163.376 ms, rising to 266.100/280.209 ms
with 120 ms delay. Severe paired median increases were 119.463 and 112.554 ms.
Async K=1/K=2 normal cadence was 40.436/40.498 ms; paired severe effects were
.058 ms [-.182,.174] and -.129 ms [-.195,.211]. Five paired effects per condition
are retained. No equivalence margin was chosen afterward; these are descriptive
local wall-clock decoupling observations.

Evidence yield limits this success. Normal median complete evidence fraction was
.1 for async K=1 and zero for K=2; severe-delay complete fraction was zero for
both. Normal async K=2 measured blocks had 60 expired and 90 dropped branches.
Cadence remained stable partly because backpressure shed most evidence. The
current spawned-worker/settings combination is not yet a useful continuous
counterfactual evidence service at this pace. Complete/partial/production-only
fractions, queue depths, latency origins and resources are in
[async tables](../../tables/cycle4_async_tables.md) and [analysis](cycle4_async_analysis.md).

## Failure, restart, storage and resources

All 162 runs completed their authoritative trajectories with matching hashes
within each paired seed, no missing production epochs and no observed unexpected
actuation. State-machine tests cover 64 transition pairs, out-of-order/duplicate/
expired delivery, finite capacity, faults, service exceptions and single-writer
rejection. Incomplete evidence has unavailable regret rather than a favourable score.

Restart uses a new identity and immutable directory. Stale results are rejected;
queued work is discarded. Durable distributed recovery is absent. Single-writer
JSONL flush and atomic JSON replacement cover tested races, but are not fsync
transactions. Comparison, polling and storage still run on the coordinator;
active queues are bounded while finalized history grows with finite run length.

The three-seed CPU/memory/occupancy microstudy had paired median cadence changes
.079/.021/-.001 ms, with poor evidence yield. This establishes neither resource
independence nor a sustained stress bound. Windows CPU zeros can reflect clock
quantization; worker RSS was unavailable and Python peak allocation is not RSS.
See [state-machine audit](async_state_machine_audit.md).

## Reproducibility and review

[Combined deterministic verification](../../tables/cycle4_reproducibility_verification.json)
passed: 28,800 action pairs per trust split, exact grid/split/order identity,
3,964 async branch replays, 17 async source files, raw-summary regeneration and
identical archived calibration tables/control hashes. Source archives accompany
every series. Workflow gates and absent final artifacts support staged compliance;
arbitrary external filesystem access is not independently logged.

[Independent review](red_team_cycle4_review.md) preserves major limitations in
information timing, structural gate failure, divergence-specific controls and
async yield. Precollection final-analyzer recalibration and missing baseline
comparison were corrected and tested before data. Review then found three
numeric overflow paths; current-tree guards reject huge integers, overflowing
weighted utility and nonfinite mirror distance. The reviewer independently
verified the regression. The measured archive remains unchanged and lacks those
later guards. The final current suite passed 54 tests in 29.807 s; an earlier
concurrent-audit localhost HTTP timeout is retained as an inconclusive caveat.

## Claims and exact Cycle 5 recommendation

Newly defensible claims are source-isolated authored-reference reproducibility,
honest no-selection gate execution and finite local async production/shadow
decoupling with explicit evidence loss. Hostile containment, physical validity,
online trust, useful continuous evidence service, resource isolation, domain
independence and learning benefit remain unsupported; see
[claim matrix](../../CLAIM_EVIDENCE_MATRIX.md).

Cycle 5 should first implement finite retained history and warmed/reusable worker
execution behind the existing authority boundary, then freeze one longer paired
continuous study. Measure production cadence independently alongside complete
evidence coverage, deadline loss, queue/process bounds and CPU/memory/storage
contention. Specify interruption/new-run restart and partial-artifact handling
before execution; retain all configurations that fail. Choose equivalence/yield
criteria from a declared workload requirement before outcomes, or report paired
distributions if no defensible requirement exists. Do not proceed directly to
a second domain, cluster claims or a learner. Future trust work is a distinct
new causal-timing protocol and fresh seed study, not another threshold search
over Cycle 4.
