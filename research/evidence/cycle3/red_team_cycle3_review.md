# Cycle 3 red-team review: uncertainty, trust signal, and asynchronous design

**Status:** Independent protocol and evidence review, 2026-09-28. No historical
result or artifact was modified.

## Question

Do the Cycle 3 analyses and proposed trust-signal/asynchronous protocols remain
scientifically falsifiable, and what must change before a positive result could
be interpreted?

## Evidence reviewed

This review read the Cycle 3 analysis protocol, failure analysis, uncertainty
taxonomy, literature note, trust-signal protocol, asynchronous design, and the
derived tables/figures. It also used the immutable factorial status and prior
red-team review as the source of the underlying negative gate result. The
failure tables are read-only derived data; they are not new independent
observations.

## Overall assessment

Cycle 3 correctly preserves the main negative finding: same-action mirror error
is not a uniform alternative-error bound in the authored J1 factorial. Its
exploratory associations are non-uniform across conditions (the reported
divergence/error correlations include positive, near-zero, and negative values),
so they support a candidate signal only, never the proposed A+B+C explanation
as a causal decomposition.

The next protocol is scientifically meaningful **if it fails**. A failure on
the new final held-out seeds would reject the narrow proposition that an
online-observable selected-branch divergence/horizon abstention selector repairs
the mirror blind spot under the declared authored mismatches. It would not show
that all CSC variants, other uncertainty methods, real traffic, or every
abstention policy fails. That bounded falsification value is sufficient reason
to run it once the changes below are made.

## CRITICAL required changes

### C1 - Prevent abstention from creating a vacuous apparent success

**Evidence.** The trust protocol requires median abstention below 0.95. With
eight anchors per run, a selector can recommend at only one anchor (12.5%
coverage) and still satisfy that condition. Precision is undefined for runs
without recommendations, while selection favours median recommendation coverage
only after the other criteria. The prior factorial already shows cells with
median abstention 1.0, so a sparse-support rule is a realistic failure mode.

**Risk.** A candidate could meet precision and false-positive criteria by
withholding almost all decisions, yet be described as a reliable trust signal.
This would be an operationally uninformative result and a form of abstention
gaming, even if no threshold was selected dishonestly.

**Required change before collection.** Add a frozen minimum per-cell
recommendation exposure: for example, a minimum median run-level recommendation
count and a minimum aggregate number of recommending seed-runs, both reported
with undefined-precision runs in the denominator. Require the final held-out
rule to beat or match baseline false-positive rate at comparable coverage, not
only avoid median abstention of 1.0. Treat insufficient exposure as D, not a
pass. The exact numbers must be justified and frozen before calibration.

### C2 - Make the proposed reference genuinely independent at the implementation boundary

**Evidence.** The current factorial oracle reused `ProductionWorld`, shared
metrics, and shared utility, so it was independent only relative to the SEM.
The new protocol correctly requires a separately maintained transition and
metric reference, but that reference does not yet exist. The oracle will define
every reliability label, calibration choice, and final endpoint.

**Risk.** A shared transition, action semantics, queue metric, random-number
rule, or hidden import could make a new “independent reference” repeat the
circularity of the prior study. Superficial mutation tests could pass while
missing shared specification mistakes.

**Required change before collection.** Block collection until a reviewed,
separately implemented reference package is source-isolated from `csc.world`,
`csc.compare`, and SEM modules; its source bundle/digest must be captured with
the series. Add bidirectional mutation tests that alter production and reference
transition/metric behavior independently, plus a test that the reference cannot
import SEM code. Declare which shared contracts are unavoidable and test their
serialization separately. Keep the result label as authored-software reference,
not factual or physical ground truth.

## MAJOR required changes

### M1 - Fully specify the calibration calculation to remove threshold discretion

**Evidence.** The protocol fixes candidate divergence quantiles
{0.25, 0.50, 0.75, 1.00} but does not state the population used for each
quantile, quantile interpolation, treatment of ties/zero divergence, whether a
single global or cell-specific `d` is selected, or how candidates with no
recommendations are ordered. `d=1.00` can be equivalent to no divergence
restriction.

**Risk.** Reasonable implementation choices can materially change coverage and
which rule “wins,” allowing accidental post-hoc threshold selection despite a
frozen grid.

**Required change before collection.** Publish a machine-readable design and
deterministic selector pseudocode that defines the calibration population,
quantile algorithm, global-versus-cell scope, inclusive/exclusive boundary,
candidate ordering, ties, undefined rates, and an equivalence check that labels
a nonbinding divergence threshold as baseline. Hash the design, driver,
analyzer, and verifier before development data are used.

### M2 - Keep the Cycle 3 derived held-out analysis out of the new performance claim

**Evidence.** `cycle3_analysis_protocol.md` permits descriptive use of the
prior calibration, evaluation, and held-out series; `failure_analysis.md` and
`failure_relationships.csv` report all three. The trust-signal candidate was
motivated by those inspected results.

**Assessment.** This is honest exploratory hypothesis generation, not a
violation by itself. It means the previous held-out series is no longer held out
for this new hypothesis. Only the fresh 841--860 final seed block can support
the candidate's performance claim.

**Required change before collection.** State this explicitly in the new series
manifest and final report: prior factorial blocks are development/exploratory
evidence for the trust-signal hypothesis. Prevent reading the 841--860 outcome
records until source identity, candidate selection, calibration output, and
final analysis report template are committed. Do not revisit the candidate
family after final results; a failure requires a new study and seed split.

