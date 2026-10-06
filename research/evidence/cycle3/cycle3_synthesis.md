# Cycle 3 synthesis: explaining counterfactual failure

**Status:** Complete explanatory/design cycle, 2026-09-28. No new confirmatory data was collected and no historical evidence was changed.

## What Decision D taught us

Same-action mirror error is not a uniform conservative estimate of alternative-action error in the declared authored J1 factorial. The read-only analysis found both false-confidence examples (45 low-mirror/high-alternative-error observations) and unnecessary-abstention examples (609 high-mirror/low-alternative-error observations). These counts use within-series descriptive quartiles and are not operational rates or new independent observations.

The strongest supported explanation is narrow: the mirror measures model discrepancy along the production action, while an alternative can create a different predicted trajectory. This is consistent with condition-dependent error/divergence relationships and targeted rollout-bias literature. It is a descriptive structural hypothesis, not evidence that trajectory divergence causes alternative error.

Plausible alternatives remain: shared authored-reference assumptions, action- and mismatch-specific transition defects, short constructed anchor histories, horizon effects, and an insufficient scalar utility can all contribute. The current evidence cannot distinguish these explanations causally.

## Proposed trust mechanism

The only small proposed mechanism is a conservative abstention selector: existing estimated-gain-over-epsilon, plus a selected-alternative SEM trajectory-divergence condition and a horizon condition. It receives only an allowlisted online input set; mismatch labels, reference outcomes, and oracle values are forbidden. It is proposed because it is interpretable and falsifiable, not because Cycle 3 demonstrated that it works.

## Exact next experiment and falsification

`research/archive/cycle4/protocol_support/trust_signal_experiment_protocol.md` freezes a fresh development (801--820), calibration (821--840), and final held-out (841--860) seed split; five separately reported mismatch regimes; eight anchors/run; a source-isolated reference; and strict per-cell reliability, coverage, and recommendation-exposure rules. The selector is rejected if no calibration candidate qualifies or any held-out cell fails. This makes a negative result useful: it rejects the narrow divergence/horizon selector for declared J1 conditions without claiming to disprove CSC broadly.

## Viability and boundaries

CSC remains viable as a research mechanism for recording non-actuating, anchored alternative estimates and studying their calibration. It is not viable yet as a policy-evidence mechanism. Physical/factual counterfactual validity, external reference independence, closed-loop policy value, hostile containment, and real-time non-interference remain unproven.

The asynchronous systems experiment is ready only as the proposed bounded-ledger design in `research/evidence/cycle3/async_noninterference_design.md`. It needs implementation invariant tests and a separately registered load/fault study before any non-interference claim. Learning remains blocked.
