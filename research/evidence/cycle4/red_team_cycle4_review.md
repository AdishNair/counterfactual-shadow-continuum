# Cycle 4 independent red-team review

**Status:** Independent final evidence and implementation review, 2026-10-05,
using GPT-6.1 Sol. Historical runs and frozen protocols were not changed.
Bounded synthetic numerical fault fixtures were executed without collecting an
experiment.

## Question, evidence and method

Can Cycle 4 support its trust and asynchronous systems claims without leakage,
abstention gaming, oracle circularity, stale evidence or hidden production waits?
The two tracks are evaluated independently.

Evidence reviewed: `research/archive/cycle4/protocol_support/cycle4_protocol_preflight.md`,
`research/archive/cycle4/protocol_support/cycle4_trust_preoutcome_specification.md`,
`research/archive/cycle4/protocol_support/cycle4_trust_source_isolation_audit.md`,
`research/archive/cycle4/protocol_support/trust_signal_experiment_protocol.md`,
`research/archive/cycle4/protocol_support/cycle4_trust_stage_ledger.json`,
`research/tables/cycle4-trust-calibration-v1/report.md`,
`research/tables/cycle4-trust-calibration-v1/verification.json`,
`research/tables/cycle4-trust-calibration-v1/negative-controls.json`,
`research/evidence/cycle4/async_state_machine_audit.md`, `research/evidence/cycle4/cycle4_async_protocol.md`,
`research/tables/cycle4_async_tables.md`,
`research/tables/cycle4_async_transition_tests.json` and
`research/tables/cycle4_async_verification.json`. Focused CodeGraph navigation
and targeted source reads covered selector/qualification, collection firewalls,
ledger/runner/store, comparator and invariant tests. Failure-reason and duplicate
counts below were extracted deterministically from candidate CSV/JSON records.

Trust verification reports 1,200 development and 1,200 calibration runs, each
with 60 cells and 9,600 anchors, using disjoint seed blocks. Calibration replayed
28,800 action pairs with no reported errors. Final seeds 841--860 were not
generated. Async archive verification reports 162 runs, 3,964 replayed branches,
17 source hashes and matching raw-summary regeneration. These are local
authored-software observations. Current-tree tests added after the async source
freeze are additional safeguards, not measurements under the archived source.

## Four independent decisions

| Decision | Finding | Permitted claim / consequence |
|---|---|---|
| Trust validity | **D: not established** | No frozen candidate qualified; final held-out generation stays blocked. Post-window calibration cannot establish current-decision online reliability. |
| Async systems | **Implemented and locally tested; narrow local timing support** | Production proceeds while older shadow work remains unresolved; cadence stayed near the imposed 40 ms pacing target in this small study. Useful evidence throughput and resource independence remain unestablished. |
| Learning | **Blocked** | No learner outcome evidence exists, and the trust protocol explicitly cannot authorize learning even if a selector passes. |
| Next systems step | **Cycle 5 recommended prospectively** | Study warmed or reusable workers under sustained load, jointly measuring cadence, evidence yield, resource competition and interruption behavior with a new preregistration. |

## CRITICAL findings and closure

**C1 — Final-outcome recalibration could invalidate the split; corrected before
collection.** The preflight identified an analyzer path that would generate
thresholds from final outcomes and omit baseline-relative checks. The corrected
`experiments/analyze_cycle4_trust.py` validates the prerequisite before opening
final records, uses the frozen rule, and checks baseline FPR and 80% coverage.
The preflight records four firewall fixtures and 15 passing trust tests. The
actual calibration selected no rule and therefore never reached final outcomes.
**Closure:** sufficient for the performed workflow. Preserve the archive and
prerequisite hashes. A stage ledger is not an independent audit of arbitrary
filesystem access; do not claim it proves every possible external read absent.

**C2 — Sparse abstention must not be called a reliable selector; closed for
Cycle 4's decision.** Qualification retains all 60 cells, exposure denominators
and undefined precision. None of the 17 displayed candidate configurations
qualified; duplicates are displayed but excluded from qualification. Baseline
passes 29 cells, q=.50 divergence 13. Pooled precision of 0.9840 with only 0.1759
coverage does not override the cell gate. **Closure:** D is scientifically
defensible. Do not promote successful subsets into a positive confirmatory
category or retrospectively relax exposure requirements.

