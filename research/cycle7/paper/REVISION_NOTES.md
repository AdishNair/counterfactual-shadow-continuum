# Revision notes

Status: editorial and technical-presentation revision complete. No experiment,
measurement regeneration or experiment-code change was performed. No result,
interval, table datum, plotted coordinate or bibliography entry was changed.

## Structural and technical changes

- Reorganized the article into Introduction, Related Work, Problem Formulation,
  Architecture, Implementation, Methodology, Results, Discussion, Limitations,
  and Conclusion. E1/E2/E3 name the experiments descriptively.
- Replaced the six-part contribution narrative with three contributions. Moved
  related work forward and retained its positioning table with shorter text.
- Consolidated containment into one table with all initial outcomes visible and
  revised-test outcomes alongside them. Initial FAIL, INCONCLUSIVE, NOT TESTED
  and N/A classifications are not replaced by later passes. Retained the failed
  memory observer and untested PID enforcement.
- Integrated the infrastructure service pilot into E2. Removed internal labels,
  paths, implementation class names, hashes and development narration from the
  article; the single artifact paragraph points to ARTIFACTS.md.
- Removed unused model-improvement/discounted quantities. Retained the mirror
  discrepancy and simulation-derived regret, with their references and units.
  Generalized the alternative-error denominator to 1/K while explicitly stating
  the evaluated K=2 case. No calculated result changed.
- Added the archived evidence deadline and distinct worker timeout, distinguished
  scheduler drops from executor rejection counters, and reported the observed
  incomplete-evidence mechanisms without inventing missing failure causes.
- Added explicit RQ answers and the exact exported per-seed paired reductions.
  Identified the stationary baseline's lack of forecasts/calibration in the
  abstract, introduction, methodology, results and discussion.
- Removed redundant yield, lifecycle and containment-status graphics. The three
  remaining figures are architecture, delay sensitivity and simulator results.
  Removed the duplicate delay row from the runtime table; the same values remain
  in Results and the plot. Re-rendered only the delay plot for label placement,
  from the existing exported coordinates and original label precision.
- Kept the original title, author blocks, IEEE template and bibliography style.
  Condensed the AI disclosure factually; author approval remains required.

## Numeric-diff result

The check expands every input table before tokenizing the original and revised
LaTeX, so abstract, body and tables are included. The full token counts, contexts,
source checksums and guards are in [revision-numeric-diff.json](revision-numeric-diff.json).
Numeric strings retain their original precision; no statistic was recalculated.
The original Results numeric-value set remains represented in revised Results.
The three simulator tables have identical numeric-token sequences. All initial
containment outcomes and all revised outcomes remain visible.

The expanded original has **297** numeric tokens; the revision has **287**. Changes below count occurrences, not changed measured values.

