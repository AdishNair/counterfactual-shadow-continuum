# Post-analysis red-team review: reference-fidelity factorial

**Status:** Independent adversarial review of completed immutable series,
2026-09-28. No experiment, result, or existing research artifact was modified.

## Question

Does the confirmatory factorial establish that the current or replacement
epsilon gate is valid for alternative-action recommendations, and does it
justify learning or stronger CSC claims?

## Scope and verification

I inspected the pre-execution amendment, frozen design, oracle, factorial
driver, analyzer, verifier, the three immutable series, and their published
tables. A read-only hash check found all listed output and current-source hashes
matching in all three series. Each series is complete with 720 scheduled runs,
2,160 anchor observations, and 6,480 action observations; no failed runs are
recorded. The corresponding verifier reports agree. This establishes internal
artifact consistency under the currently available source tree. It is not a
security audit, physical-traffic experiment, or independent replication.

## Conclusion

The factorial gives useful, reproducible **negative evidence** in the authored
J1 software model: the fixed `estimated_improvement > epsilon` gate does not
meet its predeclared all-cell criterion. It passed 15 of 36 cells in the initial
evaluation and 13 of 36 cells in the held-out replacement evaluation. The
predeclared calibration chose multiplier 1.0, so the alleged replacement made
no change; the held-out result again fails global support. The correct global
classification is therefore **counterfactual validity not established for the
gate across the declared factorial**, with certain cell-specific observations
only.

Learning remains unjustified and must remain disabled. The evidence is limited
to comparisons between an SEM and the same authored production-model family;
it does not establish physical, causal, deployment, safety, or policy-improving
validity.

## CRITICAL

### C1 - The gate fails the frozen global decision rule

**Evidence.** The amendment requires every full cell to have median precision
at least 0.95, median false-positive rate at most 0.05, and median abstention
below 0.95. The evaluation table marks 15/36 cells as passing; the held-out
replacement-evaluation table marks 13/36 as passing. Failures include
`rate-and-incident-omitted` cells with median precision 0 or 0.5 and median
false-positive rates up to 1.0, as well as cells whose median abstention is 1.0.
See `research/tables/confirmatory-factorial-evaluation/reference-factorial-cell-summary.csv`
and `research/tables/confirmatory-factorial-replacement-evaluation/reference-factorial-cell-summary.csv`.

**Assessment.** Conditional cell-level pass flags cannot be promoted to an
overall-valid decision rule. In particular, an unlabelled deployment might meet
one of the deliberately adverse regimes where the gate failed.

**Alternative explanation.** The gate may be useful after explicit regime
detection and a separately validated abstention policy. The factorial does not
evaluate such a regime classifier or a safe online detection mechanism.

**Required disposition.** Record global failure as the primary result. Do not
authorize learning, policy selection, or general gate use. A future conditional
rule needs a frozen regime classifier, a stated domain of use, and a new
held-out evaluation that includes regime-misclassification and out-of-domain
cases.

### C2 - The reference is not independent ground truth beyond the SEM boundary

**Evidence.** `experiments/reference_oracle.py` imports
`csc.world.ProductionWorld`, `csc.world.domain_metrics`, and
`csc.compare.utility`. `experiments/reference_fidelity_factorial.py` constructs
the reference in process from the same anchors, events, configuration, action
contract, and production transition implementation. The manifest explicitly
labels it `AUTHORED_PRODUCTION_SOFTWARE_ENVIRONMENT` and
`in_process_sem_evaluation`.

**Assessment.** This is a valid test of whether `ShadowWorldModel` tracks the
authored production transition for given exogenous windows. It is not an
independent implementation of the authoritative transition, an observed
alternative outcome, or physical/factual counterfactual ground truth. Shared
production, metric, action, and input assumptions can carry common defects into
both sides.

**Alternative explanation.** A software oracle may be exactly the intended
ground truth for a bounded unit test. That supports the narrow SEM-calibration
claim, provided the label remains precise.

**Required disposition.** Preserve the current reference-kind label in every
table and report. For a stronger software validity claim, implement a separately
maintained transition and metric oracle with mutation tests showing it can detect
errors in `ProductionWorld`; for external validity, compare against observed or
validated simulator outcomes. Neither change alone establishes safety or
learning benefit.

## MAJOR

### M1 - The replacement path did not select a changed rule and cannot rescue the result

**Evidence.** The calibration selection file at
`research/tables/confirmatory-factorial-calibration/reference-factorial-replacement-selection.json`
selects multiplier 1.0, because it is the smallest qualifying candidate. The
replacement-evaluation series consequently also uses multiplier 1.0, as shown
in its manifest and report. It still fails 23 of 36 cells.

**Assessment.** This is a valid predeclared result, not evidence of tuning
misconduct. It means the replacement arm is a held-out replication of the
original threshold, not evidence that a new threshold repaired it. Calling it a
successful replacement would be inaccurate.

**Required disposition.** Describe multiplier 1.0 as “no replacement selected”
or “original gate retained for held-out replication,” and report the held-out
global failure. Any new multiplier/regime-specific rule requires a new,
predeclared calibration and evaluation split.

### M2 - Calibration selection pools correlated factorial rows for its overall criterion

**Evidence.** `experiments/analyze_reference_factorial.py:select_multiplier`
takes a median across every run in the 720-row calibration series. The same seed
contributes repeated matched runs across horizons, mismatch regimes, and other
conditions, sharing anchor construction and future input windows. The amendment
correctly identifies one seed x cell as a run-level unit, but this overall
selection aggregation treats the correlated rows as a single flat collection.

