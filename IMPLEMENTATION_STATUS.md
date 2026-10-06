# Implementation status

Latest current-tree verification: **108 tests passed in 28.362 seconds** at
`results/cycle5-validation/post-review-hardening-20261006-v5/`. The prior
post-review variant passed **80 tests in 30.089 seconds** after
post-measurement transport/queue/quarantine corrections at
`results/cycle5-validation/post-review-hardening-20261006-v1/`. Corrected-source
performance is unmeasured. Independent reviews drove source-bound v2 through v5
corrections for physical queues, transport, quarantine, lifecycle, numeric,
campaign-disposition and source-copy defects. Final v5 review found no material
remaining issue in that bounded scope and one MINOR test-coverage limitation.
Measured-source
verification: **66 tests passed in 141.372 seconds** against final
Cycle 5 v2 source; `results/cycle5-gate/runtime-20261006-v2/` records source
identity. The separate 12-case local fault campaign passed its declared behavior
checks at `results/cycle5-validation/faults-20261006T135732Z-3827f22a`, including
a negative availability result: one transient CFR write failure aborted production
after 1 of 12 planned epochs. Historical Cycle 4 verification remains 54 tests.
Historical matrix evidence remains 15 paired runs,
1,500 epochs and 4,000 replayed trajectories with zero mismatches.
See [measured results](RESULTS.md) for artifacts and interpretation.

## Evidence boundary

The immutable Cycle 5 performance archive is
`results/cycle5-async/local-20261006-v1/`, collected with source identity
`9e473658ebd91e004e9caa9bb02971e95db98e22b76771bc45b7e9dd783b4cba`.
All Cycle 5 performance, cadence, resource, memory, storage, and evidence-yield
claims refer to that measured source. Review defects discovered after collection
and their v1-v5 repairs must not be projected backward onto the archive.

The current v5 source is correctness-gated only: its 108-test gate validates the
named lifecycle, transport, validation, timing, cleanup, analysis, and source-copy
paths. It has no corrected-source performance measurement. The historical review's
seven MAJOR findings are measured-source findings, not seven current-v5 blockers.
The final v5 closure found no CRITICAL or MAJOR blocker for a separately
preregistered future study; it retained one MINOR integration-coverage limit.

## Implemented and locally tested

- P0: deterministic workloads, explicit state/events/identity, separate branch state,
  actuator/virtual-actuator boundaries, structured artifacts, replay and integrity checks.
- P1: capture, scheduler, branch manager, production world, shadow world, input
  synchronization, utility/comparison/regret, mirror calibration, knowledge store, cleanup.
- Baseline K=0 and K=1/K=2 configuration; fixed/queue/predictive policies.
- Fault injection: process crash, timeout, model error, missing/duplicate/reordered/
  delayed events, simulated slot pressure, simulated capture failure.
- Same-action mirror determinism, deliberately biased model checks, unavailable
  fidelity semantics and exclusion of incomplete comparisons.
- P2 slice: HTTP remote workers, subprocess deadlines, bounded request sizes and
  worker slots, health/readiness/Prometheus endpoint. Localhost integration tested.
- Experiment matrix, fidelity/failure/ablation runner, raw JSONL, source/config/
  workload/artifact hashes, replay verification and generated report.
- Cycle 4 selectable asynchronous coordinator: bounded pending work, production
  journal, epoch/input/anchor joins, expiry, drops, duplicate rejection,
  single-writer artifacts and comparison finalization in epoch order. Default
  synchronous deterministic mode remains selectable. Local tests cover faults,
  stale delivery, shutdown and new-run restart; durable recovery is absent.
- Separately written authored-software reference, bidirectional mutation tests,
  feature firewall and frozen trust-selector driver/analysis. Development and
  calibration executed; no candidate qualified, so final held-out was not generated.
  Decision-time online trust and learning remain unestablished.
