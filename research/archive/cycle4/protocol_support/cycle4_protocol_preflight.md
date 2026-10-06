# Cycle 4 protocol preflight

**Status:** Pre-outcome methodological review, 2026-10-05. Development collection
approved after the corrected implementation checkpoint and immutable archive
freeze; calibration and final progression require their own checkpoints. No Cycle 4
development, calibration, or final held-out outcomes were inspected for this review.

## Question and evidence

Can the frozen Cycle 3 trust study be implemented without outcome-dependent
discretion, and what conclusions could its gate justify?

Reviewed: `AGENTS.md`, `research/RESEARCH_CONTEXT.md`,
`research/RESEARCH_STATUS.md`, `research/archive/cycle4/protocol_support/trust_signal_experiment_protocol.md`,
`research/evidence/cycle3/async_noninterference_design.md`, and
`research/evidence/cycle3/red_team_cycle3_review.md`. This is a design review, not a new broad
repository audit. Reviewer role: Cycle 4 research director; the available model
configuration is GPT-6 Astra, not a Terra-labelled model.

## Frozen requirements

- Preserve the 60 full-factorial cells, eight anchors per seed/run, and distinct
  development 801--820, calibration 821--840, and final 841--860 seeds.
- Development validates feature calculation. Calibration alone generates the
  four global nearest-rank divergence thresholds and selects among the frozen
  baseline, divergence, and divergence/horizon families.
- Every calibration cell must satisfy the stated exposure, coverage, precision,
  false-positive, and abstention criteria. Undefined precision is not a success.
  Preserve failed cells and all run denominators.
- No qualified candidate means Decision D and no final held-out generation or
  inspection. The request for three series is conditional on this stricter gate;
  a skipped final series must be documented, never simulated as completed.
- Before a permitted final study, freeze source, selector choice, calibration
  output, report template, and qualification/decision logic with hashes.
- References remain authored software. Source isolation is necessary for this
  study, but does not establish independently correct physical dynamics.
- Trust and async evidence answer different questions. Neither rescues failure
  in the other. No learning implementation is authorized.

## Implementation specification required before outcomes

The prose protocol leaves some executable details to implementation. Resolve
these deterministically and record/hash them before any development collection:

1. Numeric regimes for heterogeneity, service rates, and incident knowledge;
   eight-anchor schedule and matching authoritative closed-loop histories.
2. Selected-alternative tie ordering, integrated queue-distance scale, window
   alignment, and semantics of missing or unsupported input metadata.
3. Eligible and comparable populations; precision, false-positive and
   false-negative denominators; treatment of zero denominators and incomplete
   runs; bootstrap aggregation preserving seed clusters across cells.
4. Feature allowlist/firewall, raw feature logging, and concrete adversarial
   tests for unknown, misdeclared, missing, and late incident information.
5. Development diagnostics. Calibration-defined thresholds do not exist yet:
   development can validate family code and feature computation, but must not
   choose new outcome-optimized thresholds or family definitions.

These specifications fill missing operational detail; they cannot change the
frozen grid, all-cell rule, exposure thresholds, or admissible selector inputs.
If implementing them reveals an actual pre-existing scientific defect, halt
collection and record a prospective amendment before generating evidence.

## Pre-outcome timing defect and scope amendment

The implementation checkpoint confirmed a pre-existing temporal defect in the
phrase "online-observable" if interpreted as available before the current
anchor's production actuation. The frozen baseline computes epsilon as the
absolute difference between same-window SEM mirror utility and realized
production utility. Realized utility is available only after the H-tick window.
Trajectory divergence also requires completed SEM rollouts; this offline study
supplies the future event window to both implementations.

**Prospective amendment, before any new outcome generation:** retain exactly
the frozen factors, splits, selectors, metrics, and qualification rules, but
narrow the inferential target to a prospectively held-out evaluation of a
post-window, common-input evidence selector in authored software. The experiment
does not establish availability or reliability of a trust signal before the
current production decision. No lagged epsilon, newly predicted window, or new
selector is substituted. Such changes would require a separate future protocol.

This scope amendment addresses an existing scientific defect rather than a
response to results. It is authorized by the user's pre-outcome-defect clause.
The engineer must include the timing/scope statement in the executable study
freeze before collection. Even if the software gate passes, the original
current-anchor decision-time question remains unestablished.

## Structural limitations, not grounds for amendment

The horizon cutoffs 2 and 6 abstain throughout excluded horizon cells. They
therefore necessarily fail the all-cell exposure requirement. A qualifying
divergence/horizon rule can only use h=20, where the horizon restriction is
nonbinding for this factorial. Preserve these candidates and their failures;
do not remove long-horizon cells or relax the gate to make them competitive.
Consequently the frozen primary study cannot establish an incremental positive
benefit from a binding horizon cutoff while also passing its global criterion.
Descriptive condition-specific behavior does not change that conclusion.

