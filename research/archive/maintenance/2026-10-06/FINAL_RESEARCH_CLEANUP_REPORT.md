# Final pre-Cycle-6 research cleanup report

**Status:** Completed 2026-10-07. This was a documentation/path cleanup only. Cycle 6 was not started; no performance experiment ran; runtime behavior and scientific conclusions were not changed.

## Final active research context

The only active top-level research state documents are:

- `research/AGENTS.md`
- `research/RESEARCH_CONTEXT.md`
- `research/RESEARCH_STATUS.md`
- `research/CLAIM_EVIDENCE_MATRIX.md`
- `research/HUMAN_GUIDE.md`

`research/literature/`, `research/evidence/`, `research/archive/`, `research/cycle6/`, `research/tables/`, and `research/figures/` hold supporting, historical, future-work, or generated material. `research/cycle6/README.md` reserves the future workspace and explicitly states that Cycle 6 has not begun.

## Exact moved files

### Literature

- `research/bibliography.bib` -> `research/literature/bibliography.bib`
- `research/related_work_matrix.csv` -> `research/literature/related_work_matrix.csv`

### Evidence

- `research/CYCLE4_EXECUTIVE_SUMMARY.md` -> `research/evidence/cycle4/CYCLE4_EXECUTIVE_SUMMARY.md`
- `research/CYCLE5_EXECUTIVE_SUMMARY.md` -> `research/evidence/cycle5/CYCLE5_EXECUTIVE_SUMMARY.md`
- `research/async_noninterference_design.md` -> `research/evidence/cycle3/async_noninterference_design.md`
- `research/async_state_machine_audit.md` -> `research/evidence/cycle4/async_state_machine_audit.md`
- `research/confirmatory_factorial_amendment.md` -> `research/evidence/cycle2/confirmatory_factorial_amendment.md`
- `research/counterfactual_uncertainty_literature.md` -> `research/evidence/cycle3/counterfactual_uncertainty_literature.md`
- `research/counterfactual_validity.md` -> `research/evidence/cycle1/counterfactual_validity.md`
- `research/cycle3_analysis_protocol.md` -> `research/evidence/cycle3/cycle3_analysis_protocol.md`
- `research/cycle3_synthesis.md` -> `research/evidence/cycle3/cycle3_synthesis.md`
- `research/cycle4_async_analysis.md` -> `research/evidence/cycle4/cycle4_async_analysis.md`
- `research/cycle4_async_protocol.md` -> `research/evidence/cycle4/cycle4_async_protocol.md`
- `research/cycle4_reproducibility_audit.md` -> `research/evidence/cycle4/cycle4_reproducibility_audit.md`
- `research/cycle4_trust_analysis.md` -> `research/evidence/cycle4/cycle4_trust_analysis.md`
- `research/cycle5_evidence_loss_analysis.md` -> `research/evidence/cycle5/cycle5_evidence_loss_analysis.md`
- `research/cycle5_failure_recovery.md` -> `research/evidence/cycle5/cycle5_failure_recovery.md`
- `research/cycle5_instrumentation_diagnostic.md` -> `research/evidence/cycle5/cycle5_instrumentation_diagnostic.md`
- `research/cycle5_protocol.md` -> `research/evidence/cycle5/cycle5_protocol.md`
- `research/cycle5_red_team_review.md` -> `research/evidence/cycle5/cycle5_red_team_review.md`
- `research/cycle5_reproducibility_audit.md` -> `research/evidence/cycle5/cycle5_reproducibility_audit.md`
- `research/cycle5_results_analysis.md` -> `research/evidence/cycle5/cycle5_results_analysis.md`
- `research/domain_adapter_readiness.md` -> `research/evidence/cycle4/domain_adapter_readiness.md`
- `research/experiment_protocol.md` -> `research/evidence/cycle1/experiment_protocol.md`
- `research/experiments.md` -> `research/evidence/cycle1/experiments.md`
- `research/failure_analysis.md` -> `research/evidence/cycle3/failure_analysis.md`
- `research/generalization.md` -> `research/evidence/cycle1/generalization.md`
- `research/information_timing_audit.md` -> `research/evidence/cycle5/information_timing_audit.md`
- `research/limitations.md` -> `research/evidence/cycle1/limitations.md`
- `research/literature_review.md` -> `research/evidence/cycle1/literature_review.md`
- `research/methodology.md` -> `research/evidence/cycle1/methodology.md`
- `research/novelty_analysis.md` -> `research/evidence/cycle1/novelty_analysis.md`
- `research/red_team_cycle3_review.md` -> `research/evidence/cycle3/red_team_cycle3_review.md`
- `research/red_team_cycle4_review.md` -> `research/evidence/cycle4/red_team_cycle4_review.md`
- `research/red_team_factorial_review.md` -> `research/evidence/cycle2/red_team_factorial_review.md`
- `research/red_team_review.md` -> `research/evidence/cycle1/red_team_review.md`
- `research/reference_fidelity_analysis.md` -> `research/evidence/cycle1/reference_fidelity_analysis.md`
- `research/research_questions.md` -> `research/evidence/cycle1/research_questions.md`
- `research/results_analysis.md` -> `research/evidence/cycle1/results_analysis.md`
- `research/runtime_retention_design.md` -> `research/evidence/cycle5/runtime_retention_design.md`
- `research/statistical_methodology.md` -> `research/evidence/cycle1/statistical_methodology.md`
- `research/trust_signals.md` -> `research/evidence/cycle3/trust_signals.md`
- `research/uncertainty_taxonomy.md` -> `research/evidence/cycle3/uncertainty_taxonomy.md`
- `research/warm_worker_correctness.md` -> `research/evidence/cycle5/warm_worker_correctness.md`

