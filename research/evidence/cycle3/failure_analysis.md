# Counterfactual failure analysis

**Status:** Exploratory, read-only derived analysis of completed immutable factorial series.

## Question

Why does same-action mirror error fail as a uniform conservative estimate of alternative-action error?

## Method

The frozen Cycle 3 protocol (`research/evidence/cycle3/cycle3_analysis_protocol.md`) keeps seed x cell as the independent unit. This script verifies each source series, then deterministically reconstructs SEM and authored-reference traces from saved anchors and windows. It does not collect new observations. Low/high labels use within-series quartiles solely as descriptive taxonomy labels, never operational thresholds.

## Descriptive findings

Derived alternative-action observations: 12960. Low-mirror/high-alternative-error cases: 45. High-mirror/low-alternative-error cases: 609.

Failure counts and factor strata are in `research/tables/failure_taxonomy.csv`; run-level association rows are in `research/tables/failure_relationships.csv`; the analysis-only oracle bounds are in `research/tables/oracle_bounds.csv`.

### Low-mirror/high-alternative-error clusters

| Series | H | Demand | Incident | Mismatch | Production | Alternative | Observations |
|---|---:|---|---|---|---|---|---:|
| heldout | 2 | light | blocked_ew | heterogeneity-omitted | EW_GREEN | BALANCED | 10 |
| calibration | 2 | light | blocked_ew | heterogeneity-omitted | EW_GREEN | BALANCED | 4 |
| calibration | 2 | peak | blocked_ew | heterogeneity-omitted | EW_GREEN | BALANCED | 4 |
| heldout | 2 | peak | blocked_ew | heterogeneity-omitted | EW_GREEN | BALANCED | 3 |
| calibration | 2 | light | blocked_ew | heterogeneity-omitted | EW_GREEN | NS_GREEN | 2 |
| calibration | 2 | peak | blocked_ew | heterogeneity-omitted | EW_GREEN | NS_GREEN | 2 |
| calibration | 6 | peak | blocked_ew | heterogeneity-omitted | EW_GREEN | BALANCED | 2 |
| evaluation | 2 | light | blocked_ew | heterogeneity-omitted | EW_GREEN | BALANCED | 2 |
| heldout | 2 | light | blocked_ew | heterogeneity-omitted | EW_GREEN | NS_GREEN | 2 |
| calibration | 2 | light | blocked_ew | rate-and-incident-omitted | NS_GREEN | BALANCED | 1 |
| calibration | 2 | light | blocked_ew | rate-and-incident-omitted | NS_GREEN | EW_GREEN | 1 |
| calibration | 6 | light | blocked_ew | heterogeneity-omitted | EW_GREEN | BALANCED | 1 |

### Analysis-only oracle bound

| Series | Better alternative exists | CSC gate pass | Selected reference-positive | False positive recommendation |
|---|---:|---:|---:|---:|
| calibration | 0.2713 | 0.3083 | 0.2694 | 0.0782 |
| evaluation | 0.2833 | 0.3069 | 0.2819 | 0.0731 |
| heldout | 0.3028 | 0.3301 | 0.3019 | 0.0713 |

The structural hypothesis is supported only as a descriptive candidate when alternative trajectory divergence co-occurs with alternative error in a stratum. It is not a causal conclusion: horizon, mismatch, action, and constructed anchor state can jointly influence divergence and error. Mirror error captures same-action error (A); alternative trajectory divergence is a candidate marker of extrapolation error (B); horizon can compound both (C). This is an uncertainty taxonomy/hypothesis, not a proven additive decomposition.

## Next implication

No derived signal is enabled in CSC. Any trust selector must be frozen and tested using new development, calibration, and final held-out seeds against a separately maintained reference. Oracle columns are analysis-only and must never enter online CSC decisions.

## Descriptive thresholds

{
  "calibration": {
    "low_mirror": 0.0,
    "high_mirror": 1.649999999999999,
    "low_alternative": 0.0,
    "high_alternative": 1.0
  },
  "evaluation": {
    "low_mirror": 0.0,
    "high_mirror": 1.6666666666666679,
    "low_alternative": 0.0,
    "high_alternative": 0.9166666666666662
  },
  "heldout": {
    "low_mirror": 0.0,
    "high_mirror": 1.75,
    "low_alternative": 0.0,
    "high_alternative": 1.0
  }
}