A largest observed divergence threshold may coincide with baseline on
calibration observations. Report that equivalence explicitly and deduplicate
according to the frozen implementation rule. Observed equivalence does not
prove equivalence on future data or establish incremental divergence value.

The all-cell gate is deliberately demanding. A negative gate can arise from
insufficient recommendation opportunities, abstention, inaccurate labels, or
poor discrimination. Distinguish these mechanisms in the report rather than
claiming every failure proves the feature contains no predictive information.

## Decision semantics and limitations

The frozen protocol assigns D to any failed cell, no calibrated candidate,
missing reference check, or failed source identity. The requested A/B/C/D
reporting vocabulary cannot create a positive conditional category by selecting
successful cells afterward. Report replication failure descriptively if it
occurs, retaining D as the frozen decision. A positive result would support only
prospective prediction under tested software conditions; it would establish
neither causation nor general-domain reliability.

The protocol explicitly states that this evidence cannot enable learning.
Even a positive trust result therefore leaves learning blocked in Cycle 4.

## Next action

Review the engineer's compact dependency audit, bidirectional transition/metric
mutation tests, serialization tests, source/config freeze, and deterministic
endpoint tests. Authorize development only when these controls pass. Freeze its
feature-validation report before calibration; review qualification before any
final-held-out action.

## Implementation checkpoint: correction required before collection

Reviewed `research/archive/cycle4/protocol_support/cycle4_trust_preoutcome_specification.md`,
`research/archive/cycle4/protocol_support/cycle4_trust_source_isolation_audit.md`,
`research/archive/cycle4/protocol_support/cycle4_trust_preflight_verification.json`,
`experiments/trust_selector.py`, and the analysis/qualification functions in
`experiments/analyze_cycle4_trust.py` before outcomes. The audit reports eleven
passing import, serialization, mutation, and semantic-firewall tests. Reference
dependency closure is restricted to standard-library `copy` and `random`;
shared action/input semantics and PRNG specification remain explicit limitations.

**Collection remains blocked:** the first analyzer treated all non-development
input as calibration, which would recompute candidate thresholds on final
outcomes. It also omitted the final baseline-relative false-positive and 80%
coverage checks. Required remedy: separate final evaluation, accept only the
previously frozen selected rule after prerequisite verification, never generate
candidates from final outcomes, and test both no-retuning and baseline-relative
failure behavior. This is an implementation correction to the existing protocol,
not a protocol amendment. It was identified before any research outcomes.

The implementation treats any run with undefined precision as a cell failure.
The frozen phrase "for every cell, undefined precision ... is a failure" does
not explicitly say whether it concerns run precision or aggregate cell precision.
The conservative run-level reading is acceptable when disclosed and frozen
prospectively, but it must not be described as the only possible reading. It
effectively requires all twenty runs to recommend at least once, making the
separate twelve-recommending-runs check redundant. Report that implication.

## Corrected checkpoint and development authorization

The director reviewed the corrected `final_gate`, final phase path, and four new
fixtures, then independently executed
`python -m unittest tests.test_cycle4_trust -v`: **15 tests passed**. The final
analysis gate now checks selection, bundle identity, and prerequisite digest
before opening outcomes. It evaluates baseline and the previously frozen rule
without calling the candidate generator; every final cell additionally requires
nonworse baseline false-positive rate and at least 80% of baseline coverage.
Fixtures cover no-selection prevention of generation and analysis, frozen-rule
use without recalibration, and independent baseline coverage/FPR failures.

**Decision:** authorize development collection once the corrected source,
pre-outcome specification, and report/verifier implementation are archived and
hashed. This approves only the amended post-window software estimand. Freeze
the development feature-validation result before calibration. This checkpoint
does not authorize final-held-out generation or inspection.

## Development checkpoint and calibration authorization

Reviewed the compact frozen feature-validation record at
`research/tables/cycle4-trust-development-v1/development-freeze.json`, referencing
`results/cycle4-trust/development-20261005-v1`. Verification passed with 1,200 runs,
60 cells, seeds 801--820, 9,600 anchors, 28,800 replayed action pairs, no split
overlap, and no reported errors. The report records no performance selection.
The immutable source bundle digest is
`d190fcb2afa01d6c49c48e7b6ebb8071c6b53151d75d56a5747ea35c2debe5de`.

**Decision:** authorize calibration seeds 821--840 under that unchanged bundle
after freezing the development gate. Development reports 7,680 available and
1,920 unsupported-semantic observations. Preserve the latter as abstentions;
do not remove their cells or relax exposure. Their structural zero-coverage
implication must be distinguished from any empirical lack of discrimination.
No final-held-out generation or inspection is authorized by this checkpoint.