### M3 - Preserve correct statistical units and factor coverage

**Evidence.** The protocol correctly calls seed x full cell the independent
unit and treats eight anchors as repeated observations. However, run-level
rates from only eight anchors remain discrete, and a single seed is shared
across its factorial cells. The Cycle 3 derived 12,960 alternative observations
and per-stratum Spearman values are descriptive, not independent replications.

**Risk.** Pooling anchors/actions or flattening all cells for selection would
produce spuriously stable precision, false-positive, and correlation estimates.

**Required change before collection.** Reduce anchors within run; use seed-
clustered/cellwise bootstrap intervals; require all declared cells to meet the
criteria; report recommendation count, incomplete count, and undefined rate per
run and cell. Do not summarize factor effects as causal without a model that
accounts for shared seeds and without the missing rate-only and incident-only
cells already specified by the new protocol.

### M4 - Test observability rather than using regime labels as a hidden oracle

**Evidence.** The protocol says unsupported or unknown input semantics force
abstention, and `trust_signals.md` warns that reference-only mismatch labels
would leak oracle information. In the authored study, a configured SEM can know
whether it models an incident field, but it cannot in general know all real
mismatch or reference outcomes.

**Risk.** Passing a ground-truth `mismatch_regime`, a reference-derived
unsupported flag, or a retrospective incident label to the selector would
produce an unrealistically effective abstention rule.

**Required change before collection.** Define a feature allowlist sourced only
from the anchor, supplied window, SEM output, and static SEM capability
declaration. Log every selector input. Add adversarial tests for unknown and
misdeclared semantics, late/missing incident metadata, and a no-oracle-import
check. Stratify results by known versus unknown/misdeclared conditions rather
than silently treating all simulated labels as observable.

### M5 - Do not overinterpret trajectory divergence as a cause or domain-general signal

**Evidence.** `failure_relationships.csv` contains condition-specific
associations that vary in direction, including negative values. The J1 action
space, queue utility, engineered incidents, fixed anchor construction, and
short action plans remain domain-specific. Large alternative/mirror queue
distance can be a normal beneficial action effect, a model error marker, or
both.

**Required change before collection.** Keep the hypothesis predictive and
falsifiable: “does this observable abstention feature improve held-out decision
reliability in declared J1 cells?” Do not describe trajectory divergence as a
causal uncertainty component or general CSC signal. Report action margins,
action changes, and choice-value loss alongside divergence so a selector is not
credited merely for avoiding large, beneficial action effects.

## ASYNCHRONOUS DESIGN REVIEW

The asynchronous ledger proposal is a reasonable implementation hypothesis,
not evidence of non-interference. Its explicit whole-batch admission,
immutable production journal, terminal backpressure/expiry statuses, epoch-order
comparison, and late-result discard rule are strengths. The proposed tests can
establish local logical properties such as “epoch N+1 opens before shadow N
finishes.”

Two claim boundaries must remain hard requirements:

- A nonblocking ledger poll does not prove a wall-clock deadline. Production can
  still be delayed by capture, journal writes, process startup, CPU contention,
  scheduler pauses, or the authoritative world itself.
- Expired tasks retaining permits protects the stated bound, but requires
  measured queue/task/byte and process-liveness telemetry. Otherwise a long
  tail of expired running subprocesses can consume the host while the ledger
  reports accepted production progress.

Before any timing claim, implement the listed invariant tests, add an
independent production-side monotonic-clock probe, distinguish enqueue, start,
completion, expiry, and finalization timestamps, and run a separately
registered fault/load experiment. Results would remain local cooperative-worker
evidence until a policy-enforcing deployment study exists.

## Evidence that remains supportable

- The frozen factorial's global gate failure is preserved and remains the
  correct starting point for Cycle 3.
- The taxonomy's 45 low-mirror/high-alternative-error and 609
  high-mirror/low-alternative-error observations are useful descriptive examples
  of non-uniformity, subject to their within-series quartile definitions.
- A fresh, source-isolated, fully split trust-signal study can reject a narrow
  observable-divergence hypothesis without touching production authority or
  enabling learning.

## Learning decision

Learning is **not** justified. No Cycle 3 artifact changes the RQ4 failure,
creates external alternative ground truth, validates the new selector, or
establishes hostile containment and real-time non-interference. A future
positive trust-signal result would still be an authored-J1 calibration result;
it would need another explicit review before any learner is considered.

## Final answer on failure value

Yes. If the next protocol fails after the required safeguards, it remains
scientifically meaningful: it rejects the simple, interpretable premise that
mirror-gated selected-branch divergence plus horizon can produce an adequate
abstention/recommendation rule across the declared authored J1 cells. Preserve
that failure as evidence. Do not respond by expanding thresholds, inspecting the
final holdout for a new feature, or claiming that CSC itself has been disproved.

## Amendment confirmation

The amendment closes the design-level issues identified in this review: it
restricts the online feature interface, fixes the calibration grid and selector,
defines exposure-aware cell criteria, and strengthens reference isolation. No
scientific design defect blocks collection once those controls are implemented.
The implementation freeze must select no candidate when zero comparable
calibration anchors exist, and must hash the executable factor/config generator,
reference package, selector, analysis, verifier, report template, and firewall
enforcement code before it produces or reads final held-out records.
