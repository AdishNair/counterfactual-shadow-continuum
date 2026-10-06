# Counterfactual validity review

**Status:** Skeptical evidence review, 2026-09-28. No new experiment was run.

## Question

What does same-action mirror error establish about CSC alternative-action
estimates, and what must be tested before those estimates support a decision
claim?

## Evidence and method

This review inspected `csc/world.py`, `csc/branches.py`, `csc/sync.py`,
`csc/compare.py`, `csc/runner.py`, and `experiments/validation.py`, with the
saved validation artifacts named below. It also checked the relevant CSC design
sections (2.5, 3.3, and 3.6). No external literature is cited; this makes no
novelty or literature claim.

For an accepted epoch, production and the mirror begin at the same immutable
anchor, use the same ordered event window, and receive the same action. The
comparison code checks anchor, window, role, action, provenance, trace length,
and synchronized input hash. It then records:

`epsilon = abs(U_hat_mirror(a0) - U_real(a0))`.

Invalid or incomplete windows are excluded. Utility is currently a scalar
negative weighted queue cost, with mean queue as the active term. Alternative
discounted regret is `max(0, U_hat(ai) - U_real(a0) - epsilon)`. This is a
conservative heuristic, not a confidence interval, error bound, or validated
decision rule.

The discrepancy is meaningful inside the authored software world because the
transitions differ: `ProductionWorld` has seeded per-tick service heterogeneity
and blocks EW service for `blocked_ew`; the default `ShadowWorldModel` is a
deterministic fluid model and models that block only when `model_incidents` is
enabled. It remains a discrepancy between two authored models, not a physical
traffic validation.

## Evidence

**Implemented and locally tested.** The system can produce a paired,
same-action production-versus-shadow utility gap for a complete local window,
and can reject a supplied window that does not match its planned input contract.
This establishes a local diagnostic of model mismatch under the production
action.

The two-mirror check had 8/8 identical traces and zero mismatches in
`results/validation/two-mirrors-fee3c6c01ae4/`. It demonstrates deterministic
repeatability of two copies of the same shadow computation for the same
request. It does not validate either copy against production or a junction.

| Local run, 8 epochs | Perturbation | Median epsilon | p95 epsilon | Bounded conclusion |
|---|---|---:|---:|---|
| `exact-control-a293497cb2ba` | Production heterogeneity disabled; matched service rate | 0 | 0 | The paired pipeline can agree when the intended transition difference is removed. |
| `biased-sem-ee57c67798a2` | Shadow service rate 4; production rate 2 | 6.167 | 8.183 | The mirror detects this authored service-rate bias in this short run. |
| `fidelity-h2-701b27266ea5` | Incident workload, H=2; shadow incident model disabled | 0.500 | 1.325 | Short-window local measurement. |
| `fidelity-h6-392d3bf96dc1` | Incident workload, H=6; shadow incident model disabled | 0.917 | 2.108 | Short-window local measurement. |
| `fidelity-h20-b3cf7b2117a5` | Incident workload, H=20; shadow incident model disabled | 1.000 | 15.445 | Tail error is material in this small run. |

The H=20 artifact contains individual epsilon values of 19.05 and 8.75 in
epochs with 20 and 6 blocked EW events. This is consistent with the known
incident omission. It is not an incident-effect estimate: the run has eight
epochs, one seed, and incident position is tied to time. The horizon runs also
have different total workloads, so they cannot identify a horizon-only effect.

The five-seed matrix gives preliminary routine-operation evidence: median
mirror epsilon is 0.75 for K=1 and K=2 (`RESULTS.md`). It cannot assess
alternative accuracy because production trajectories are intentionally held
invariant across K.

## What epsilon does not establish

1. **Alternative accuracy.** Mirror error is measured at `(state, a0, input
   window)`, with no demonstrated relation to error at `(state, ai, input
   window)`. Alternative actions can visit different phases, queue saturation,
   and incident regimes. No tested assumption makes same-action error an
   alternative-action error bound.

