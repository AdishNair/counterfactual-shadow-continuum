# Cycle 4 selector robustness diagnostics

**Status:** Predefined secondary diagnostics; no new rule or tuning.
**Question:** is apparent reliability explained by abstention, a few conditions, actions, or unstable seeds?
**Evidence/method:** `research/tables/cycle4-trust-calibration-v1` deterministic seed/run summaries; q=.50 family display fixed before outcomes; all candidate cell results retained.

| Rule | Factor | Level | Coverage | Precision | Abstention | Undefined precision runs |
|---|---|---|---:|---:|---:|---:|
| baseline | horizon | 2 | 0.3741 | 0.9949874686716792 | 0.6259 | 96 |
| baseline | horizon | 20 | 0.4944 | 0.9083438685208597 | 0.5056 | 88 |
| baseline | horizon | 6 | 0.4138 | 0.9871601208459214 | 0.5862 | 98 |
| baseline | demand | light | 0.4519 | 0.9898570769940065 | 0.5481 | 156 |
| baseline | demand | peak | 0.4029 | 0.9245087900723888 | 0.5971 | 126 |
| baseline | incident | blocked_ew | 0.4750 | 1.0 | 0.5250 | 240 |
| baseline | incident | none | 0.3798 | 0.9078442128359846 | 0.6202 | 42 |
| baseline | mismatch | aligned-control | 0.5781 | 1.0 | 0.4219 | 7 |
| baseline | mismatch | combined-rate-plus-incident | 0.2052 | 0.7918781725888325 | 0.7948 | 128 |
| baseline | mismatch | heterogeneity-only | 0.5703 | 0.9963470319634703 | 0.4297 | 12 |
| baseline | mismatch | incident-knowledge-only | 0.1823 | 1.0 | 0.8177 | 127 |
| baseline | mismatch | rate-only | 0.6010 | 0.92894280762565 | 0.3990 | 8 |
| divergence-q0.5 | horizon | 2 | 0.3741 | 0.9949874686716792 | 0.6259 | 96 |
| divergence-q0.5 | horizon | 20 | 0.0291 | 0.956989247311828 | 0.9709 | 336 |
| divergence-q0.5 | horizon | 6 | 0.1247 | 0.9573934837092731 | 0.8753 | 244 |
| divergence-q0.5 | demand | light | 0.2148 | 0.9873908826382153 | 0.7852 | 249 |
| divergence-q0.5 | demand | peak | 0.1371 | 0.9787234042553191 | 0.8629 | 427 |
| divergence-q0.5 | incident | blocked_ew | 0.1798 | 1.0 | 0.8202 | 409 |
| divergence-q0.5 | incident | none | 0.1721 | 0.9673123486682809 | 0.8279 | 267 |
| divergence-q0.5 | mismatch | aligned-control | 0.2391 | 1.0 | 0.7609 | 111 |
| divergence-q0.5 | mismatch | combined-rate-plus-incident | 0.0859 | 0.9212121212121213 | 0.9141 | 170 |
| divergence-q0.5 | mismatch | heterogeneity-only | 0.2375 | 0.9978070175438597 | 0.7625 | 114 |
| divergence-q0.5 | mismatch | incident-knowledge-only | 0.0865 | 1.0 | 0.9135 | 174 |
| divergence-q0.5 | mismatch | rate-only | 0.2307 | 0.9706546275395034 | 0.7693 | 107 |
| divergence-horizon-q0.5-h20 | horizon | 2 | 0.3741 | 0.9949874686716792 | 0.6259 | 96 |
| divergence-horizon-q0.5-h20 | horizon | 20 | 0.0291 | 0.956989247311828 | 0.9709 | 336 |
| divergence-horizon-q0.5-h20 | horizon | 6 | 0.1247 | 0.9573934837092731 | 0.8753 | 244 |
| divergence-horizon-q0.5-h20 | demand | light | 0.2148 | 0.9873908826382153 | 0.7852 | 249 |
| divergence-horizon-q0.5-h20 | demand | peak | 0.1371 | 0.9787234042553191 | 0.8629 | 427 |
| divergence-horizon-q0.5-h20 | incident | blocked_ew | 0.1798 | 1.0 | 0.8202 | 409 |
| divergence-horizon-q0.5-h20 | incident | none | 0.1721 | 0.9673123486682809 | 0.8279 | 267 |
| divergence-horizon-q0.5-h20 | mismatch | aligned-control | 0.2391 | 1.0 | 0.7609 | 111 |
| divergence-horizon-q0.5-h20 | mismatch | combined-rate-plus-incident | 0.0859 | 0.9212121212121213 | 0.9141 | 170 |
| divergence-horizon-q0.5-h20 | mismatch | heterogeneity-only | 0.2375 | 0.9978070175438597 | 0.7625 | 114 |
| divergence-horizon-q0.5-h20 | mismatch | incident-knowledge-only | 0.0865 | 1.0 | 0.9135 | 174 |
| divergence-horizon-q0.5-h20 | mismatch | rate-only | 0.2307 | 0.9706546275395034 | 0.7693 | 107 |

Accepted-action counts and oracle coverage/value-loss bounds are in `robustness.json`. Per-seed distributions and all-cell coverage floors are in the frozen calibration selection JSON. Figures are descriptive; no significance is inferred from pooled anchors.

Limitations: no calibrated probability or nominal epsilon error coverage exists. Precision near one can coexist with inadequate coverage. Cells with unsupported metadata abstain by design. Final heldout remains ungenerated if qualification fails. Next action: preserve frozen decision; no replacement selectors.
