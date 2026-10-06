# CSC related-work review

**Status:** Source-verified screening, 2026-09-28. This is a literature map, not evidence that CSC is novel or effective.

## Question

What previously published work bears on CSC's claimed combination of live input duplication, a captured decision boundary, simulated alternative actions, non-actuating execution, and comparison with the production outcome?

## Method

The review screened primary publisher/proceedings pages, DOI landing pages, or authoritative proceedings repositories. It retains only sources whose title, authors, venue/status, and persistent URL were checked. Search clusters were digital twins/what-if simulation, shadow traffic/production testing, and counterfactual or off-policy evaluation. The resulting map is deliberately selective; it is not a systematic review and makes no completeness claim.

## Findings

### Digital-twin and what-if simulation

Digital twins already cover virtual representations updated from operational systems and used for decision support. Grieves and Vickers formulate the broad digital-twin rationale [@grieves2017]. Kritzinger et al. distinguish a digital model, digital shadow, and digital twin by the direction/integration of data exchange [@kritzinger2018]. That taxonomy means CSC should not claim the word "shadow" or operational model synchronization as new.

The distinction that matters for this repository is narrower: the CSC alternative world is an explicitly *non-authoritative estimate*, shares an application-level decision anchor and exogenous window with production, and is calibrated by a same-action mirror. The screened digital-twin work does not, on its own, establish that this exact combination is absent elsewhere.

### Production shadow traffic and sandboxed alternatives

CSC also overlaps with production shadow testing. Durieux, Hamadi, and Monperrus propose live regression testing of generated patches on copied production traffic in a sandboxed application [@durieux2017]. It is direct precedent for copying live inputs into a non-authoritative execution. Its goal is patch validation after a failure, rather than per-decision evaluation of alternative control actions; nevertheless, it defeats any broad claim that "sandboxed shadow traffic" is a CSC innovation.

The repository's implementation evidence only supports an application-level actuator gateway and local process/localhost behavior. Kubernetes NetworkPolicy documentation [@kubernetesNetworkPolicy] is useful engineering guidance for a deployment test, but is not experimental evidence that CSC shadows are contained. It must remain labelled documentation, not literature validation.

### Counterfactual and off-policy evaluation

Counterfactual policy evaluation is an established statistical field. Rubin sets out the potential-outcomes framing [@rubin1974]; Pearl provides a formal structural-causal account [@pearl2009]. In logged contextual bandits, Li et al. give replay-based offline evaluation under their logging conditions [@li2011]. Jiang and Li propose doubly robust off-policy value evaluation [@jiang2016], while Thomas and Brunskill study data-efficient off-policy value evaluation [@thomas2016].

These methods are not interchangeable with CSC. CSC evaluates a model evolved from a shared anchor, whereas logged-bandit/OPE methods estimate policy values from observed logged rewards under stated identification and coverage conditions. Conversely, a shadow-model value is not a physical counterfactual merely because inputs are duplicated. Model error, unmodelled post-action dynamics, and feedback create bias risks not removed by the local mirror epsilon. CSC's current discounted-regret number therefore should be called a calibrated *model estimate*, never an unbiased causal/OPE estimate, unless an appropriate identification and validation protocol is established.

## Implications for CSC claims

| Claim | Screening assessment | Evidence needed before making it |
|---|---|---|
| Live alternatives from production state are novel | Unsupported; digital twins, shadow traffic, and simulation-based decision support are established. | A systematic, date-bounded novelty review across systems, digital-twin, and control venues. |
| Sandbox plus copied traffic is novel | Contradicted as a broad claim by production-driven patch generation. | Narrow the claim to a documented, unanticipated technical mechanism and compare it directly. |
| CSC supplies counterfactual outcomes | Unsupported. Current shadows are model estimates. | Domain model validation over action/horizon strata and an explicit causal estimand/assumptions. |
| Same-action mirror is useful for calibration | Plausible but unproven in the screened sources and this repository. | Pre-registered longer fidelity study showing that epsilon predicts alternative-action error. |
| A production-authoritative, non-actuating branch contract is a useful systems pattern | A potentially differentiating design hypothesis, not a demonstrated contribution. | Threat model, policy-enforced deployment tests, and comparison to related shadow-testing architectures. |

## Limitations and open questions

This search did not exhaust proprietary engineering practice, grey literature, or every systems venue. It found no verified source in this limited screen that uses CSC's exact terms or proves that the precise mirror-plus-K contract was previously published. Absence from this screen is not novelty evidence. The next literature pass should use an explicit review protocol, record databases and exclusion reasons, and obtain full texts for the closest papers.

## Next actions

1. Turn the exact CSC contribution into testable claims before searching for novelty.
2. Conduct a systematic related-work search focused on decision-time simulation, production traffic mirroring, and safe exploration.
3. Add a fidelity protocol that separates same-action calibration from alternative-action validity.