### Archive

- `research/DOCUMENTATION_AUDIT.md` -> `research/archive/maintenance/2026-10-06/DOCUMENTATION_AUDIT.md`
- `research/DOCUMENTATION_CLEANUP_REPORT.md` -> `research/archive/maintenance/2026-10-06/DOCUMENTATION_CLEANUP_REPORT.md`
- `research/cycle4_protocol_preflight.md` -> `research/archive/cycle4/protocol_support/cycle4_protocol_preflight.md`
- `research/cycle4_trust_preflight_verification.json` -> `research/archive/cycle4/protocol_support/cycle4_trust_preflight_verification.json`
- `research/cycle4_trust_preoutcome_specification.md` -> `research/archive/cycle4/protocol_support/cycle4_trust_preoutcome_specification.md`
- `research/cycle4_trust_report_template.md` -> `research/archive/cycle4/protocol_support/cycle4_trust_report_template.md`
- `research/cycle4_trust_source_isolation_audit.md` -> `research/archive/cycle4/protocol_support/cycle4_trust_source_isolation_audit.md`
- `research/cycle4_trust_stage_ledger.json` -> `research/archive/cycle4/protocol_support/cycle4_trust_stage_ledger.json`
- `research/cycle5_post_review_campaign_hardening.md` -> `research/archive/cycle5/post_collection_hardening/cycle5_post_review_campaign_hardening.md`
- `research/cycle5_post_review_hardening.md` -> `research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening.md`
- `research/cycle5_post_review_hardening_v2.md` -> `research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v2.md`
- `research/cycle5_post_review_hardening_v3.md` -> `research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v3.md`
- `research/cycle5_post_review_hardening_v4.md` -> `research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v4.md`
- `research/cycle5_post_review_hardening_v5.md` -> `research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v5.md`
- `research/cycle5_post_review_rereview.md` -> `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview.md`
- `research/cycle5_post_review_rereview_v2.md` -> `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v2.md`
- `research/cycle5_post_review_rereview_v3.md` -> `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v3.md`
- `research/cycle5_post_review_rereview_v4.md` -> `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v4.md`
- `research/cycle5_post_review_rereview_v5.md` -> `research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v5.md`
- `research/cycle5_protocol_rereview.md` -> `research/archive/cycle5/protocol_review/cycle5_protocol_rereview.md`
- `research/cycle5_protocol_review.md` -> `research/archive/cycle5/protocol_review/cycle5_protocol_review.md`
- `research/trust_signal_experiment_protocol.md` -> `research/archive/cycle4/protocol_support/trust_signal_experiment_protocol.md`

A machine-readable source/destination inventory and pre-move current-tree reference record is retained at `path_refactor_inventory.json` beside this report.

