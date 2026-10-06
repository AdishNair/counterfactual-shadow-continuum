# Cycle 3: uncertainty and counterfactual-reliability literature

**Status:** Source-verified, bounded literature search, 2026-09-28. This is a
research-design note, not an implementation, experimental result, or evidence
that CSC recommendations are valid.

## Question

Which established methods bear directly on CSC's observed failure: a
same-action mirror residual (`epsilon`) did not provide a uniform bound on an
alternative action's estimated-gain error across the frozen factorial,
especially under authored mismatch? Can they support a small, interpretable
signal for a future *abstain/recommend* protocol?

## Scope and method

This is Cycle 3 only. It does not repeat the repository's broad novelty screen
in [../cycle1/literature_review.md](../cycle1/literature_review.md). On 2026-09-28, the search was
limited to primary proceedings, publisher DOI pages, and an official accepted
conference page for: compounding rollout error, uncertainty-aware MPC,
probabilistic ensembles, alternative-distribution shift, off-policy evaluation,
trust regions, sim-to-real discrepancy, and selective prediction. Searches
were title/author checked against the linked primary source. One relevant
preprint-only item is not used as evidence below.

The repository evidence motivating the search is deliberately narrow:
[../cycle1/reference_fidelity_analysis.md](../cycle1/reference_fidelity_analysis.md) and
[../cycle2/red_team_factorial_review.md](../cycle2/red_team_factorial_review.md) show that the
fixed epsilon gate failed its all-cell criterion in the authored J1 evaluation
(15/36 initial and 13/36 disjoint held-out cells passed). The reference is
independent of `ShadowWorldModel`, but remains an authored-software reference,
not a realised alternative outcome or physical ground truth. Learning stays
blocked under [../../RESEARCH_STATUS.md](../../RESEARCH_STATUS.md).

## Verified sources and CSC classification

