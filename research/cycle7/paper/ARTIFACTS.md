# Artifact and reproducibility index

This companion index contains implementation and archive identifiers deliberately
excluded from the article body. Paths below are relative to the repository root.
Archives are private local evidence; no public artifact DOI or availability claim
is made. These are separate experiments and source versions, not one pooled dataset.

| Article experiment | Immutable evidence and reproducibility records |
|---|---|
| E1: runtime evidence yield and fault isolation | `results/cycle6-gate-a/local-20261007-v3/`: pre-registration, per-run configuration, exact source snapshot, records and manifests. Existing verified summaries: `research/cycle6/tables/gate_a_synthesis.json`, `gate_a_verification.json`, `gate_a_verification_replay.json`, and `gate_a_analysis/cycle6_runs.json`. The archived source includes its protocol and reproduction workflow. |
| E2: initial containment | `results/cycle6-gate-b/local-20261007T002415Z/gate_b_evidence.json`; execution identity `5c4e9bd2d853d189f5450f5e539bd0cb613fae6c842f543899e4a7d52fcb82b0`. Initial image: `csc-gateb-registry:5000/csc-prototype@sha256:8a48256c33842166295a8cc43aafeadcb806d775083ecc42365ade4ef5bab9f1`. |
| E2: extended authorization and resource tests | `results/gateb-followup-20261111T094758Z-5d8f70e4/`: `attempt-01/source/`, source/configuration/protocol manifests, raw observations and broker logs; `memory-01/` preserves the separate failed memory-observer test. Final dispositions: `analysis-01/verified-results.json`. Application image digest: `sha256:8a988b3d505bd266ffff771338dc0512d2fc6b382b3d94d00fe431d68f230d54`; Redis/NATS digests and per-node checks are in `prerequisites/images.json` and `delivery.json`. |
| E2: infrastructure service pilot | `results/o4-prerequisites-20261111T123223-abdc904b/`: deployment observations, source, request records, two dispositions, image delivery, network controls, cleanup and hashes. Successful pilot: `attempt-02/`; verified findings: `derived-v2/o4-verification.json`. Image digest: `sha256:89e730490850154832e4879f0b482f73f591fdf46fddb9d006b8a01944d35d1b`. |
| E3: independent-simulator evaluation | `results/o5-sumo-evaluation-20261111T132947-f9fb82ac/`: exact source, protocol, configuration, seed registry, raw traces and manifests. Archived analysis: `results/o5-sumo-analysis-20261111T134030-32c9aaf7/`. Protocol/source pins: `research/cycle7/o5/frozen-protocol.json`. Protocol checksum: `32b778e06444708eb6abcda9039a290b87fbba2e318bafaf221c2ee0af2662d1`; raw manifest checksum: `0f0541d4fa413256a160a0424e56325c9803d5d7bf20e583c2d7153c79c67d32`. |

The source base was `b3d2a390590069d2528f1ad8329582c094c98bb4` with uncommitted
files; the archived exact-byte snapshots and checksums, rather than that commit
alone, identify the implementations that produced the observations. Simulator
and client versions, seed definitions, network/scenario files and software
environment records are preserved with each experiment. Worker credentials are
excluded; credential policy and authorization observations are retained.

## Reproduce summaries and the article

The existing analysis entry points operate on immutable archives and require new
output directories. They are listed here for reproduction, not executed by this
editorial revision:

```powershell
python -m experiments.sumo_o5_analyze --source results/o5-sumo-evaluation-20261111T132947-f9fb82ac --output results/NEW-SIMULATOR-ANALYSIS
python -m experiments.gate_b_followup_analyze --source results/gateb-followup-20261111T094758Z-5d8f70e4 --output results/NEW-CONTAINMENT-ANALYSIS
```

Use the corresponding archived source snapshots for exact method reproduction;
current experiment files may differ. The existing E1 verification and synthesis
records identify the archived methods and their input hashes. Reproduction of
the deployment itself also requires the exact node-preloaded images and the
declared Kubernetes environment; ordinary local tests are not substitutes.

The article builds with `build.py`, the compiler digest in `build-engine.json`,
and the existing Tectonic resource cache. The earlier publication artifact
package under `results/o6-publication-20261111T140316-29ee0cef/` preserves that
cache and dependency instructions. A system-wide TeX installation is unnecessary.

```powershell
python research/cycle7/paper/build.py --engine C:/PATH/tectonic.exe --output results/NEW-MANUSCRIPT-BUILD
```

`render_delay.py` only changes layout of the exported delay plot from
`research/cycle7/figure_data.json`. All plotted coordinates and label precision
are preserved. The architecture and simulator figures are byte-identical copies
of the existing assets under descriptive names; the redundant yield, lifecycle
and containment-status figures are excluded from the revised article.

The original manuscript and editorial verification are preserved at
`results/manuscript-revision-20261111T104622Z-1ab3980b/`. See
`REVISION_NOTES.md` and `revision-numeric-diff.json` for numerical accounting,
author decisions and verification scope. No experiment was rerun, result data
regenerated or experiment code modified during this revision.