No actuator-boundary bypass or accepted terminal-evidence resurrection was found
in the reviewed paths. This statement concerns local application logic, not
hostile-worker containment.

## MAJOR findings

**M1 — Timing changes the estimand; original online question remains open.**
Epsilon uses realized production utility from the same H-tick window; divergence
uses completed supplied-window SEM rollouts. This is future-window information
relative to the current actuation. The pre-outcome amendment correctly limits
Cycle 4 to post-window common-input selection. **Remedy:** retain that wording
in every conclusion. A future online study needs a frozen causal ordering,
features actually available before actuation, and new splits. This limitation
does not invalidate the narrowed negative calibration result.

**M2 — Some all-cell failures are structural, limiting falsification scope.**
Blocked-EW incident cells with unsupported SEM capability force abstention:
12 of 60 cells and 1,920 of 9,600 calibration anchors. The baseline has exactly
12 zero-median-coverage cells. Cutoffs h=2/6 also force excluded-horizon exposure
failure; h=20 is nonbinding and duplicates its divergence-only counterpart.
Thus the primary gate cannot prove a positive contribution from a binding
horizon cutoff. Additional failures exist: baseline has 29 cells with undefined
run precision and two FPR failures. **Remedy:** preserve D and distinguish
unsupported semantics/exposure from empirical discrimination. Any future
objective separating safe abstention on unsupported inputs from useful coverage
on supported inputs must be prospectively specified. Cycle 4 cannot reject all
divergence signals, all horizon methods or all CSC designs.

**M3 — Negative controls do not establish divergence-specific information.**
At the predefined q=.50 threshold, shuffled divergence has pooled precision
0.9916 and coverage 0.1861, versus 0.9840 and 0.1759 observed. Constant divergence
recovers baseline. Label permutation yields a diagnostic tail fraction
0.00990, but permutes labels for the combined frozen acceptance rule; baseline,
SEM action choice and epsilon still contribute selection information. **Remedy:**
report these controls as descriptive, without attributing the label association
uniquely to divergence or declaring a confirmatory significance result. They do
not rescue the failed gate.

**M4 — Near-target cadence accompanies severe loss of usable evidence.**
Async K=1 normal median complete-comparison fraction is 0.100; async K=2 normal
is 0.000. Async alternatives are mostly expired/dropped, while synchronous
normal comparisons are complete. **Remedy:** always pair cadence with complete
evidence yield. Cycle 5 should use warmed/reusable workers and sustained arrival
load, freeze evidence-age and completeness objectives alongside production
latency, and retain unsuccessful configurations. The present result supports
local delay decoupling, not useful continuous counterfactual service throughput.

**M5 — Malformed numeric evidence could stop comparison or serialization through
overflow; demonstrated cases closed in the current tree.** A bounded fake-ledger fixture used the
admissible weight `wait_weight=1` and a correctly identified shadow record with
finite `mean_queue=waiting_vehicle_ticks=1e308`. `valid_identity` accepted it;
after both futures settled, `poll()` raised `ValueError: nonfinite utility` in
comparison. Further bounded fixtures used the JSON-valid integer `10**400`,
which overflowed `math.isfinite`, and finite mirror queues `1.7e308` in both
directions, whose Euclidean distance became infinity and could not serialize.
Bad shadow evidence can therefore abort the coordinator instead of becoming
terminal rejected evidence. **Remedy:** handle overflow during component
validation and validate derived utility and mirror distance before accepting an
outcome; regress all three cases. **Closure:** the current `csc/pending.py` now
catches component conversion/arithmetic errors and checks derived utility and
mirror distance. The extended
`tests.test_async.AsyncTests.test_finite_metrics_with_overflowing_utility_are_rejected`
was independently rerun and passed, covering oversized metric/trace integers,
nonfinite mirror distance, rejected weighted overflow, missing epsilon/regret and
the next epoch's commit. This closes the demonstrated numerical cases, not
arbitrary hostile-output robustness. The measured series used ordinary authored
queues and zero wait/switch weights, so these fixtures do not demonstrate a
failure in its observations. Its immutable source lacks the new guards; do not
retroactively attribute the correction to measured code.

