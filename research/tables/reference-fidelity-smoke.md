# Local reference-fidelity smoke analysis

**STATUS:** MEASURED PRELIMINARY — two seeds per cell in the authored J1 software environment. The reference replays `ProductionWorld` and does not import `ShadowWorldModel`; it is not physical ground truth.

**Evidence:** `results/reference-fidelity/all-action-smoke-20260928`. Each underlying run was source-identity and artifact verified during analysis.

| Horizon | Shadow service rate | Runs | Median mirror absolute error | Median alternative absolute error | Median ranking agreement | Median epsilon coverage |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 2 | 2 | 0.5000 | 0.3750 | 0.9722 | 0.6111 |
| 2 | 4 | 2 | 3.0000 | 2.3750 | 0.9722 | 0.7222 |
| 6 | 2 | 2 | 0.7500 | 0.6250 | 0.8889 | 0.6944 |
| 6 | 4 | 2 | 6.9167 | 5.5625 | 0.8333 | 0.7222 |

## Findings

This is an implementation-level calibration check. It shows that mirror error and alternative error can differ, and that the current epsilon threshold does not uniformly cover selected-alternative error. It does not estimate physical traffic performance, establish a causal effect, or support a policy update.

## Limitations

The cells have only two seeds and 18 post-warm-up epochs per run. The reference shares the production software environment, so it is an independent oracle only relative to the SEM, not an external validation. Horizon, mismatch, and incident timing are not fully crossed or randomized. Use `research/evidence/cycle1/experiment_protocol.md` for the confirmatory design.