- Local async 162-run experiment, source archives and deterministic verification:
  3,964 successful branches replayed; raw summaries matched. Cadence decoupled
  under tested delays, with poor evidence yield. Subsequent numeric-overflow
  rejection is locally tested but absent from measured source snapshots.
- Cycle 5 optional local warm subprocess pool alongside cold fresh workers;
  fresh per-assignment state/model/input/actuator objects, exact anchor checks,
  RNG reset, declared bounded metadata, environment/input integrity checks,
  destruction on tested reset/assignment/transport failures, and configurable recycling.
  Cold/warm deterministic agreement and contamination/replacement tests passed
  for first-party models; this is not hostile-code containment.
- Mirror-first bounded branch admission and requested/admitted/completed K
  accounting. Complete evidence requires the originally requested mirror and
  distinct alternatives rather than just the admitted subset.
- Bounded hot completion/duplicate/resource rings, monotonic commit watermark,
  and current-worker lifecycle counters. Physical executor queues are not directly
  measured by these ledger caps. Durable research evidence grows with
  epoch count; exact offline summaries reread the finite archive.
- Windows current working-set RSS, process CPU and handle sampling, distinct
  from Python allocations and peak RSS; unavailable/quantized samples retain
  measurement limits.
- Cycle 5 preregistered 84-run pilot plus 3,000/1,000-epoch continuous probes
  completed: 86 verified runs and 41,686 replayed accepted branches, zero missing
  production epochs/errors/observed unauthorized mutations, and paired production/
  workload hashes matching within every main seed. Independent final review complete. See
  `research/evidence/cycle5/cycle5_protocol.md`, `research/evidence/cycle5/warm_worker_correctness.md`,
  `research/evidence/cycle5/runtime_retention_design.md`, and `research/evidence/cycle5/cycle5_failure_recovery.md`.
- Normal-load cold K=1/K=2 produced zero complete comparisons in every main run;
  warm K=1 produced fraction 1.000 and warm K=2 median 0.994 (range 0.989–0.994).
  Warm moderate/severe-delay median completeness was zero. This supports a
  narrow measured yield improvement, not universal continuous-service success.
- Hot count caps held during 3,000/1,000-epoch runs. Working-set RSS and Python
  current allocations retained positive late-run slopes; a memory plateau and
  indefinite bounded memory were not demonstrated. Archives grew to about
  125/15 MiB. Cadence had substantial individual-run degradation despite many
  condition medians near 40 ms; shared-resource non-interference is not established.
- All-online long-run second-half RSS slopes are +339.915/+265.009 bytes per
  epoch and Python current allocation slopes +23.340/+191.497 bytes per epoch.
  These all-online estimates differ from frozen warmup-excluded tables.
  Post-production exact summary sampled working set after reduction reached
  512,155,648 bytes (488.430 MiB); this is not an independently sampled RSS peak.
  offline memory is separate from continuously retained ledger/ring state.
- Immutable future-series directories and source-identity replay checks; a local
  all-actions reference-fidelity smoke runner that replays `ProductionWorld`
  without importing the SEM. Its eight-run output is preliminary research evidence,
  not external validation.

## Implemented but not deployment-validated

- Docker image recipe, K3s worker Deployment/Service and coordinator Job/PVC.
- NetworkPolicy with deny-all shadow egress and coordinator-only ingress.
- Resource limits, read-only rootfs, dropped capabilities, no mounted credentials.
- Optional gVisor placement patch.
- CI workflow for Linux/Windows and Python 3.11/3.14. Only the local Python 3.14
  Windows test execution has been observed here; remote CI has not run.

## Simplified

- Python control plane rather than Go; canonical JSON rather than CBOR.
- One two-approach junction and three plans, rather than eight lanes/six actions.
- Independent fluid traffic models with deterministic per-tick heterogeneity in
  production; no individual vehicle identities or physical validation.
- Batch event fan-out over process pipes/HTTP rather than NATS live streams.
- In-memory epoch interlock and local HMAC issuer rather than Redis/Ed25519.
- Selectable fresh or reusable local subprocesses rather than a
  deployment-validated reusable pod hydration pool.
