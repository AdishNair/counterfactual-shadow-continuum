# CSC research questions

**Status:** Audit baseline, 2026-09-28. This is a research plan and evidence map, not a claim that every question has been answered.

## Scope

CSC is evaluated here only in the software Junction J1 environment. Production is authoritative; mirrors and alternative shadows are non-actuating estimates. `K` is the number of alternative actions and excludes mirrors. Read [../../RESEARCH_CONTEXT.md](../../RESEARCH_CONTEXT.md) and [../../RESEARCH_STATUS.md](../../RESEARCH_STATUS.md) for the shared current state.

## Questions

| ID | Question | Current evidence | Status |
|---|---|---|---|
| RQ1 | Does the implemented application path keep shadows non-actuating? | Gateway/world audit and tests; indexed matrix records zero unexpected authoritative commands. | Locally supported at the application boundary; not containment-validated. |
| RQ2 | What run-level overhead is associated with K=0, 1, and 2? | Five paired workload seeds in `results/matrix/matrix-summary.json`. | Preliminary local smoke measurement. |
| RQ3 | How does overhead change from one to two alternative actions? | Same five paired seeds. | Preliminary local smoke measurement. |
| RQ4 | Does a same-action mirror reproduce production in the authored model? | Matrix epsilon and 0/8 two-mirror trace disagreements in `results/validation/validation-summary.json`. | Partially measured; not external-model fidelity. |
| RQ5 | Do horizon and deliberate model mismatch affect calibration? | One short run each at horizons 2, 6, and 20; exact and biased controls. | Exploratory only. |
| RQ6 | Can recorded counterfactual evidence improve production policy? | No learner exists; `learning_enabled` is rejected. | Unanswered. |
| RQ7 | Do local shadow faults alter the production logical trajectory? | One short paired fault run per scenario retained the baseline production digest. | Local logical-harness evidence only. |
| RQ8 | What fidelity/information benefit justifies increasing K? | K=1/K=2 differ in alternative set; no predeclared information metric exists. | Open. |
| RQ9 | Is CSC portable beyond this traffic model? | No second adapter or domain experiment. | Unanswered. |

## Decision rules

Evidence for RQ2--RQ5 is summarized at the independent run/seed level. Epochs within a run are repeated measurements, not independent replicates. A shadow outcome cannot establish the real outcome of an unexecuted production action. For RQ1 and RQ7, a zero count in this controlled workload is evidence only of the checked application path; it does not establish OS, network, container, or K3s isolation.

## Next actions

Reconcile stale high-level latency figures with the primary matrix index. Then run a predeclared, randomized-order, multi-seed protocol with resource measurements and a separate deployment-validation phase. RQ6 needs a conservative learner and evaluation protocol before implementation.