## Exact deleted files

- `research/cycle5_post_review_rereviewer_execution.log`
- `research/cycle5_post_review_rereviewer_v2_execution.log`
- `research/cycle5_post_review_rereviewer_v3_execution.log`
- `research/cycle5_post_review_rereviewer_v4_execution.log`
- `research/cycle5_post_review_rereviewer_v5_execution.log`
- `research/cycle5_protocol_rereviewer_execution.log`
- `research/cycle5_protocol_reviewer_execution.log`
- `research/cycle5_protocol_reviewer_execution_v2.log`
- `research/cycle5_red_team_reviewer_execution.log`
- `research.zip`
- `csc/__pycache__/` (removed before and after tests)
- `experiments/__pycache__/` (removed before and after tests)
- `tests/__pycache__/` (removed before and after tests)

The first nine deleted entries are the authorized temporary execution logs; `research.zip` was the unreferenced redundant snapshot. The last cache entries were removed after test execution.

## Current-tree references changed

- Exact current-tree path replacements were made before each move; 59 current text/source files were remapped by the path refactor.
- Eleven relative Markdown links inside relocated historical records were repaired after the move.
- `README.md`, `ARCHITECTURE.md`, `IMPLEMENTATION_STATUS.md`, `RESULTS.md`, and all five canonical research documents now point to current/evidence/archive locations as appropriate.
- `AGENTS.md` now explicitly forbids recursive ingestion of both `research/evidence/` and `research/archive/`.
- Cycle 4 and Cycle 5 scripts were redirected to their relocated current-tree evidence/archive paths. Immutable source snapshots under `results/` were not edited.

## Immutable paths intentionally untouched

No file below `results/` was edited. Before cleanup the result tree contained **7858 files** with aggregate path/content SHA-256 `9dbbfbdd4ea946f6e6926c9ea213821ba49d6735880d2494d1f266be0a8c1cec`. After cleanup and tests it contains **7858 files** with aggregate SHA-256 `9dbbfbdd4ea946f6e6926c9ea213821ba49d6735880d2494d1f266be0a8c1cec`. The values match: **True**.

Historical manifests and archived source snapshots still contain their original paths and hashes. They were deliberately not rewritten to make relocation appear historical.

## Verification

- Full unit suite: **108 tests passed in 29.102 seconds** (`C:\Python314\python.exe -m unittest discover -v`).
- Broken local Markdown links outside `results/`: **0**.
- Missing required literal `research/...` paths in current Python: **1**.
- The only reported literal is `experiments/cycle5_async.py` -> `research/tables/cycle5_warm_gate.json`. It is a deliberately optional source-bundle input: the existing copy loop checks `is_file()` and skips it when absent. No artifact was fabricated merely to satisfy a static scan.
- Runtime semantics: unchanged; the unit suite covers the current source after path-only script/document refactoring.

## Counts and blocked moves

- Top-level `research/` file count: **80 before**, **5 after**.
- Files moved to `research/evidence/`: **42**.
- Files moved to `research/archive/`: **22** (including the two prior maintenance records).
- Literature files moved: **2**.
- Total moved by this cleanup: **66**.
- Deleted unique file/directory targets: **13**.
- Blocked moves: **none**. Files with source-hash or script dependencies were moved only after current-tree references were updated; immutable result-source copies were left in place.

## Scientific state preserved

Trust remains **Decision D**. Learning remains **BLOCKED**. Cycle 5 remains **CLOSED**. The immutable 86-run archive remains the sole Cycle 5 performance source. The v5 108-test gate remains correctness-gate evidence only; no corrected-source performance experiment exists. No Cycle 5 measured conclusion was revised.

## Final research tree

```text
research/
  AGENTS.md
  RESEARCH_CONTEXT.md
  RESEARCH_STATUS.md
  CLAIM_EVIDENCE_MATRIX.md
  HUMAN_GUIDE.md
  literature/
    bibliography.bib
    related_work_matrix.csv
  evidence/
    cycle1/ cycle2/ cycle3/ cycle4/ cycle5/
  archive/
    cycle1/ cycle2/ cycle3/ cycle4/ cycle5/ maintenance/
  cycle6/
    README.md
  tables/
  figures/
```
