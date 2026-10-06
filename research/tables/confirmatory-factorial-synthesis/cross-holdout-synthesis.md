# Cross-holdout factorial synthesis

**Status:** Deterministic seed-level synthesis of two disjoint evaluation blocks.

Reproduced support appears in 11 of 36 predeclared cells.

| H | Demand | Incident | Mismatch | Evaluation | Held-out | Reproduced support |
|---:|---|---|---|---|---|---|
| 2 | light | blocked_ew | aligned-control | pass | pass | yes |
| 2 | light | blocked_ew | heterogeneity-omitted | pass | pass | yes |
| 2 | light | blocked_ew | rate-and-incident-omitted | fail | fail | no |
| 2 | light | none | aligned-control | pass | pass | yes |
| 2 | light | none | heterogeneity-omitted | pass | pass | yes |
| 2 | light | none | rate-and-incident-omitted | fail | pass | no |
| 2 | peak | blocked_ew | aligned-control | fail | fail | no |
| 2 | peak | blocked_ew | heterogeneity-omitted | fail | fail | no |
| 2 | peak | blocked_ew | rate-and-incident-omitted | fail | fail | no |
| 2 | peak | none | aligned-control | fail | fail | no |
| 2 | peak | none | heterogeneity-omitted | fail | fail | no |
| 2 | peak | none | rate-and-incident-omitted | fail | fail | no |
| 6 | light | blocked_ew | aligned-control | pass | pass | yes |
| 6 | light | blocked_ew | heterogeneity-omitted | pass | pass | yes |
| 6 | light | blocked_ew | rate-and-incident-omitted | fail | pass | no |
| 6 | light | none | aligned-control | pass | fail | no |
| 6 | light | none | heterogeneity-omitted | pass | fail | no |
| 6 | light | none | rate-and-incident-omitted | pass | fail | no |
| 6 | peak | blocked_ew | aligned-control | fail | fail | no |
| 6 | peak | blocked_ew | heterogeneity-omitted | fail | fail | no |
| 6 | peak | blocked_ew | rate-and-incident-omitted | fail | fail | no |
| 6 | peak | none | aligned-control | fail | fail | no |
| 6 | peak | none | heterogeneity-omitted | fail | fail | no |
| 6 | peak | none | rate-and-incident-omitted | fail | fail | no |
| 20 | light | blocked_ew | aligned-control | pass | pass | yes |
| 20 | light | blocked_ew | heterogeneity-omitted | pass | pass | yes |
| 20 | light | blocked_ew | rate-and-incident-omitted | fail | fail | no |
| 20 | light | none | aligned-control | pass | pass | yes |
| 20 | light | none | heterogeneity-omitted | pass | pass | yes |
| 20 | light | none | rate-and-incident-omitted | pass | pass | yes |
| 20 | peak | blocked_ew | aligned-control | fail | fail | no |
| 20 | peak | blocked_ew | heterogeneity-omitted | fail | fail | no |
| 20 | peak | blocked_ew | rate-and-incident-omitted | fail | fail | no |
| 20 | peak | none | aligned-control | pass | fail | no |
| 20 | peak | none | heterogeneity-omitted | fail | fail | no |
| 20 | peak | none | rate-and-incident-omitted | fail | fail | no |

Correlation rows use one seed x cell run as each observation. They are descriptive associations in the authored software environment; the bootstrap intervals resample runs and do not turn anchors into independent units.
