# Reference-fidelity smoke analysis

**Status:** Measured preliminary evidence, 2026-09-28.

## Question

Can a same-action mirror threshold (`epsilon`) serve as an error bound for the
selected alternative branch, and do branches preserve the action ranking in a
reference computation that is independent of the SEM?

## Method

`experiments/reference_fidelity.py` reads each saved CSC run, verifies its
artifact and recorded CSC source identity through `experiments.replay`, then
replays every action from the same saved anchor and common inputs in the authored
`ProductionWorld`. The reference module does not import `ShadowWorldModel`.

The immutable smoke series crosses two seeds, horizons 2 and 6, and shadow
service rates 2 and 4. Each run has 18 post-warm-up epochs. Per run it records
mirror absolute error, alternative absolute error, all-action ranking agreement,
and whether epsilon covers the selected alternative's estimated-gain error.
The deterministic reporting script is `experiments/analyze_reference_fidelity.py`.

## Evidence

- Raw immutable series: `results/reference-fidelity/all-action-smoke-20260928`
- Run-level table: `research/tables/reference-fidelity-smoke-runs.csv`
- Aggregated table: `research/tables/reference-fidelity-smoke.md`
- Verification: `research/tables/reference-fidelity-smoke-replay-verification.json`

The independent verifier replayed all eight runs, covering 640 reported branch
trajectories, with zero trajectory mismatches. Each manifest's recorded 13 CSC
source files and artifact hashes also verified.

Across the four two-run cells, median rank agreement was 0.8333--0.9722. Median
epsilon coverage was 0.6111--0.7222; individual runs ranged from 0.3889 to
0.8333. Mirror and alternative error therefore differ, and the current epsilon
gate is not a uniformly covering selected-alternative error bound in this smoke
study.

## Limits and decision

This reference is independent only relative to the SEM. It shares the authored
software environment with production, is not a factual counterfactual outcome,
and does not validate physical traffic. Two seeds per cell and structured
incident timing prevent stable uncertainty estimates or causal claims about
horizon or mismatch. Do not use this evidence to enable learning or policy
actuation.

Run the predeclared replicated factorial in `research/evidence/cycle1/experiment_protocol.md`
before selecting a horizon, a confidence threshold, or a decision rule.

## Confirmatory factorial result

**Status:** Measured and red-team reviewed, 2026-09-28. The smoke series above
is unchanged and remains separate evidence.

The serious pre-execution protocol defect was documented before collection in
`research/evidence/cycle2/confirmatory_factorial_amendment.md`. The frozen factorial crossed
three horizons, two demand regimes, two incident regimes, and three named
authored mismatch regimes. Each full cell had 20 seed/run units and three
matched anchors per run. Horizons used prefixes of the same saved 20-tick input
window. The independent reference module imports `ProductionWorld` but not
`ShadowWorldModel`; it is therefore an SEM-relative authored-software reference,
not external or physical ground truth.

The primary evaluation series has 720 runs, 2,160 anchors and 6,480 action
observations. Artifact and source identity verified. It failed the frozen
all-cell gate criterion: 15 of 36 cells passed. A disjoint 20-seed calibration
block selected the predeclared smallest multiplier, 1.0, so no changed
replacement was selected. Its separate held-out evaluation again failed (13 of
36 cells passed). Only 11 cells passed in both evaluations; no regime detector
or abstention policy was evaluated to identify those cells safely at use time.

Run-level Spearman associations between mirror and alternative absolute error
were non-uniform across nonconstant cells (range -0.306 to 0.990; median 0.522)
and their seed-bootstrap intervals were often wide. The gate-margin to reference
gain relationship was also condition-dependent. These descriptive associations
do not establish a transferable predictive calibration rule.

**Decision:** **D. Counterfactual validity is not established** for using the
current gate or a replacement for policy decisions. Preserve the conditional
cell observations as model-calibration evidence only. See
`research/evidence/cycle2/red_team_factorial_review.md` and
`research/tables/confirmatory-factorial-synthesis/cross-holdout-synthesis.md`.
