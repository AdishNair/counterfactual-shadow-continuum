# IEEE/Overleaf build guide

1. Open the official **IEEE Conference Template** on Overleaf.
2. Upload or replace `main.tex` with this package's `main.tex`.
3. Upload `references.bib`, `containment_results.tex`, `simulator_results.tex`,
   `execution_modes.tex`, `scenario_results.tex` and `seed_differences.tex`.
4. Upload the three referenced figures: `architecture.pdf`, `evidence_delay.pdf`
   and `simulator_reference.pdf`, under `figures/`. Include `ARTIFACTS.md` as companion material.
5. Compile with **pdfLaTeX**, then BibTeX, then pdfLaTeX twice (Overleaf normally
   performs these passes automatically).
6. Never modify IEEE margins, column widths, fonts, or title formatting.
7. Have the named authors verify their names, affiliations, emails and approval.
8. Adjust length only after the target venue and its final page limit are known.

## Current validation status

The revised article has 9 pages in IEEEtran conference format. Its ten sections
use descriptive E1/E2/E3 experiment names. One containment table retains initial
and revised outcomes. Three figures and seven tables are referenced. All original
result values and the numerical sequences of the three simulator tables are
preserved; the bibliography and its 24 citation keys are unchanged.

See `REVISION_NOTES.md`, `revision-numeric-diff.json` and `ARTIFACTS.md` for
verification, exact source/data locators, author decisions and the pinned build.
The tested compiler is portable Tectonic with its existing offline cache;
Overleaf/pdfLaTeX was not separately executed. Submission, venue approval and
authorship approval remain pending. The sections below retain prior experiment
and publication reproduction instructions; their earlier page counts are historical.

Do not suppress negative results to meet a page limit. Shorten background first,
then move provenance details to an appendix if the venue permits one.

## Prior simulator-experiment reproduction

Install `../o5/requirements.txt` into an isolated Python environment for SUMO.
The collection source, simulator hashes, six evaluation seeds and selected
development rate are pinned by `../o5/frozen-protocol.json`; the protocol document
is `../../operational/O5_SUMO_PROTOCOL.md`. Each command requires a new result
directory. Use the recorded source snapshot when reconstructing that identity.

`python -m experiments.sumo_o5 evaluate --protocol research/cycle7/o5/frozen-protocol.json --output results/NEW-EVALUATION`

Install `../o5/requirements-analysis.txt` in the analysis environment; recorded
versions are in `../o5/analysis-environment.json`. Then analyze:
`python -m experiments.sumo_o5_analyze --source results/NEW-EVALUATION --output results/NEW-ANALYSIS`.
`python -m experiments.sumo_o5_paper --analysis results/NEW-ANALYSIS` exports
checked tables and figures; it refuses to overwrite changed existing paper
assets. Run an export in a fresh source copy or compare against existing assets.
`../o5/paper-export.json` records the actual checked analysis and output hashes.

The evaluation is a completed one-window independent-simulator study, not a
physical validity or policy-promotion gate. It retains a condition where
persistence beats calibrated predictions and an async cohort without lower mean
commit latency. The target venue remains unspecified; the current identified 10-page draft is
not a conference-ready submission. See the O6 venue-readiness record before
choosing a category, anonymization policy or AI-content policy.

## Reproduce the pinned offline PDF build

The final PDF is `main.pdf`. Use `build.py` with the portable Windows x86_64
Tectonic release pinned in `build-engine.json`; it verifies the executable hash,
uses cached resources only, disables unsafe TeX features, preserves inputs/logs,
and refuses output-directory reuse. It runs normal BibTeX/reference passes.
No full system-wide TeX installation or Kubernetes change is needed.

```powershell
python research/cycle7/paper/build.py --engine C:/PATH/tectonic.exe --output results/NEW-PAPER-BUILD
```

The O6 private artifact package includes the exact resource-cache snapshot,
checksums and restoration instructions. On an environment with no such cache,
provision that snapshot first; offline mode intentionally fails rather than
silently downloading a different bundle. The package also includes frozen O5
source, audit/analysis scripts, protocol/seeds, raw-evidence locators and final
build/visual checks. No DOI, external artifact availability or author approval
is asserted. Data are not publicly uploaded.

O6 provenance: `results/o6-publication-20261111T140316-29ee0cef/` from the
repository root. `scientific-audit.json` independently recomputes raw queue
metrics and clarifies 56/72 distinct action sets (112/144 policy labels).
`figure-embedding.json` records the font-only O5 re-export using its frozen
plotting function with `pdf.fonttype=42`, without editing the original analysis.
`final-pdf-check.json`, `visual-inspection.json` and `venue-readiness.json`
record the actual final checks and remaining submission gates.

DSN 2027 requires double-blind anonymization and a declared paper category;
its tool limit is 7 pages and regular limit 11, excluding references. ITSC 2027
prohibits substantive LLM-generated manuscripts; the current draft must not be
misrepresented as grammar-only assistance. The named authors must approve
scientific content, citations, originality, authorship and the truthful AI Tool
Usage disclosure before any submission. Generic IEEE formatting is not acceptance,
PDF eXpress certification, physical validity or TRL 7.

## Gate B follow-up extension

The current canonical draft includes the separate Redis/NATS follow-up, its new
architecture figure `figures/fig1_architecture_gateb.pdf`, and
`table_gateb_followup.tex`. The original Gate B matrix/figure remain historical
outcomes. Evidence, source freeze, row protocol, image/delivery identity,
authorization logs, bounded resource failures, and the Humanize editorial
record are in `results/gateb-followup-20261111T094758Z-5d8f70e4/`.
The tested final build is `paper-final/` there. That preceding draft had 12 pages; the current revision has 9 pages, and
conference-specific page limits and author/AI/anonymity approval remain pending.
No submission or upload was performed.

To reproduce derived results without redeployment:
`python -m experiments.gate_b_followup_analyze --source results/gateb-followup-20261111T094758Z-5d8f70e4 --output results/NEW-FOLLOWUP-ANALYSIS`.
The later figure-padding correction is identified by `figure-layout-v2/`.
For a separately authorized new deployment, verify/import the exact image pins,
then use `python -m experiments.gate_b_followup --output results/NEW-FOLLOWUP`.
It refuses existing namespaces/output directories, generates ephemeral Secrets,
and deletes only its disposable namespaces. The memory probe is separately
bounded and remains scientifically inconclusive. Never rerun merely to change
a negative classification. Existing O5 reproduction and venue restrictions above
remain applicable.
