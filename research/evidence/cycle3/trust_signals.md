# Candidate counterfactual trust signals

**Status:** Proposed, not implemented and not calibrated. These signals are
motivated by the Cycle 3 decomposition and targeted literature review.

| Signal | Hypothesis | Required implementation | Calibration / held-out method | Possible failure mode |
|---|---|---|---|---|
| Mirror error (`epsilon`) | Same-action residual is relevant but insufficient alone. | Existing field. | Baseline only; no retuning on existing held-out data. | Low mirror error with high alternative error. |
| Alternative-to-mirror SEM trajectory divergence | A branch that departs strongly from the mirror is more exposed to extrapolation error. | Record integrated/max/terminal queue distance between selected alternative SEM trace and mirror SEM trace. | Freeze definition; select any boundary on new calibration seeds and evaluate once on new held-out seeds. | Shared SEM error can make paths agree while both are wrong; divergence may be beneficial. |
| Horizon | Longer windows may compound model error. | Existing configuration label. | Stratify all measures by H; predeclare a maximum-H candidate family before calibration. | Error need not grow monotonically. |
| Known-input regime completeness | An estimate is less trustworthy when required input semantics are unsupported. | Explicit metadata stating whether SEM models provided incident fields. | Unknown/unsupported semantics force abstention; test detection errors on new data. | Real mismatch may be unknown; reference-only mismatch labels would leak oracle information. |
| Alternative utility margin | Small predicted separation may be fragile. | Record best-versus-next estimated alternative margin. | Development-only unless a later protocol freezes it. | Large margins can be confidently wrong. |
| Ensemble disagreement | Diverse models might reveal alternative-specific uncertainty. | New genuinely diverse SEM family. | Separate implementation and new calibration/evaluation. | Shared misspecification can make members agree. |

## Narrow proposal

The next study tests only an interpretable conjunction: retain the existing
gain-versus-epsilon requirement and abstain when selected-alternative SEM
trajectory divergence or horizon exceeds a calibration-selected conservative
limit. Known unsupported input semantics force abstention. This is a predictive
hypothesis for declared J1 cells, not a causal or domain-general account of
uncertainty. The exact rule is frozen in
`research/archive/cycle4/protocol_support/trust_signal_experiment_protocol.md`.

This proposal may fail usefully: failure would reject a simple
trajectory-divergence trust explanation. It does not alter non-actuation or
unblock learning.
