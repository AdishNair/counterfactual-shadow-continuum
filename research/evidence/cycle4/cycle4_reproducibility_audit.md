# Cycle 4 reproducibility audit

**Status:** Deterministic source/artifact replay and summary checks, 2026-10-05.
The machine verdict is `tables/cycle4_reproducibility_verification.json`;
this document does not substitute for that record.

## Question and method

Can a reader reproduce the completed Cycle 4 results from their preserved
sources and records? `experiments/verify_cycle4_reproducibility.py` invokes the
archived trust verifier on each split, the archived async verifier on every
registered run, and full archived calibration reanalysis. It compares output
hashes of selection, candidate cell/run CSVs and predefined negative controls.
Raw JSONL is processed by scripts; no manual sampling supplies the verdict.

| Series | Expected units | Deterministic verification |
|---|---|---|
| `results/cycle4-trust/development-20261005-v1` | 1,200 runs;60 cells;801–820;8 anchors | Hashes, reference/SEM replay, features, saved random order, exact grid |
| `results/cycle4-trust/calibration-20261005-v1` | 1,200 runs;60 cells;821–840;8 anchors | Same checks plus 17 candidate summaries and full archived reanalysis |
| Trust final841–860 | Zero generated runs after no selection | Runner/analysis gates, stage record and no final directory |
| `results/cycle4-async/local-20261005-v1` | 150 primary+12micro runs;12 epochs | Source/artifact/config hashes, exact registry, replay/journal join, capacities, trajectories, raw summaries |

## Findings and provenance

Separate trust verification records report 28,800 replayed action pairs per
split, no hash/replay/factor errors, disjoint seed blocks and one bundle digest.
The async record verifies 162 runs, 3,964 successful branch trajectories and
17 archived files, with exact raw-summary regeneration. The combined verdict
also compares complete deterministic trust analysis outputs, so passing a few
candidate flags alone cannot conceal changed tables or controls.

Each source bundle records configuration/design and script identity, Python/runtime
versions, input/workload hashes and per-record seed/factors. Async records
selector version as not applicable. Trust selector implementation/firewall
is source-hashed. UTC provenance and monotonic completion timestamps are kept
separate from the fields that determine trajectory hashes. Git identity may
be unavailable: source digests are the usable code identity in this workspace.
Both archives must accompany raw results when preserving the research.

Current-tree hardening can differ from measured archives. The final live utility
overflow rejection and extra journal/duplicate tests are locally tested; their
timing was not measured in this series. Verification executes archived sources
and does not silently substitute the newer implementation.

## Limits and next actions

An intact manifest/hash chain proves reproducibility against recorded identity,
not independent truth or protection from deliberate coordinated rewriting.
Workflow gates and absence of a final series support compliant staged access;
there is no general filesystem access log proving arbitrary reads absent.
Historical series were not modified by these scripts, but no full initial
filesystem hash inventory was taken to independently prove absence of every
external historical write. Wall-clock timings can be regenerated as summaries;
the exact host timing values cannot be recreated deterministically.

Flushed single-writer JSONL is not durable crash-transaction storage. Only
terminal completed series support these results. New-run restart and stale-result
rejection are tested; durable interrupted-run recovery remains unestablished.
Use a new immutable series for future work and retain any inconclusive result.