## MODERATE findings

**O1 — Source isolation is not an independently correct oracle.** Reference
imports are limited to stdlib copy/random, transition and metric mutation tests
are bidirectional, and serialization preserves input. Action semantics, J1
specification and keyed PRNG remain shared common causes. The feature firewall
excludes reference labels and mismatch names, but self-declared incident
capability can be false without detection. **Remedy:** keep the authored-software
reference label and declaration limitation; physical validity or model adequacy
requires additional independent evidence.

**O2 — Numeric scales and undefined endpoints need explicit interpretation.**
Divergence is an unnormalized sum in queue-vehicle ticks; epsilon/gain are utility
units derived from negative mean queue. Larger H changes divergence scale even
with similar tickwise discrepancies. The prospective run-level interpretation
of undefined precision requires all 20 runs to recommend, making the separate
12-run criterion redundant. Undefined FPR/FNR become zero only in descriptive
median reduction when their relevant denominator is absent. **Remedy:** disclose
these choices and label absent-denominator summaries; none is a calibrated
probability or evidence of zero underlying risk. Do not normalize or change them
after seeing this calibration.

**O3 — Active-work limits do not bound retained history for a continuous
service.** `pending` and `active` have capacity controls; `finalized` and
`finished` retain entries for the full run, and runner resource rows also grow.
**Remedy:** before long-running deployment, stream summaries and use bounded
identity retention or durable indexed history with a declared replay horizon.
The finite 12-epoch experiment is unaffected; a bounded-memory service claim
is unsupported.

**O4 — Storage, restart and resource independence remain limited.** Single
writer checks and atomic JSON replacement avoid the tested local writer races;
flushed JSONL is not an fsync transaction. Restart creates a new identity and
directory, with stale outputs rejected, but does not recover or redispatch a
durable queue. Slow or failed storage still lies on the coordinator path. Thread
joining occurs after production, with cooperative finite-timeout workers; it is
not a hard scheduling bound. **Remedy:** test coordinator interruption, partial
records, worker restart, slow/full storage and actual resource contention under
a separately specified recovery model before service-readiness claims.

## MINOR reporting issues

**N1 — Cross-mode completion origins differ.** Sync branch latency is dispatch
roundtrip; async is commit-to-acceptance including queue/poll delay. Comparison
origins also differ. **Remedy:** keep the table footnote and avoid treating these
absolute values as a controlled cross-mode latency effect.

**N2 — Small-sample resource summaries cannot imply zero cost.** Five primary
seed pairs, three microstudy seeds and ten measured epochs per run provide
descriptive p95/p99 only. Windows CPU quantization produces zeros; Python peak
allocation is not RSS, and observed PIDs omit some expired workers. **Remedy:**
retain unavailable values and ranges; use higher-resolution and external resource
instrumentation in Cycle 5.

**N3 — Local test timing can be sensitive to concurrent load.** The integrator
reported one localhost HTTP test timeout during a full-suite invocation concurrent
with the heavy archive audit; a subsequent full suite passed all 54 tests in
29.807 seconds after the audit ended. Concurrency is context, not an established
cause of the failure. **Remedy:** retain the failure and clean rerun in validation
reporting; neither invocation establishes resource-independent HTTP latency.

## Limitations, open questions and next actions

This review did not rerun data collection, tune selectors, alter historical
artifacts or inspect a final held-out series. It reviewed the reported archived
verification and executed synthetic numerical-edge fixtures; root's combined
reproducibility audit supplies the full regeneration record. Application tests
do not establish OS/network/K3s containment, physical counterfactual truth,
real-time safety, domain portability or learning benefit.

Preserve Cycle 4 D, no final generation and the learning block. Preserve the
current-tree M5 regression and its archive limitation.
Prioritize the systems-focused Cycle 5 outlined above. A future trust study is
a separate prospective design task: establish actual pre-actuation information
availability and a scientifically justified exposure objective before generating
fresh outcomes. No current timing or oracle result authorizes policy actuation
from shadow estimates.
