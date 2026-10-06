# CSC statistical methodology

**Status:** Rules for current smoke evidence and a planned confirmatory analysis. No formal hypothesis-test conclusion is drawn from five seeds.

## Estimands and units

For timing, the estimand is the paired change in a run's post-warm-up median epoch duration when K changes. The independent unit is a seed/run, not an epoch, branch, or replayed trajectory. The current K comparison has five paired units. The within-run median limits worker-start outlier influence; the paired contrast limits workload-seed variation.

For calibration, summarize each run's mirror gap (`epsilon`) and complete-comparison fraction. For alternatives, retain raw/discounted regret and beaten rate as shadow-model estimates. They describe this authored simulator and do not estimate an unobserved factual alternative outcome. For safety and faults, report counts, exposure, and scenario-level production-digest equality without extrapolating zero observed events to untested attacks or infrastructure.

## Valid current analyses

The valid primary contrasts are K=1-K=0, K=2-K=0, and K=2-K=1 within seeds 1--5. Report five differences and their median in milliseconds plus condition medians. Avoid p-values, normal-theory intervals, and general scaling claims: n=5, condition order was not counterbalanced, and host/process startup behavior is a material confounder.

K=0 fidelity and regret are undefined, not zeros. A missing, faulted, duplicate, or non-comparable branch remains an exclusion; never impute utility, rank, or regret. Validation scenarios have one short run each. Their eight same-action mirror epochs are correlated measurements in one configuration, not eight independent fidelity replications.

## Proposed confirmatory analysis

Predeclare endpoints and comparison family. For each paired K contrast, publish all paired effects, median and mean differences, a nonparametric paired-bootstrap interval, and the empirical seed-effect distribution. With an adequately large seed set, use a paired permutation or sign-flip sensitivity test and predeclare multiple-comparison control across K contrasts and secondary endpoints.

Analyze horizon, mismatch, action distance, and backend factorially with independent workload seeds in every cell. Use a hierarchical model or seed-level summaries for repeated epochs, with seed as replication level. Publish raw per-run summaries, exclusions, timeout rate, hardware metadata, and a deterministic analysis script before interpreting a threshold decision.

## Evidence strength

Current timing/determinism observations are reproducible local smoke evidence with low external validity. Application-route audit evidence is moderate only for the exercised first-party gateway path and low for hostile containment. No statistic supports physical-traffic, real-time non-interference, general scaling, policy-improvement, or K3s-security claims.
