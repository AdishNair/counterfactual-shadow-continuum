# CSC uncertainty taxonomy

**Status:** Hypothesis and analysis model, 2026-09-28. It is not a validated
uncertainty decomposition or a policy certificate.

| Component | Meaning | Current observable | What it cannot establish |
|---|---|---|---|
| A. Same-action model error | Difference between mirror and reference under the production action. | Mirror absolute utility error, `epsilon`. | Error after an unexecuted action changes the trajectory. |
| B. Counterfactual extrapolation error | Extra discrepancy from evaluating an alternative trajectory outside the mirror trajectory. | Candidate proxy: alternative-versus-mirror SEM trajectory divergence. | Causation, factual outcomes, or a bound without fresh calibration. |
| C. Horizon accumulation error | Error that can compound across simulated ticks. | Horizon and within-trace divergence/error profiles. | A monotone or universal horizon effect. |

## Observable implication

The structural hypothesis is that `epsilon` primarily measures A, while an
alternative recommendation requires information about A + B + C. It predicts
that alternative error can remain high when epsilon is low, especially where an
alternative departs from the mirror trajectory or a horizon exposes an omitted
transition effect.

The read-only decomposition found 45 descriptive low-mirror/high-alternative-
error observations and 609 high-mirror/low-alternative-error observations.
Low-mirror/high-alternative cases cluster in some H=2 blocked-EW,
heterogeneity-omitted action transitions, but do not identify a cause. The
online-observable SEM alternative-versus-mirror divergence had condition-specific
run-level associations with alternative error (rho -0.594 to 0.953; median
0.384 across 72 nonconstant rows). This is insufficient for a universal signal.

## Consequence

Treat A, B, and C as distinct sources of uncertainty in future study design.
Only A is implemented in the present gate. B and C motivate a small,
interpretable abstention study frozen in
`research/archive/cycle4/protocol_support/trust_signal_experiment_protocol.md`. None authorizes recommendation
or learning today.
