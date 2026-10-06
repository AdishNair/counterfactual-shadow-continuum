# Cycle 5 reproducibility and delivery audit

**Status:** VERIFIED; deterministic read-only delivery audit, 2026-10-06.

## Question, evidence and method

Are the required research artifacts present, the frozen run inventory/configs/seeds exact, and raw/source/gate evidence unchanged? `experiments/cycle5_delivery_audit.py` streams SHA-256 checks and compares manifests without modifying results. Machine evidence: `research/tables/cycle5_delivery_audit.json`. Existing deterministic archived-source replay/summary verification is reused, not rerun.

## Findings

- Scheduled main/long runs: 86; execution status counts: {'COMPLETE': 86}.
- Exact factorial grid: True; unexpected seed overlap: []; config/factor errors: [].
- Main series artifact hashes: 1182 checked, 0 broken. Archived source hashes: 38 checked, 0 broken. Per-run provenance checks remain in JSON.
- Measured CSC/gate closure matches: True; current corrected CSC/gate differences: [].
- Prior replay/summary verification: VERIFIED, 86 runs, 41686 accepted branch replays; failures: [].
- Missing required artifacts: []; retained fault and cleanup archive checks are individually recorded, including failed validation attempts.
- Forbidden final trust checks: {'main_seed_overlap': [], 'observed_top_level_directories': ['calibration-20261005-v1', 'development-20261005-v1', 'source-freeze-20261005-v1'], 'unexpected_final_or_heldout_directories': [], 'scope': 'Cycle4 trust top-level directory inventory plus Cycle5 frozen seed plan; not exhaustive arbitrary-filesystem surveillance'}.
- Delivery failures: [].

## Limitations, open questions and next actions

These are byte/inventory/config checks, not physical traffic, hostile containment, OS-wide non-interference or hidden-file surveillance. Prior replay verification does not establish total resource accounting or recovery. The corrected source has local validation but no repeated main performance campaign. Independent reviews retain their methodological scope and open findings. Preserve all raw results; any new performance run requires fresh source/protocol identity and a unique output directory. Trust remains Decision D and learning BLOCKED.
