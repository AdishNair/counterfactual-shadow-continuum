# Next trust-signal experiment protocol

**Status:** Proposed and frozen before implementation or data generation,
2026-09-28. This protocol follows Decision D; it does not rerun, retune, or
reinterpret the completed factorial.

## Question

Does a small, online-observable abstention signal based on selected-alternative
SEM trajectory divergence and horizon predict recommendation reliability better
than mirror epsilon alone in the authored J1 environment?

## Scope and reference

Implement a separately maintained production transition-and-metric reference
package that does not import `csc.world`, `csc.compare`, or any SEM module.
Collection is blocked until reviewed source-isolation, no-SEM-import, source-
bundle digest, serialization-contract, and bidirectional transition/metric
mutation tests pass. This remains software-environment reference, not physical
or factual ground truth.

Generate anchors using matching authoritative-regime histories, not the fixed
heterogeneity-disabled anchor process used in the prior factorial. Preserve
common exogenous windows within anchor/action comparisons. The independent unit
is a seed x full-cell run with eight anchors; anchors are repeated observations.

## Frozen factors and splits

- Horizons: {2, 6, 20}; demand: {light, peak}; incident: {none, blocked-EW}.
- Mismatch: aligned control; heterogeneity-only; rate-only; incident-knowledge-
  only; combined rate-plus-incident. Each is reported separately.
- Development seeds: 801--820. They validate feature calculation only.
- Calibration seeds: 821--840. They select a candidate or record no selection.
- Final held-out seeds: 841--860. They are not inspected until code, candidate,
  selection rule, and reports are frozen.
- Run order is a saved deterministic shuffle. A new unique immutable series
  records source/config/environment identity, raw traces, exclusions, and a
  source-bundle digest. The completed Cycle 2 held-out series are exploratory
  hypothesis-generation data only for this study; they cannot support its
  performance claim. Final-held-out records remain unread until source identity,
  calibration output, selector choice, and report template are committed.

## Candidate rules

All rules require `estimated_improvement > epsilon`. Unsupported or unknown
required input semantics force abstention. The selector feature allowlist is:
anchor state; supplied window; horizon; static SEM capability declaration; and
SEM/mirror/alternative outputs, including selected-alternative-to-mirror SEM
trajectory distance. It excludes mismatch-regime labels, reference outcomes,
oracle columns, and retrospective incident labels. Log every feature and add
unknown/misdeclared/late incident-metadata tests.

1. **Baseline:** existing condition only.
2. **Divergence selector:** baseline plus selected-alternative integrated SEM
   queue divergence from the mirror no greater than `d`.
3. **Divergence/horizon selector:** rule 2 plus horizon no greater than `h`.

The calibration grid is frozen. Form one selected-alternative divergence value
per comparable calibration anchor, sort all such values globally, and define
quantile `q` as the value at zero-based index `ceil(q*N)-1`. Candidate `d` uses
q in {0.25, 0.50, 0.75, 1.00}, accepts `divergence <= d`, and is labelled
baseline-equivalent when it accepts every comparable calibration anchor. `h` is
one of {2, 6, 20}. Exclude duplicate candidate rules before selection.
If there are zero comparable calibration anchors, skip quantile calculation,
select no candidate, and record **D**. Before producing or reading any final
held-out record, commit and hash the executable factor/config generator,
reference package, selector, analysis, verifier, report template, and firewall
enforcement code in the immutable series manifest.

For every cell, undefined precision, fewer than two recommended anchors in the
median run, fewer than 12 recommending seed-runs of 20, or median coverage
below 0.25 is a failure. A candidate qualifies only when every calibration cell
has median precision >= 0.95, median false-positive rate <= 0.05, median
abstention < 0.75, and the exposure requirements above. Select the qualifying
rule that maximizes the *minimum* cell median coverage; then maximize the mean
cell median coverage; ties favor baseline, simpler rule, smaller `d`, then
shorter `h`. If none qualifies, select none.

## Endpoints and decision

Primary endpoint: held-out seed/run-level false-positive recommendation rate by
full cell. Secondary endpoints: precision, false-negative rate, abstention,
recommendation coverage, selected-alternative epsilon coverage, ranking/regret-
sign agreement, oracle choice-value loss, incomplete rate, and calibration/
coverage error. Report seed-bootstrap intervals without pooling anchors.

The selector receives support only if every held-out cell satisfies the same
precision/false-positive/abstention/exposure criteria, matches or improves the
baseline false-positive rate, and has median coverage at least 80% of baseline
coverage in that cell. Report undefined-precision runs in every denominator.
Any cell failure, no calibrated candidate, missing reference check, or failed
source identity yields **D**. This evidence cannot enable learning.

## Oracle bound

The reference-only oracle reports whether a better alternative exists, maximum
recommendation coverage with perfect information, selected-action value loss,
and coverage lost by abstention. These values exist only in analysis/reference
records and cannot enter normal CSC branches, comparison, or actuation.

## Falsification value

If the selector fails, it shows that observable trajectory divergence/horizon
does not repair the mirror's structural blind spot under declared mismatches.
That outcome advances the research by rejecting a simple explanation rather
than inviting threshold search.
