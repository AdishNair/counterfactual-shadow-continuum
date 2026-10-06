# CSC repository instructions

## Purpose and terms

Counterfactual Shadow Continuum (CSC) evaluates alternate decisions from a
captured decision state. Production is the only authoritative branch. A mirror
is a non-actuating same-action shadow used to measure model error. A shadow is a
non-actuating alternative-action branch. `K` always means the number of distinct
alternative actions and excludes mirrors.

## Non-negotiable rules

- Production outcomes and state are authoritative only within the declared test
  environment. Shadow outcomes are estimates and must retain that provenance.
- Shadows must not actuate or mutate authoritative state. Never weaken or bypass
  the actuator boundary for an experiment.
- Clearly label functionality as proposed, implemented, locally tested, or
  deployment-validated. Do not upgrade a category without evidence.
- Never fabricate measurements, infrastructure validation, citations, DOIs, or
  literature claims. Preserve negative and inconclusive findings.
- Treat existing `results/` runs as immutable evidence. New runs require a new,
  unique output directory; do not overwrite, delete, or silently regenerate them.
- Use deterministic scripts for bulk extraction, statistics, tables, hashes,
  replay, and plots. Interpret their compact outputs; do not calculate research
  conclusions from selective manual inspection.

## Working conventions

- Read [research/RESEARCH_CONTEXT.md](research/RESEARCH_CONTEXT.md) before
  research work and [research/RESEARCH_STATUS.md](research/RESEARCH_STATUS.md)
  when current evidence matters. Retrieve only files relevant to the task.
- Research artifacts belong in `research/`; raw experiment output belongs in a
  new `results/` subdirectory; runnable methods belong in `experiments/`.
- Every research artifact states status, question, evidence, method, findings,
  limitations, open questions, and next actions, as applicable.
- Cite repository evidence by path. Cite external literature with a resolvable
  primary source or authoritative publisher page, and distinguish it from a
  preprint or documentation.
- Keep this file short and stable. Put changing evidence in `RESEARCH_STATUS.md`
  or the relevant artifact, not here.

## Documentation authority

For current project truth, read documents in this order:

1. `AGENTS.md`
2. `research/RESEARCH_CONTEXT.md`
3. `research/RESEARCH_STATUS.md`
4. `research/CLAIM_EVIDENCE_MATRIX.md`
5. `IMPLEMENTATION_STATUS.md`
6. `RESULTS.md`
7. `ARCHITECTURE.md`
8. task-specific evidence retrieved on demand

Files under `research/evidence/` and `research/archive/` are **HISTORICAL**. Do
not treat them as current project truth unless the task explicitly requires
historical or methodological evidence, and do not recursively ingest either
directory. Numerical claims must still trace to
immutable result artifacts or their verified analyses. If canonical documentation
conflicts with an immutable measured artifact, the measured artifact wins for
that measurement; report the conflict rather than silently reconciling it.

## Repository navigation

Use CodeGraph first for structural questions (symbols, callers, impact, files).
Use targeted file reads for a known file or literal text. Do not load the full
repository merely for orientation.
