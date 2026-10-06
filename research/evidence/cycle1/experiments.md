# Prioritized CSC experiment program

**Status:** Proposed after the first audit and independent red-team review.
Nothing in this file is a completed experiment unless it links to a result path.

| Priority | Experiment | Research question | Why it is needed | Required change | Expected artifact | Decision enabled |
|---:|---|---|---|---|---|---|
| 1 | Immutable-series migration and source-identity replay | Evidence integrity | Current aggregate roots can be replaced and old/high-level timing reports conflict. | Implemented in `experiments/runner.py` and `experiments/replay.py`; inventory legacy runs. | New unique series manifest; source-verified replay; `research/tables/result_series_inventory.csv`. | Whether an experiment may be cited reproducibly. |
| 2 | Independent-reference all-actions fidelity | RQ4/RQ5, C1 | A mirror at production action does not validate alternative-action estimates. | Executed: frozen, all-actions authored-reference factorial with disjoint calibration/evaluation blocks. | Per-action error, rank agreement, regret-sign and epsilon-gate coverage by seed/horizon/regime. | **Global gate rejected for policy use; preserve conditional observations.** |
| 3 | Replicated horizon/mismatch factorial | RQ5 | Current H=2/6/20 checks are one seeded run and incident timing is confounded. | Executed with 20 seeds/cell and randomized order, using matched anchor/input prefixes. | Per-seed distributions and tail-error/ranking tables. | Follow-up needs separated mismatch mechanisms and a regime classifier, not a selected horizon. |
| 4 | Counterbalanced K cost study | RQ2/RQ3/RQ8 | Existing timing is cold spawned-worker barrier cost on one host. | New immutable series; randomized K order; host and child CPU/RSS; cold/warm/asynchronous modes. | Paired K effects and resource/latency plots with run-level uncertainty. | Whether K=1 or K=2 fits a declared runtime budget. |
| 5 | Threat-model and containment deployment test | RQ1 | Local gateway checks do not contain hostile code. | Available K3s/NetworkPolicy/gVisor runtime and independently collected actuator logs. | A1--A14 outcome table, manifests, policy test evidence, environment audit. | Whether any hostile-shadow containment claim is justified. |
| 6 | Asynchronous production failure study | RQ7 | Current coordinator waits for shadows, so it cannot establish continuity. | Separate production clock and comparison path; fault roles/stages individually. | Production cadence and state continuity under branch/network/resource faults. | Whether principle “production is not blocked by speculation” holds. |
| 7 | Adapter refactor and second minimal domain | RQ9 | Current source is traffic-coupled. | Implement/test `TrafficAdapter` against golden existing semantics, then a small independent adapter. | Compatibility traces and a domain-change log. | Whether the core is technically reusable beyond J1. |
| 8 | Conservative learner comparison | RQ6 | No learning evidence exists. | Only after 2--6; implement an independently disableable conservative learner and promotion gate. | Baseline vs observation-only vs learning paired series, realised held-out utility, rollback records. | Whether CSC evidence improves a policy safely. |

## Planned protocol rules

The independent unit is a seed/run. Use fresh immutable series directories,
fixed configuration and source identities, randomized/counterbalanced condition
order, predeclared exclusions, and raw artifact/replay verification. Do not pool
epochs as independent observations. Treat zero observed actuation escapes as a
count at a stated exposure, never as a general safety guarantee.

## Current decision

Do not implement a learner or claim counterfactual decision benefit. Priority 1
is implemented and priority 2 has only smoke evidence; execute its confirmatory
replicated design next. Priority 5 depends on unavailable
infrastructure and cannot be replaced by a successful local simulation.