| Numeric token | Removed occurrences | Added occurrences | Disposition |
|---|---:|---:|---|
| `0` | 3 | 0 | Removed duplicate/unused-equation occurrence; measured zeros and failures remain. |
| `0.16` | 0 | 1 | Typesetting width; no experimental value. |
| `0.18` | 0 | 1 | Typesetting width; no experimental value. |
| `0.222` | 0 | 1 | Existing agreement values repeated in the revised abstract, including persistence. |
| `0.23` | 1 | 0 | Typesetting width; no experimental value. |
| `0.28` | 1 | 0 | Typesetting width; no experimental value. |
| `0.3` | 0 | 3 | Archived evidence-deadline setting, newly stated in method/result/caption. |
| `0.32` | 0 | 1 | Typesetting width; no experimental value. |
| `0.34` | 1 | 0 | Typesetting width; no experimental value. |
| `0.37` | 0 | 1 | Typesetting width; no experimental value. |
| `0.52` | 1 | 0 | Typesetting width; no experimental value. |
| `0.58` | 1 | 0 | Typesetting width; no experimental value. |
| `0.5979687500000036` | 0 | 1 | Copied verbatim from archived paired seed_values; newly displayed, not recalculated. |
| `0.65` | 1 | 0 | Typesetting width; no experimental value. |
| `0.69` | 1 | 0 | Typesetting width; no experimental value. |
| `0.778` | 0 | 1 | Existing agreement values repeated in the revised abstract, including persistence. |
| `0.9138802083333336` | 0 | 1 | Copied verbatim from archived paired seed_values; newly displayed, not recalculated. |
| `0.94` | 1 | 0 | Typesetting width; no experimental value. |
| `01` | 1 | 0 | Removed archive-path/hash fragment; full identifier remains in companion artifacts. |
| `1.088` | 1 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `1.28` | 1 | 0 | Version 1.28.0 stated once instead of twice; version unchanged. |
| `1.6872656250000007` | 0 | 1 | Copied verbatim from archived paired seed_values; newly displayed, not recalculated. |
| `1.819218749999999` | 0 | 1 | Copied verbatim from archived paired seed_values; newly displayed, not recalculated. |
| `120` | 1 | 0 | Removed duplicate delay-table occurrence; unchanged Results/plot and service-pilot findings remain. |
| `128` | 1 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `144` | 2 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `2` | 0 | 1 | Existing count/setting repeated for clarity or seed-position indexing; no new measured value. |
| `2.0` | 0 | 1 | Archived worker-timeout setting, newly stated. |
| `2.2061458333333257` | 0 | 1 | Copied verbatim from archived paired seed_values; newly displayed, not recalculated. |
| `2.647` | 1 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `256` | 2 | 0 | SHA-256 naming removed from prose; 256-item spool result remains. |
| `299` | 1 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `3` | 0 | 1 | Positions in the six-element seed export; not new experimental runs. |
| `3.648333333333335` | 0 | 1 | Copied verbatim from archived paired seed_values; newly displayed, not recalculated. |
| `4` | 0 | 1 | Positions in the six-element seed export; not new experimental runs. |
| `40` | 0 | 1 | Existing count/setting repeated for clarity or seed-position indexing; no new measured value. |
| `400` | 1 | 0 | Removed duplicate delay-table occurrence; unchanged Results/plot and service-pilot findings remain. |
| `403` | 1 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `5` | 0 | 1 | Existing count/setting repeated for clarity or seed-position indexing; no new measured value. |
| `512` | 1 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `56` | 1 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `6` | 0 | 3 | Existing count/setting repeated for clarity or seed-position indexing; no new measured value. |
| `60` | 2 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `64` | 1 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `65,207` | 1 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `69` | 0 | 1 | Existing count/setting repeated for clarity or seed-position indexing; no new measured value. |
| `72` | 1 | 0 | Consolidated duplicate reporting; same measured value remains in Results. |
| `77.78` | 0 | 1 | Existing agreement values repeated in the revised abstract, including persistence. |
| `89e73049` | 1 | 0 | Removed archive-path/hash fragment; full identifier remains in companion artifacts. |
| `93.11` | 1 | 0 | Removed duplicate prose occurrence; runtime table retains identical value. |
| `95.78` | 1 | 0 | Removed duplicate prose occurrence; runtime table retains identical value. |
| `96.00` | 1 | 0 | Removed duplicate prose occurrence; runtime table retains identical value. |
| `96.22` | 1 | 0 | Removed duplicate prose occurrence; runtime table retains identical value. |

Only typesetting widths and an archive/hash fragment disappear from the set of
unique numeric strings. Newly unique experimental numbers are the six exact
archived seed differences requested by the revision; the other additions are
pre-existing configuration settings or seed indices. The 1/K change is symbolic.
The discarded 1/2 factor and unevaluated improvement formulas are not altered
measurements. Removed repetitions of confidence bounds remain in Results with
exactly the original precision. No sign test, permutation test, interval update,
new rounding, percentage conversion or additional statistical analysis was run.

## Verification

- Compiled using the existing pinned Tectonic engine and offline cache: 9 US-Letter
  IEEEtran conference pages, 24 bibliography entries, no undefined citations or
  references, no overfull boxes. Four nonfatal underfull prose boxes remain.
- All 20 PDF fonts are embedded; no Type 3 fonts. Rendered pages were inspected
  for layout, tables, equations, figures, captions and references. The delay
  label is now inside the plot rather than overlapping the upper axis area.
- Every figure/table is referenced. The bibliography bytes and 24 used citation
  keys match the original exactly; reference numbering changes normally because
  related work now appears earlier. No citation or source was added.
- The abstract has 174 whitespace-delimited words. Its campaign size/completion
  scope is supported by VII-C; MAE and agreement by Table IV and VII-C/RQ1;
  the 120 requests by VII-B's service pilot; delay collapse and the unexecuted
  study by VII-A; memory inconclusiveness by Table III and VII-B.
- The compiled LaTeX inputs have no forbidden internal-label matches. Raw PDF
  extraction reports one apparent `gate`, from a line-broken `aggre-` / `gate`;
  after joining ordinary end-of-line hyphenation there are no matches. This is
  not an internal label. ARTIFACTS.md, the preserved backup and verification
  tooling intentionally contain exact old labels, paths and hashes. They are
  companion material, not article text. The article intentionally names only
  ARTIFACTS.md in its single reproducibility paragraph.
- Acronym definitions were checked in order: CSC and SUMO separately in the
  abstract and body; TraCI in Related Work; VAB, TTL, ACL and HMAC in Architecture;
  MAC in the architecture caption; CPU and GiB in E1; HTTP, DNS, TCP, MiB, OOM
  and PID in E2; MAE in E3; I/O and RSS in Results; TLS in Limitations.
  Redis and NATS are project/product names, not invented acronym expansions.
  The existing CSE(AIML) affiliation abbreviation is retained for author review.
