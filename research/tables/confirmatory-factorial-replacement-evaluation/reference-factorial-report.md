# Confirmatory reference-fidelity factorial

**Status:** Deterministic run/seed-level analysis.

**Series:** `results/reference-fidelity/confirmatory-replacement-evaluation-20260928`
**Gate multiplier:** 1.0
**Provisional classification:** B. CONDITIONAL SUPPORT

The independent unit is the seed x cell run. Three anchors are repeated observations reduced within run; bootstrap intervals resample runs.

| H | Demand | Incident | Mismatch | Runs | Median precision | Median FP rate | Median abstention | Median selected coverage | Gate criterion |
|---:|---|---|---|---:|---:|---:|---:|---:|---|
| 2 | light | blocked_ew | aligned-control | 20 | 1.0000 | 0.0000 | 0.3333 | 1.0000 | pass |
| 2 | light | blocked_ew | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 0.3333 | 0.8333 | pass |
| 2 | light | blocked_ew | rate-and-incident-omitted | 20 | 0.5000 | 1.0000 | 0.5000 | 0.6667 | fail |
| 2 | light | none | aligned-control | 20 | 1.0000 | 0.0000 | 0.6667 | 1.0000 | pass |
| 2 | light | none | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 0.6667 | 1.0000 | pass |
| 2 | light | none | rate-and-incident-omitted | 20 | 1.0000 | 0.0000 | 0.6667 | 1.0000 | pass |
| 2 | peak | blocked_ew | aligned-control | 20 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | fail |
| 2 | peak | blocked_ew | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | fail |
| 2 | peak | blocked_ew | rate-and-incident-omitted | 20 | 0.0000 | 0.3333 | 0.6667 | 0.6667 | fail |
| 2 | peak | none | aligned-control | 20 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | fail |
| 2 | peak | none | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | fail |
| 2 | peak | none | rate-and-incident-omitted | 20 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | fail |
| 6 | light | blocked_ew | aligned-control | 20 | 1.0000 | 0.0000 | 0.3333 | 1.0000 | pass |
| 6 | light | blocked_ew | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 0.3333 | 0.6667 | pass |
| 6 | light | blocked_ew | rate-and-incident-omitted | 20 | 1.0000 | 0.0000 | 0.6667 | 0.6667 | pass |
| 6 | light | none | aligned-control | 20 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | fail |
| 6 | light | none | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 1.0000 | 0.6667 | fail |
| 6 | light | none | rate-and-incident-omitted | 20 | 1.0000 | 0.0000 | 1.0000 | 0.6667 | fail |
| 6 | peak | blocked_ew | aligned-control | 20 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | fail |
| 6 | peak | blocked_ew | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 1.0000 | 0.5000 | fail |
| 6 | peak | blocked_ew | rate-and-incident-omitted | 20 | 0.2500 | 0.0000 | 0.8333 | 0.1667 | fail |
| 6 | peak | none | aligned-control | 20 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | fail |
| 6 | peak | none | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 1.0000 | 0.6667 | fail |
| 6 | peak | none | rate-and-incident-omitted | 20 | 0.0000 | 0.0000 | 1.0000 | 0.6667 | fail |
| 20 | light | blocked_ew | aligned-control | 20 | 1.0000 | 0.0000 | 0.3333 | 1.0000 | pass |
| 20 | light | blocked_ew | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 0.3333 | 0.6667 | pass |
| 20 | light | blocked_ew | rate-and-incident-omitted | 20 | 0.5000 | 1.0000 | 0.3333 | 0.6667 | fail |
| 20 | light | none | aligned-control | 20 | 1.0000 | 0.0000 | 0.3333 | 1.0000 | pass |
| 20 | light | none | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 0.3333 | 0.3333 | pass |
| 20 | light | none | rate-and-incident-omitted | 20 | 1.0000 | 0.0000 | 0.3333 | 0.0000 | pass |
| 20 | peak | blocked_ew | aligned-control | 20 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | fail |
| 20 | peak | blocked_ew | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 1.0000 | 0.6667 | fail |
| 20 | peak | blocked_ew | rate-and-incident-omitted | 20 | 0.0000 | 0.6667 | 0.3333 | 0.0000 | fail |
| 20 | peak | none | aligned-control | 20 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | fail |
| 20 | peak | none | heterogeneity-omitted | 20 | 1.0000 | 0.0000 | 1.0000 | 0.3333 | fail |
| 20 | peak | none | rate-and-incident-omitted | 20 | 0.0000 | 0.6667 | 0.3333 | 0.3333 | fail |

The reference is independent relative to `ShadowWorldModel` only. It is an authored production-software reference, not physical or factual ground truth. Do not treat the provisional classification as permission to implement learning.