- Synchronous accelerated epochs retain a comparison barrier. Async paced local
  epochs avoid shadow-completion waits, but still perform coordinator storage,
  comparison and polling work. Resource non-interference is not established.
- Configured worker-slot ceiling; resource-pressure injection reduces that ceiling.
  This is not measured adaptive CPU/memory scheduling or actual cgroup exhaustion.
- Snapshot size bound; no enforced capture-time budget/fallback for arbitrary
  exceptions. A capture fault injection exercises the branch-skip path only.

## Deferred / not established

The independent [Cycle 5 review](research/evidence/cycle5/cycle5_red_team_review.md) reported
**no CRITICAL findings and seven MAJOR findings for the pre-correction measured source**: evidence persistence can
abort production, transport/shutdown can block, physical cancellation queues are
not bounded by ledger metrics, invalid result validation occurs after worker
return, memory trends remain positive, cadence is heterogeneous, and delay
coverage collapses. It also retains eight moderate/minor findings; only the
narrow OS-metrics-cache hypothesis was closed by its diagnostic. These historical
findings remain essential limitations of the archive; they are not a statement
that v5 has seven unresolved implementation blockers.

Cycle 5 post-measurement corrections addressed physical cancellation-queue accounting, warm-result validation before reuse, pipe/shutdown blocking, lease and cold-capacity ownership, derived numeric validation, cleanup disposition, analysis failure treatment, and source-copy compatibility. The final current source passed the v5 108-test gate in 28.362 seconds at `results/cycle5-validation/post-review-hardening-20261006-v5/`. Independent v5 judgment found no CRITICAL, MAJOR, or MODERATE defect within this bounded correction scope; one MINOR integration-coverage limitation remains. This is local current-code correctness evidence only. It neither alters the immutable 86-run archive nor supplies corrected-source performance measurements.

Successive independent reviews reproduced and corrected the stranded warm lease,
unresolved cold capacity, derived arithmetic, consumed timing, cleanup-analysis
and copied-source compatibility paths. Final v5 passed **108 tests in 28.362
seconds** at `results/cycle5-validation/post-review-hardening-20261006-v5/`.
Independent v5 review found no remaining CRITICAL, MAJOR or MODERATE issue in its
bounded correction scope and retained one MINOR nonblocking integration-test
limitation. V5 is locally adequate only as the correctness-gated basis for a
separately preregistered finite systems study; it has no new performance evidence.
These were source-established paths, not observed 86-run failures.
See `research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening.md` and the separate eight-test mocked
campaign cleanup checks in `research/archive/cycle5/post_collection_hardening/cycle5_post_review_campaign_hardening.md`.
The measured main archive remains immutable. No new-source cadence, memory or
efficiency result is claimed. R1 storage, R5 memory, R6 cadence and R7 delayed
yield remain open for the measured source.

- Full A1–A14 hostile-container containment, gVisor validation, cgroup stress,
  network partition testing and three-node measurements.
- Full-duration continuous production validation, durable epoch restart/recovery,
  independent comparator restart and a production fallback on service loss.
- NATS/Redis service transport/storage and Go service decomposition.
- Adaptive learning, policy promotion/audits/canary/rollback. `learning_enabled=true`
  is rejected explicitly, rather than silently doing nothing. RQ6 remains unanswered.
- Pruning, learned/adaptive resource scheduling, kernel snapshots, eBPF,
  Firecracker and additional domains. Fixed mirror-first admission can lower
  admitted K; it is not learned scheduling.
- Full E1–E8 paper protocol, 5,000-epoch determinism gate and learning effectiveness.
- Complete Prometheus catalogue and Grafana dashboards; current exporter is a subset.

## Environment blockers observed

- `docker info`: Linux Docker daemon named pipe unavailable.
- `kubectl config current-context`: no context configured.
- Go executable unavailable.

These block actual cluster validation, not local implementation or experiments.
