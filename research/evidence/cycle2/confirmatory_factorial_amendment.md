# Confirmatory reference-fidelity factorial amendment

**Status:** Pre-execution amendment, 2026-09-28. This document was written
before collecting the confirmatory series.

## Defect in the prior proposed protocol

`research/evidence/cycle1/experiment_protocol.md` correctly required independent seed/run
replication, an independent reference, fixed factors, and at least 20 seeds.
It did not freeze the factor levels, seed allocation, anchor construction,
condition order, endpoint denominators, tie handling, decision criteria, or a
calibration/evaluation split. The former smoke driver also changed horizon by
changing workload/incident placement and collected its nested-loop conditions in
a fixed order. It cannot serve as the confirmatory factorial unchanged.

The following amendment resolves those defects without using any confirmatory
outcome. It supplements rather than revises the historical smoke evidence.

## Scope and independence

The target is SEM calibration in the authored J1 production software model.
For each saved anchor the reference evaluates every action with
`ProductionWorld` and never imports or calls `ShadowWorldModel`. This is
independent relative to the SEM; it is neither physical ground truth nor a
factual causal counterfactual. Artifact/source verification is a separate step
and is not part of the reference evaluator.

## Frozen design

The machine-readable design is `experiments/reference_fidelity_factorial.json`.
It contains the exact seeds, levels, randomization seed, endpoint definitions,
and decision rules. The driver copies and hashes it into the new immutable
series before work begins.

- **Independent unit:** one seed x full factorial cell. Three anchors are
  repeated observations within that run and are reduced to run-level rates or
  summaries. Epochs/anchors never become independent replicates.
- **Evaluation seeds:** 521--540 (20 independent seeds per full cell).
- **Factors, fully crossed:** horizons {2, 6, 20}; demand {light, peak};
  incident {none, blocked-EW}; mismatch {aligned-control,
  heterogeneity-omitted, rate-and-incident-omitted}.
- **Mismatch levels:** aligned-control uses production heterogeneity false,
  SEM rate 2 and SEM incident knowledge true; heterogeneity-omitted sets
  production heterogeneity true with the same SEM settings; rate-and-incident-
  omitted additionally sets SEM rate 4 and SEM incident knowledge false.
  These are named authored-model conditions, not measurements of real-world
  model error.
- **Anchor bank:** it is generated from production-only deterministic history,
  before any SEM setting is applied. Each horizon uses a prefix of the same
  saved 20-tick future window from that anchor. Thus horizon does not alter the
  anchor or incident placement. Conditions sharing seed/demand/incident/anchor
  must have the same anchor and input hashes.
- **Execution order:** all 720 evaluation runs are shuffled once using the
  recorded order seed; the frozen schedule is written before the first run.
- **Exclusions:** an anchor is non-comparable if it lacks exactly one production
  reference, one matching mirror estimate, and one estimate for each alternative,
  or has an invalid window/hash/non-finite utility. It remains in raw output and
  in an explicit incomplete denominator. No utility or decision is imputed.

## Endpoints and ties

For every comparable anchor, retain every action's shadow estimate and reference
utility; mirror/alternative signed and absolute errors; estimated/reference gain
against production; gain error; selected and per-action epsilon coverage; full
action ranking; recommendation outcome; and reference choice-value loss.

An action tie is a utility difference at most 1e-9. Full ranking agreement
requires equal best-action sets. The selected alternative is the first action in
the fixed `ACTIONS` order among tied estimated alternatives. The fixed current
decision rule is `estimated_improvement > epsilon`. It abstains otherwise;
epsilon-unavailable and incomplete anchors are separate abstention/exclusion
reasons.

For a comparable anchor, a positive reference outcome means the selected
alternative has reference improvement strictly greater than zero. A gate pass
with a positive reference outcome is TP; a gate pass otherwise is FP; an
abstention with any reference-beneficial alternative is FN; an abstention with
none is TN. Regret-sign agreement compares the sign of the best estimated
alternative gain with the sign of the best reference alternative gain.

Primary endpoint: each run's selected-alternative epsilon-coverage proportion.
Secondary endpoints: run-level precision, FP/FN rates, abstention, ranking and
regret-sign agreement, per-action error/coverage, and choice-value loss. Report
cell summaries and nonparametric seed-bootstrap intervals; do not pool anchors
as independent observations.

## Decision and replacement plan

The current gate is supported in a cell only when its 20 evaluation runs have
median precision >= 0.95, median false-positive rate <= 0.05, and median
abstention < 0.95; undefined precision fails the criterion. Overall support
requires every full cell to satisfy these criteria. Conditional support requires
the criteria to hold only in explicitly reported cells and does not authorize
use outside them.

If the current rule fails, the only predeclared replacement investigation is a
multiplier rule `estimated_improvement > m * epsilon`, with m in
{1.0, 1.5, 2.0, 3.0}. It uses calibration seeds 541--560 and different held-out
evaluation seeds 561--580, each with the same complete factorial. Select the
smallest multiplier whose calibration runs have overall median precision >=
0.95, median false-positive rate <= 0.05, and median abstention < 0.95. If none
qualifies, no replacement is selected. A selected multiplier is evaluated once
on held-out seeds; it cannot be re-tuned. A replacement can receive support only
if the held-out criteria hold, with any surviving cells stated explicitly.

These operational thresholds are research decision rules for this bounded
software experiment, not safety guarantees. Learning remains blocked regardless
of outcome until the final red-team review explicitly concludes otherwise.
