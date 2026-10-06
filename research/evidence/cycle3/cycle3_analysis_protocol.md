# Cycle 3 exploratory analysis protocol

**Status:** Frozen before Cycle 3 derived analyses, 2026-09-28. This is an
exploratory analysis of completed immutable evidence, not a new confirmatory
experiment and not a threshold-selection exercise.

## Purpose

Explain the Decision D failure by characterizing where same-action mirror error
does and does not track alternative-action error in the completed authored J1
factorial. The question is whether a structural extrapolation mechanism is a
plausible explanation, not whether a post-hoc gate can be made to pass.

## Inputs and units

Use only the three immutable confirmatory factorial series and their verified
raw anchors, input windows, anchor observations, and action observations. The
seed x factorial cell run remains the independent unit. Its three anchors are
repeated observations for descriptive within-run summaries; they must not be
treated as independent replication. Any derived trace is a deterministic replay
from the saved anchor/window under recorded source identity and is labelled
derived analysis data.

## Predeclared descriptive questions

1. Locate false confidence (low mirror error with high alternative error) and
   unnecessary abstention (high mirror error with low alternative error), using
   thresholds defined only from each series' descriptive distribution and never
   as an operational proposal.
2. Summarize errors and gate outcomes by horizon, demand, incident, mismatch,
   production action, alternative action, action change, queue imbalance, and
   predicted/reference gain magnitude.
3. Derive mirror-versus-alternative trajectory distance, including integrated,
   maximum, and terminal queue distance, and describe its association with
   alternative error. This probes the structural hypothesis; it cannot establish
   that divergence causes error because both may share factors.
4. Compute analysis-only oracle bounds: whether any reference-beneficial
   alternative exists, the best reference action, and the gap from the CSC
   selected action. Oracle values must not appear in any CSC decision signal.

## Boundaries

No completed result is rerun, replaced, filtered for a favorable answer, or used
to tune a new operational threshold. Calibration/evaluation/held-out series are
named separately in every derived table. Any candidate trust mechanism designed
after this exploration must use new development, calibration, and final
held-out seeds under a later frozen protocol.

## Interpretation

Report counts, run-level distributions, and bootstrap intervals where useful.
Call every association descriptive. A credible structural hypothesis requires
observable consistency across the independent evaluation blocks; it remains
falsified or inconclusive if high divergence does not consistently co-occur with
alternative error, or if the proposed signal does not outperform mirror-only
behavior in a new held-out experiment.
