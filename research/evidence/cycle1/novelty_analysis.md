# CSC novelty analysis

**Status:** Conservative assessment from the verified screening in `research/evidence/cycle1/literature_review.md` and `research/literature/related_work_matrix.csv`.

## Question

Which parts of CSC are established, which may be differentiating, and what is required to make a defensible novelty claim?

## Evidence and assessment

| CSC element | Assessment | Basis |
|---|---|---|
| Virtual model informed by operational state | Established family of digital-twin/digital-shadow ideas. | [@grieves2017; @kritzinger2018] |
| What-if simulation to support a decision | Established digital-twin use class; the limited source set does not establish a CSC-specific mechanism. | [@grieves2017; @kritzinger2018] |
| Copying production traffic into a sandboxed execution | Established in production-driven patch testing. | [@durieux2017] |
| Estimating an unobserved action's value | Established counterfactual/OPE research problem, with assumptions and estimators. | [@rubin1974; @pearl2009; @li2011; @jiang2016; @thomas2016] |
| One authoritative production action plus K non-actuating alternative actions from an application-level anchor, with a same-action mirror used as a local calibration signal | Potentially differentiating *combination*, but unverified as novel. | No exact duplicate found in this limited screen; absence is not evidence. |
| Regret discounted by current mirror error | A repository-specific metric proposal, not yet a demonstrated estimator or contribution. | `research/RESEARCH_CONTEXT.md`; no validating study in the screened set. |
| Security/non-actuation contract | An engineering design intent. Local evidence is limited to application boundary behavior, and deployment enforcement remains unvalidated. | `research/RESEARCH_CONTEXT.md`, `research/RESEARCH_STATUS.md` |

## Recommended research position

Do not describe CSC as a new kind of counterfactual reasoning, digital twin, or shadow traffic. A defensible provisional position is:

> CSC is a proposed runtime pattern for recording calibrated, non-authoritative estimates of alternative actions at explicit application decision boundaries. It combines production-authoritative execution, non-actuating alternatives, shared input windows, and mirror-based model-error instrumentation.

This is a design description, not a novelty claim. Its research contribution would need to be framed around a precise mechanism and supported by direct comparisons, ideally one of: (1) a reliable relationship between mirror epsilon and alternative-branch error; (2) an isolation contract that is tested under a real threat model; or (3) a measured fidelity/cost result unavailable from a conventional digital-twin or shadow-test setup.

## Claim boundaries

The present prototype may claim **implemented and locally tested** deterministic branching, artifact replay, application-level actuation routing, and selected fault behavior, subject to the repository's existing evidence. It may not claim deployment-validated containment, real-time non-interference, causal validity, learning benefit, domain independence, or literature novelty.

## Limitations

This assessment has not conducted exhaustive database searches or full-text comparisons. It intentionally treats the strongest possible CSC novelty claim as unresolved. Any manuscript should replace this screen with a reproducible review protocol and cite the final versions of the closest works.

## Next actions

1. Specify one falsifiable differentiating mechanism before a full literature review.
2. Register comparative baselines: conventional what-if simulator, shadow traffic without alternatives, and OPE where logging assumptions permit.
3. Validate whether mirror epsilon predicts alternative-branch error across action distances, horizons, and deliberate model mismatch.
4. Repeat novelty screening across ACM DL, IEEE Xplore, USENIX, and digital-twin journals with retained search strings and exclusions.