- Symbols are defined at use: epoch t, anchor s_t, inputs x_t, production action,
  K excluding the mirror, production/mirror utilities and epsilon_t; E3 window i,
  horizon H, simulation queue reference, prediction, selected action and regret.
  Median p50 and ninety-fifth percentile p95 are explicitly identified.

Original source and PDF backup:
`results/manuscript-revision-20261111T104622Z-1ab3980b/original/`.
Final build, numeric audit, extracted PDF text, renders and provenance are in the
same revision directory, under `build-complete/`, `verification-complete/` and
`rendered-complete/`. Earlier build/check outputs remain preserved.

## NEEDS AUTHOR DECISION

1. **Title and target setting.** The title is unchanged. Suggested alternative:
   *Counterfactual Shadow Continuum: Bounded Non-Actuating Execution for
   Simulation-Based Decision Evaluation*. Authors should decide whether retaining
   ?cloud?edge? as design intent is appropriate for single-host evidence.
2. **AI disclosure and venue policy.** The disclosure was shortened without
   removing attribution or the approval requirement. Authors must verify its
   scope and final wording. The previously checked ITSC 2027 policy prohibited
   substantive LLM-generated manuscripts, so this work must not be represented
   as grammar-only assistance. No conference compliance or author approval is
   asserted; target-specific page, anonymity and AI policies still need approval.
3. **Deadline and incomplete evidence.** The deadline is present in archived
   pre-registration: `shadow_result_deadline_s=0.3`, versus
   `shadow_timeout_s=2.0`. The archived ledger starts the deadline after production
   commit. No deadline was guessed. An inspected normal-load archive records
   `scheduler_capacity` drops and FAILED completions, but its failed-completion
   entries do not identify every underlying cause. The paper states only those
   observations. A complete causal breakdown would require a separately scoped
   archive analysis; no percentages or causal allocation were manufactured here.
4. **Replication and additional analysis.** The six exact paired seed reductions
   are now shown in archive-array order, not rounded into new values. No new
   statistical test was performed. Authors may consider a pre-specified exact
   paired analysis from these exports; the current descriptive intervals remain
   unchanged. More independent seeds, traffic geometries and operational
   environments would require new evaluation, not editorial changes or reuse of
   exposed held-out seeds as fresh confirmation.
5. **Predictor baseline and RQ wording.** The question now identifies the
   development-calibrated, forecast-using predictor; it does not attribute the
   difference to calibration alone or to CSC. A forecast-aware baseline, an
   uncalibrated-model comparison and broader action-budget experiments would
   require an explicitly designed new experiment. No such results are implied.
6. **RQ2 coverage.** Existing horizon, mismatch, agreement and regret outcomes are
   reported, with aggregate mirror error retained. The archived export also has
   condition-level mirror fields; a full mirror-by-horizon report or prospective
   trust-rule study is not added here. Authors should decide whether the existing
   descriptive answer is sufficient for their venue. No new aggregation was run.
7. **Missing adjacent related work.** Reviewers may expect closer comparisons with
   dark launches/canary and shadow deployment in production systems, deterministic
   record-and-replay, and simulation-in-the-loop traffic signal control. Verify
   primary sources before adding citations; this revision adds none. The existing
   targeted literature set does not establish exhaustive novelty.
8. **Containment and operations.** PID enforcement remains untested; the memory
   observer criterion remains unmet despite the OOMKilled event. TLS,
   restart/HA/durable exactly-once behavior, whole-host containment and resource
   non-interference remain unestablished. Real multi-host/cloud?edge or physical
   validation would require new protocols and experiments. No trust, policy
   promotion, learning or operational-readiness upgrade is made.
9. **Metadata and availability.** Authors must verify names, CSE(AIML)
   affiliations, emails, contribution attribution and release permissions.
   Artifact paths are private local locators. No public release, DOI, conference
   submission or acceptance is asserted.

## Uncertain or potentially misleading source passages

No original numerical inconsistency was identified or silently repaired.
The original agreement fraction 0.778 and percentage 77.78% use different
reporting precision; both are retained exactly, and persistence remains 0.222
rather than a newly converted percentage. Counts of executions, windows and
independent seeds are distinguished explicitly. The old generic model-improvement
and discounted quantities were removed because they were not evaluated in the
reported results; simulation-derived regret remains unchanged.

The cause of every failed runtime branch is unavailable in the inspected
lifecycle entries, and is explicitly left unresolved. No speculative explanation
was inserted. The comparison of shared-state/inputs is explicitly limited to the
runtime experiment; E3 predictors receive reduced anchors and forecasts, while
reference simulations alone receive fixed future demand. Existing literature
claims and affiliations remain subject to author verification; no newly uncertain
scientific claim was retained as an established finding.