2. **A counterfactual causal effect.** An alternative is never realised in the
   authoritative world. Reusing production's event batch conditions the
   estimate on that batch; it does not observe the outcome caused by the other
   action. The seeded arrivals are exogenous by construction in this test
   world. A deployment must justify action-independence of every replicated
   input over the horizon; feedback through sensors, routing, demand, blocking,
   operators, or timing would invalidate it.

3. **Calibrated uncertainty.** Absolute utility error loses direction and can
   conceal offsetting trajectory errors. It uses only the first accepted mirror.
   `epsilon_ewma` after a missing mirror is a stale global average, not a
   state-, action-, horizon-, or regime-conditioned calibration.

4. **Long-horizon or physical validity.** Re-anchoring prevents error from
   carrying between epochs, but does not control within-window error; the H=20
   tail illustrates this. Exact control is a positive implementation control,
   because it removes a transition difference within the same authored world.
   Neither it nor the service-rate perturbation validates sensing, actuation,
   physical traffic, or an independent reference model.

5. **Closed-loop policy value.** One plan is pinned for the whole horizon.
   Alternative estimates assess fixed plans from an anchor, not a realised
   receding-horizon policy. Learning is disabled and has no outcome evidence.

## Methodological limitations

- Synchronization validates the supplied batch, rather than its source
  authenticity, live completeness, latency, or counterfactual invariance.
  Deduplication/reordering cannot restore a missing observation.
- Seeded hand-designed workloads support replay and paired comparison, but not
  independent sampling of environments or traffic regimes.
- Ranking accuracy, wrong-action rate, sign error, and coverage of alternative
  margins are not measured. A small same-action utility error can still produce
  a wrong alternative ranking.
- Each horizon artifact is one eight-epoch run. Epochs are not independent runs.
- Future input is supplied as a complete batch at branch launch. This is a
  controlled offline-window construction, not evidence that a live deployment
  obtains the needed future exogenous stream without coupling production.

## Concrete fidelity experiments

1. **Independent alternative ground truth.** Build a separately maintained
   reference environment that does not import `ShadowWorldModel`. For each
   anchor and action, run a fresh reference replica under common exogenous
   random numbers, then compare the shadow prediction to the realised
   alternative. Report signed/absolute utility error, trajectory error,
   ranking accuracy, and regret-sign accuracy by action.

2. **Mirror-to-alternative calibration.** On the same anchors, test whether
   mirror epsilon predicts or covers realised alternative error. Evaluate the
   `improvement > epsilon` gate on held-out data, stratified by action distance,
   queue level, phase age, demand, incident state, and horizon. Do not promote
   the gate unless its stated coverage is demonstrated.

3. **Replicated horizon sweep.** Use H={1,2,4,6,10,20,40}, multiple independent
   workload seeds, and comparable initial states. Report per-seed distributions
   and tail quantiles rather than pooled epochs. Predefine an operational error
   and coverage threshold before choosing a horizon.

4. **Mismatch factorial.** Independently vary service rate, heterogeneity,
   incident knowledge, observation noise/delay, capture staleness, and missing
   inputs. Measure alternative error and epsilon's detection rate. Include
   falsifying cases where mirror error is small but alternative error is large.

5. **Exogenous-input test.** Classify every input as action-independent or
   potentially action-dependent. In the reference environment, introduce known
   feedback such as action-dependent blocking and sensor delay; require model
   inclusion or abstention. Test outages, late events, and wrong window/epoch
   attribution without treating repair as evidence for missing observations.

6. **Decision-relevant metrics.** Evaluate trajectories, final queue,
   throughput, phase changes, and safety constraints alongside mean queue.
   Predefine unacceptable state error and wrong-action rate so scalar utility
   cannot conceal a safety-relevant mismatch.

## Assessment and next action

The supportable claim is narrow: CSC has an implemented, locally tested
same-action discrepancy diagnostic in a deterministic queue-world prototype,
and short ablations show it reacts to selected authored mismatch. Alternative
outcomes remain unvalidated estimates. The highest-value next experiment is an
independent-reference, all-actions evaluation, followed by a held-out test of
whether mirror error gives useful decision coverage. Until then, present epsilon
as a local diagnostic and discounted regret as a heuristic, not evidence that
an alternative would have improved production.