**Assessment.** The frozen selection returned 1.0 and the held-out study fails
regardless, so this defect does not reverse the negative conclusion. It would
invalidate a future claim that an aggregate calibration threshold is confirmed
without a cellwise or seed-clustered analysis.

**Alternative explanation.** The selection rule uses medians against operational
thresholds rather than a p-value, so it does not literally assert 720
independent samples. Correlation still changes the weight given to a seed and
can conceal factor-specific failure.

**Required disposition.** In future selection, require all cells to pass, or
first reduce each seed across the factorial and use a cluster-aware criterion.
Report both cellwise and seed-clustered results. Do not use an aggregate median
to choose a global operational rule after a cellwise rule has failed.

### M3 - The factorial establishes a model-to-model comparison, not realised control outcomes

**Evidence.** The driver calls `execute_shadow` directly and evaluates
`reference_outcome` for each action. It does not run an authoritative production
branch for the anchor during the factorial; the reference itself supplies the
production-action utility. `make_anchor` also creates every anchor using
`ProductionWorld` with heterogeneity disabled, then evaluates some conditions
with heterogeneity enabled.

**Assessment.** Common random inputs and fixed anchors are appropriate for
isolating short-horizon transition differences. They do not show what a
closed-loop policy would actually encounter under each mismatch regime, and
anchors may be off-distribution for a production history with heterogeneity
enabled. The result therefore concerns local simulation fidelity at constructed
anchors.

**Required disposition.** Retain “authored model calibration at fixed anchors”
as the result scope. For policy claims, generate anchors from the matching
authoritative regime and evaluate closed-loop alternatives or observed outcomes
under a justified exogeneity contract.

### M4 - Decision endpoints remain coarse because each run has only three anchors

**Evidence.** `anchors_per_run` is 3. Run-level precision, false-positive rate,
and abstention therefore take a small set of discrete values. Several reported
precision values are undefined because a run makes no recommendation. The
analyzer correctly preserves undefined precision and the amendment says it
fails the support rule, but the report tables omit the bootstrap intervals they
calculate.

**Assessment.** Twenty seed-runs per cell meets the declared replication count,
but three constructed anchors give limited resolution for tails and operational
rates. Medians can also hide how many recommendations actually occurred.

**Required disposition.** Keep the predeclared pass/fail result, but include
gate count/exposure, undefined-precision counts, and run-bootstrap intervals in
any summary. A future decision-rule study should increase and diversify anchor
episodes independently of the seed, while preserving seed-level clustering.

## MODERATE

### O1 - Source identity is checked but historical executable recovery is incomplete

The series manifests hash current CSC and selected experiment files, and the
verifier confirms those hashes today. They do not contain an archived source
bundle or immutable interpreter/container image. `verify_reference_factorial.py`
is recorded only by the generated verifier hash, not as a manifest source input.
Future source changes can prevent replay without supplying the historical
executable. Archive a source bundle/container digest with the series and include
all generator, oracle, analyzer, and verifier sources in the recorded identity.

### O2 - The manifest is self-authenticating rather than independently anchored

`series-manifest.json` lists hashes for the other outputs but is itself not in a
separately protected hash or signed provenance record. This is adequate for
ordinary local integrity checking, not for adversarial chain-of-custody claims.
Write a detached manifest digest or signed release record if evidence must be
transported or independently audited outside this workspace.

### O3 - The adverse mismatch level combines mechanisms

`rate-and-incident-omitted` changes both SEM service rate and incident
knowledge. Its failures correctly falsify robustness to that combined authored
mismatch, but they cannot identify which mechanism caused each failure. Future
factorials should include rate-only and incident-knowledge-only cells before
making mechanism-specific claims.

### O4 - Aligned controls are pipeline checks, not broad calibration evidence

The aligned-control shares the stated transition choices between SEM and the
authored reference. Its strong cells show correct wiring under an intentionally
matched model; they should not counterbalance failed adverse cells or be cited
as support for model validity outside that control.

## Evidence that survives this review

- The design, seeds, conditions, endpoints, tie rule, thresholds, and
calibration/evaluation separation were frozen before the reported series in
`research/evidence/cycle2/confirmatory_factorial_amendment.md` and each series' `frozen-design.json`.
- Conditions were shuffled using the recorded ordering seed, all three series
have no failed runs, and every run has three comparable anchors according to the
stored summaries.
- The analysis uses run/seed x cell summaries rather than treating anchors as
independent observations for the reported cell medians.
- The held-out evaluation preserves the negative result; it does not conceal
the lack of universal support.

## Learning decision

**Do not implement or enable learning.** The factorial fails the full-cell gate
criterion even in its constrained authored environment. It also lacks an
independent external oracle, realised policy outcomes, hostile-containment
validation, asynchronous non-interference evidence, and a conservative learner
protocol. The appropriate next step is to preserve the failure, refine the
validity protocol, and only then consider another bounded calibration study.

## Limitations

This review did not rerun the 2,160 anchor evaluations, recalculate every table
from source, or audit the host execution environment. It did check stored
series structure, declared hashes, source identity, cell counts, and reported
gate outcomes. The evidence supports a narrow falsification result in the
authored software environment; it does not support general CSC validity.