| Technique and primary source | What the source establishes | CSC classification | Limitation for the observed failure |
|---|---|---|---|
| Short model rollouts from real states - Janner et al., [*When to Trust Your Model: Model-Based Policy Optimization* (NeurIPS 2019)](https://proceedings.neurips.cc/paper/2019/hash/5faf461eff3099671ad63c6f3f094f7f-Abstract.html) | Model-generated data trades off utility against model bias; the paper uses short branched rollouts from real data to avoid long-horizon failure modes. | **Directly applicable** as a design constraint for CSC's finite-horizon branch evaluation. | It is a policy-optimisation result, not a guarantee that a mirror residual bounds an alternative branch. Receding/short rollout reduces exposure to error; it does not establish an acceptable horizon. CSC must select horizon on a held-out, per-regime fidelity study. |
| Probabilistic ensemble dynamics and trajectory sampling (PETS) - Chua et al., [*Deep Reinforcement Learning in a Handful of Trials using Probabilistic Dynamics Models* (NeurIPS 2018)](https://proceedings.neurips.cc/paper/2018/hash/3de568f8597b94bda53149c7d7f5958c-Abstract.html) | An ensemble of probabilistic dynamics models and sampled trajectories can represent predictive uncertainty while choosing finite-horizon actions. | **Adaptable.** Ensemble disagreement could be an additional alternative-specific uncertainty feature. | Ensemble spread is a model diagnostic, not automatically calibrated error; shared misspecification can make all members agree. Its neural continuous-control construction also does not match the current small hand-authored SEM. |
| High-probability uncertainty-aware MPC - Koller et al., [*Learning-based Model Predictive Control for Safe Exploration* (CDC 2018)](https://doi.org/10.1109/CDC.2018.8619572) | With a statistical dynamics model, stated regularity assumptions, reliable trajectory confidence intervals, and a terminal safe set, MPC can preserve prescribed safety constraints with high probability. | **Conceptually related.** It clarifies the ingredients required before calling a bound a safety/trust certificate. | CSC has no validated statistical transition bound, disturbance set, terminal safe set, or physical constraint claim. This does not certify recommendation correctness or authorise actuation. |
| Pessimistic model-based evaluation under shift - Yu et al., [*MOPO: Model-based Offline Policy Optimization* (NeurIPS 2020)](https://proceedings.neurips.cc/paper/2020/hash/a322852ce0df73e204b7e67cbbef0d0a-Abstract.html) | Distributional shift between data and a learned policy can make ordinary model-based optimisation exploit model error; the method penalises model uncertainty to optimise a lower-bound construction under its assumptions. | **Adaptable.** A predeclared conservative penalty can be used as a recommendation-abstention feature, rather than treating predicted gain as sufficient. | MOPO's practical penalty uses an ensemble model and its theory needs a suitable uncertainty/error relation. Current CSC has evidence that epsilon alone lacks that relation, so a penalty cannot be presented as a bound without fresh calibration. |
| Doubly robust off-policy value evaluation - Jiang and Li, [*Doubly Robust Off-policy Value Evaluation for Reinforcement Learning* (ICML 2016)](https://proceedings.mlr.press/v48/jiang16.html) | Combining a model with importance-weighted logged trajectories can reduce variance while retaining unbiasedness under the estimator's logged-policy and support conditions. | **Unsuitable** for current per-anchor CSC validity; **adaptable** only if a future logged-data study supplies known behaviour propensities and adequate action support. | A deterministic production action plus simulated alternatives is not logged exploration of those alternatives. No importance weights or overlap exist for the unexecuted action, so this cannot repair the mirror gate retrospectively. |
| Horizon limits in OPE - Liu, Bacon, and Brunskill, [*Understanding the Curse of Horizon in Off-Policy Evaluation via Conditional Importance Sampling* (ICML 2020)](https://proceedings.mlr.press/v119/liu20a.html) | Even unbiased importance-sampling OPE can have high variance at long horizons; the paper analyses that dependence. | **Conceptually related.** It reinforces reporting horizon explicitly and resisting long-horizon reliability claims. | It studies statistical OPE variance, whereas CSC's present issue is model bias at unexecuted actions. It does not supply an error signal for a single captured state. |
| Trust-region policy updates - Schulman et al., [*Trust Region Policy Optimization* (ICML 2015)](https://proceedings.mlr.press/v37/schulman15.html) | Restricting successive policy changes supports a monotonic-improvement analysis for policy optimisation. | **Conceptually related.** A future learner could restrict updates away from the evaluated/behaviour policy. | A policy-distance constraint neither measures transition-model error nor validates an individual alternative recommendation. It must not be relabelled as a CSC shadow-trust region. Current learning remains blocked. |
| Dynamics randomisation for simulator discrepancy - Peng et al., [*Sim-to-Real Transfer of Robotic Control with Dynamics Randomization* (ICRA 2018)](https://doi.org/10.1109/ICRA.2018.8460528) | Simulated policies can be trained across varied dynamics to reduce a demonstrated simulation-to-hardware discrepancy. | **Adaptable** as a future stress-test design: define mismatch families before evaluation and test the rule across them. | Domain randomisation promotes robustness in the studied robot task; it does not create factual counterfactuals, quantify CSC's local error, or cover unknown mismatch mechanisms. |
| Conformal risk control - Angelopoulos et al., [*Conformal Risk Control* (ICLR 2024)](https://proceedings.iclr.cc/paper_files/paper/2024/hash/f3549ef9b5ff520a7e41ff3cc306ab2b-Abstract-Conference.html) | A calibration procedure can choose a threshold controlling a user-defined bounded risk under its exchangeability assumptions, with a finite-sample correction. | **Adaptable.** A threshold on a small trust score could target selective false-recommendation risk on a frozen calibration set. | The guarantee is distributional, not per-anchor or per-regime, and does not survive arbitrary deployment shift. The factorial's condition dependence means calibration/evaluation must be grouped by declared regimes and include out-of-domain abstention; a pooled threshold is insufficient. |
| Selective prediction / reject option - Geifman and El-Yaniv, [*SelectiveNet: A Deep Neural Network with an Integrated Reject Option* (ICML 2019)](https://proceedings.mlr.press/v97/geifman19a.html) | Selective prediction makes a risk--coverage trade-off explicit: a system can decline low-confidence cases rather than optimise accuracy alone. | **Directly applicable** as the operational framing: CSC may abstain from a recommendation while still recording an estimate. | The paper does not make an arbitrary confidence score calibrated under shift. CSC must report coverage, recommendation count, selective precision/false-positive rate, and abstention by held-out regime; abstention itself is not validity. |

## Findings for CSC

1. **The present failure is expected under rollout bias and alternative shift.**
   A same-action agreement assesses a narrow local transition. An alternative
   action may visit a different part of the transition/incident response, so its
   error can differ even when the mirror error is small. Janner et al. and MOPO
   motivate conservative finite-horizon model use; they do not supply evidence
   that CSC's `epsilon` is an alternative-error bound. The observed
   non-uniform mirror-to-alternative association is consistent with this
   distinction, but does not identify its mechanism.

2. **No cited method justifies converting CSC estimates into counterfactual
   facts.** OPE requires observed trajectories, a specified behaviour policy,
   and overlap. CSC's unexecuted branches have none of those observations.
   Robust/uncertainty-aware MPC requires validated uncertainty sets and explicit
   constraints. Simulation-to-real methods require an independently tested
   target environment. None is present in the current J1 SEM-versus-authored
   reference comparison.

3. **Abstention is a testable decision rule, not an after-the-fact label.** A
   future protocol may use a conservative selector, but only after freezing its
   features, loss, calibration data, and evaluation split. It must retain the
   global negative result if any declared use regime fails. Conformal risk
   control could calibrate a *population* selective-risk threshold only where
   exchangeability is credible; it cannot erase the adverse mismatch regimes.

## Small, interpretable trust-signal implication

The literature supports testing a compact selector rather than widening the
current epsilon threshold. A candidate **proposed** (not implemented) feature
vector is:

| Signal | Meaning | Required evidence before use |
|---|---|---|
| Mirror absolute utility error | Local same-action residual already recorded by CSC. | Assess monotonic association and coverage separately by horizon and declared mismatch regime. It has already failed as a universal one-feature rule. |
| Horizon | Direct control on compounded rollout exposure. | Predeclare a maximum accepted horizon or allow only a monotone conservative penalty; evaluate the boundary on disjoint seeds/anchors. |
| Alternative-specific disagreement | Spread across independently trained/parameterised SEM members, if such members are built. | Verify that spread predicts *alternative* reference error, including shared-misspecification stress cases. |
| Action-margin / rank stability | Difference between best and next-best predicted utilities, optionally across ensemble members. | Define ties and loss before looking at evaluation data; a large predicted margin is not evidence unless it predicts correct ranking. |
| Regime/OOD indicator | A transparent label/distance based on input demand, incident attributes, and known SEM assumptions. | Freeze a detector, evaluate its misclassification and out-of-domain abstention, and use anchors generated by matching authoritative regimes. |

Use a one-sided, understandable policy: recommend only when all predeclared
checks pass; otherwise label the alternative estimate as **abstained / not
validated for recommendation**. Avoid opaque score aggregation or tuning many
thresholds on the same 20-seed cells. A compact monotone rule is easier to
audit, but it still needs a new independent reference and held-out evaluation.
Signals must not alter the non-actuating boundary or enable learning.

## Limitations

- This is a selective methods search, not a systematic review, meta-analysis,
  or claim about the best method for J1.
- The cited control and learning guarantees are conditional on their respective
  model, uncertainty, support, stationarity, and constraint assumptions. Those
  assumptions have not been shown for CSC.
- The current reference shares the authored production-model family and fixed
  anchors with the test setup. It cannot establish physical validity,
  closed-loop alternative outcomes, or external distribution-shift coverage.
- An ensemble, OOD score, or conformal threshold would be new functionality and
  requires a predeclared protocol before implementation or policy use.

## Open questions and next actions

1. Specify one bounded decision loss: for example, an incorrect positive
   alternative recommendation relative to a separately maintained reference.
   Define whether a wrong ranking, a sign error, or a gain-error tolerance is
   the endpoint.
2. Build a new validity protocol around matching closed-loop anchor generation,
   a separately maintained transition-and-metric reference, declared
   rate-only/incident-only/combined mismatch strata, and an explicit OOD row.
3. Compare only predeclared compact selectors: epsilon alone; horizon plus
   epsilon; and, if an independent ensemble is added, the same rule plus
   alternative disagreement. Use a calibration block and a truly held-out
   block; report selective risk, coverage, recommendation count, and each cell.
4. Keep `learning_enabled` rejected. Consider a trust-region or OPE study only
   after a separate logged-action/support design and a successful validity gate;
   neither is a replacement for this calibration problem.
