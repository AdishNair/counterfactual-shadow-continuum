# CSC limitation register

**Status:** First audit synthesis, 2026-09-28.

| ID | Limitation | Consequence | Evidence | Required response |
|---|---|---|---|---|
| L1 | Alternative-action validity is not established. | The 20-seed/cell factorial rejected the current gate globally: only 11/36 cell flags reproduced across disjoint evaluations. Discounted regret remains a calibrated model output, not a validated counterfactual or causal estimate. | `research/evidence/cycle1/reference_fidelity_analysis.md`, `research/evidence/cycle2/red_team_factorial_review.md`. | Separately maintained reference, matching closed-loop anchors, and a new held-out regime-detection study. |
| L2 | Result-series provenance is ambiguous. | Conflicting timing figures can be selected from same-named result roots. | `research/evidence/cycle1/results_analysis.md`, red-team M1. | Unique immutable series manifests and inventory. |
| L3 | Replay originally ignored recorded code identity. | Current code could be used to replay old evidence without detection. | Red-team M2. | Source-identity enforcement in replay; preserve source bundle. |
| L4 | Local K cost is cold process/barrier dominated. | It does not characterize asynchronous/deployed CSC. | `research/evidence/cycle1/results_analysis.md`, red-team M3. | Counterbalanced cold/warm/asynchronous study. |
| L5 | Local non-actuation assumes cooperative first-party code. | No hostile-code or OS/network containment claim is supported. | `README.md`, red-team M4. | Explicit threat model and policy-enforcing deployment test. |
| L6 | Input exogeneity/live availability are constructed assumptions. | A live control interpretation may fail under action-dependent observations. | Red-team O3. | Input provenance inventory and live availability/abstention study. |
| L7 | One domain, authored models, small action set. | No physical or generality claim follows. | `research/evidence/cycle1/generalization.md`. | Adapter compatibility and small second-domain experiment. |
| L8 | Learning is absent. | No usefulness or policy-improvement claim is possible. | `csc/contracts.py`, status RQ6. | Conservative learner only after fidelity/safety gates. |

Negative findings and failed preconditions are retained as research outcomes.
