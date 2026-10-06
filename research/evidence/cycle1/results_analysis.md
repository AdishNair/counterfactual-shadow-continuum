# Results analysis: local CSC evidence audit

**Status:** Audited 2026-09-28. All results below are preliminary local smoke evidence in the Junction J1 software environment.

## Question

What do the declared matrix and validation artifacts support after preserving the proper run/seed unit, source provenance, and incomplete comparisons?

## Evidence and method

This audit read `results/matrix/matrix-summary.json`, its 15 referenced raw run directories, `results/matrix/REPORT.md`, `results/matrix/replay-verification.json`, and `results/validation/validation-summary.json`. A deterministic read-only audit recomputed every manifest artifact hash for the 15 indexed matrix runs and 18 indexed validation runs: 0 hash failures. Calculations use indexed post-warm-up summaries, not all similarly named directories under `results/`.

The matrix has five paired workload seeds, with one run at each K. Each summary contains 90 measured epochs, but the independent count for a K comparison is five. Every seed triplet has identical workload and production semantic hashes across K. Each matrix summary records 100 authoritative production commands and zero unexpected shadow-originated mutations under its application-boundary audit.

## Matrix findings

| K | Independent runs | Median of run-median epoch time (ms) | Median of run-median production-decision time (ms) | Median mirror gap | Median beaten rate |
|---:|---:|---:|---:|---:|---:|
| 0 | 5 | 1.6169 | 0.1848 | N/A | N/A |
| 1 | 5 | 135.1413 | 0.2578 | 0.7500 | 0.4778 |
| 2 | 5 | 145.6411 | 0.2605 | 0.7500 | 0.4778 |

The seed-paired median epoch-time changes are +133.5170 ms for K=1-K=0, +144.0242 ms for K=2-K=0, and +11.5590 ms for K=2-K=1. All five paired differences are positive in each comparison. The effect is dominated by the collection barrier: median barrier time is 0.0014, 131.3703, and 141.1876 ms at K=0, K=1, and K=2. This supports the narrow conclusion that the current spawned-worker, synchronized local harness has substantial added epoch latency as K is enabled and increased. It does not measure a warmed, remote, or asynchronous deployment.

Complete fraction is 1.0 in every K=1/K=2 matrix run and indexed branch exclusions total zero. The common 0.75 median mirror gap is an authored-model calibration signal. It is neither an error bound for alternatives nor a confidence interval. Median discounted regret is zero in both CSC conditions; the nonzero beaten rate means that median-zero must not be read as evidence that alternatives were never estimated better.

The recorded matrix replay verification reports 4,000 replayed branch trajectories and zero mismatches. It supports reproducibility for the recorded local implementation, not counterfactual truth or containment.

## Validation findings

The validation index has one eight-epoch run per fault scenario. For none, crash, timeout, drop, duplicate, reorder, delay, model-error, resource-budget, and capture, the saved result reports production digest equality with its paired baseline. Crash, timeout, drop, and model-error each exclude one branch; resource-budget and capture have fewer replayed branches because the scenario changes planned availability. These are local regression checks, not failure-probability estimates.

One two-mirror run reports 0 disagreements across 8 same-action comparisons. Incident-horizon runs report median mirror gaps of 0.5 (h=2), 0.9167 (h=6), and 1.0 (h=20), one run per horizon. The pattern is hypothesis-generating, not a supported horizon effect. Exact-control has median gap 0.0 and deliberately biased-sem has 6.1667, showing sensitivity within authored models rather than fidelity to an external world. No-mirror has no epsilon as required; no-sync-reorder excludes one comparison.

## Timing provenance and primary-evidence rule

`RESULTS.md`, `research/RESEARCH_CONTEXT.md`, and `research/RESEARCH_STATUS.md` quote matrix epoch medians of 4.3614, 169.3680, and 189.9336 ms. They do not match the declared primary matrix index or its current generated `results/matrix/REPORT.md`, which give 1.6169, 135.1413, and 145.6411 ms.

For this audit, the primary evidence is the indexed raw summaries named by `results/matrix/matrix-summary.json`, subject to manifest-hash verification. The higher-level figures are treated as stale or as an unindexed distinct run series until their provenance is reconciled. They must not be combined with the indexed series, used for effect calculations, or cited as the current matrix result without an explicit source correction.

## Confirmatory reference-fidelity factorial

The new immutable series are separate from all historical output:
`results/reference-fidelity/confirmatory-evaluation-20260928`,
`confirmatory-calibration-20260928`, and
`confirmatory-replacement-evaluation-20260928`. Each has 720 shuffled planned
seed/cell runs, 2,160 matched-anchor observations, 6,480 action observations,
zero failed runs, and verified artifacts/source identities. The design was
frozen in `research/evidence/cycle2/confirmatory_factorial_amendment.md` before collection.

The independent unit is the seed x factorial cell run; each run reduces its
three anchors to rates or summaries. The reference evaluates all actions in the
authored `ProductionWorld` without importing `ShadowWorldModel`. It therefore
tests SEM calibration against this authored production-model family, not a
physical, factual, or closed-loop alternative outcome.

The fixed gate `estimated_improvement > epsilon` failed its predeclared global
criterion. The first evaluation had 15/36 passing cells and a fully disjoint
evaluation had 13/36. Eleven cells passed in both, concentrated in named
light-demand conditions; no validated classifier exists to recognize those
conditions safely. The calibration block selected multiplier 1.0, so it did not
produce a changed conservative replacement. The correct global classification
is **D: counterfactual validity not established** for policy use.

The seed-level mirror-error to alternative-error Spearman association varied
from -0.306 to 0.990 across 45 nonconstant cell/block estimates (median 0.522),
with many broad bootstrap intervals. This shows condition-dependent association,
not a uniformly conservative prediction. The detailed seed-level tables are in
`research/tables/confirmatory-factorial-synthesis/`; the independent review is
`research/evidence/cycle2/red_team_factorial_review.md`.

## Limitations and next actions

Evidence strength is low for general performance, physical fidelity, safety, and
every deployment claim. Preserve the confirmed negative gate result. A future
validity study needs a separately implemented/validated reference, matching
closed-loop anchor histories, more diverse anchors, isolated rate and incident
mismatch factors, and a predeclared regime-detection abstention policy with a
new held-out test.
