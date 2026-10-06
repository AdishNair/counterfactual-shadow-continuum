# Independent red-team review of CSC evidence

**Status:** Skeptical source-and-artifact review, 2026-09-28. No experiment was
run and no result artifact was modified.

## Question

Do the implementation, tests, and recorded artifacts support the research
claims currently made for the Counterfactual Shadow Continuum (CSC) prototype?

## Method and scope

I read the applicable repository and research instructions, the current
research reviews, the matrix/validation indexes and reports, selected raw-run
manifests, and the implementation paths for execution, comparison, replay,
state synchronization, and actuation. I also read the unit/integration tests.
This is an independent repository review, not a security penetration test,
literature review, physical-traffic validation, or reanalysis of all JSONL
records. It treats the raw immutable run directories as stronger evidence than
derived prose or replaceable aggregate indexes.

## Overall assessment

The narrow implementation claim is credible: a deterministic J1 software
harness creates one production branch and local non-actuating first-party shadow
processes, stores branch records, and can replay recorded trajectories under the
currently installed code. The repository is unusually explicit that this is not
hostile-code containment, physical traffic, real-time non-interference, causal
counterfactual validation, learning evidence, or a novelty result.

However, no evidence currently validates the decision-relevant quantity that a
shadow's alternative-action estimate is accurate. In addition, result-selection
and replay-versioning weaknesses mean that timing and reproducibility claims
need tighter provenance before they are used outside the local prototype report.

## CRITICAL

### C1 - Alternative-action estimates have no independent ground truth

**Evidence.** `csc/compare.py` computes `epsilon` only from the production
action and the first same-action mirror. It then discounts a shadow's estimated
improvement by that number. `csc/world.py` intentionally uses a different
transition model for production and shadows. The matrix holds production fixed
across K, so it cannot reveal the outcome that would have followed an
alternative action. `research/evidence/cycle1/counterfactual_validity.md` correctly describes
this limitation, and `research/RESEARCH_STATUS.md` leaves RQ4 open.

**Why this is critical.** A small error at `(state, production action, window)`
does not bound error, sign, or ranking at `(state, alternative action, window)`.
The alternative can enter a different phase, queue regime, or incident regime.
Therefore a positive discounted regret is not evidence that production would
have improved under that action; it is only a model output. This blocks any
effectiveness, policy-selection, calibrated-uncertainty, or causal claim.

**Alternative explanation.** Mirror epsilon may be empirically useful as a
conservative screening feature in this toy environment. The present evidence
does not distinguish that possibility from an uninformative or anti-calibrated
gate.

**Resolution required.** Add a separately maintained reference environment
which does not import `ShadowWorldModel`. From each saved anchor, execute every
action in that reference under common exogenous random numbers. On held-out
seeds, report signed/absolute error, action ranking accuracy, regret-sign
accuracy, and coverage of the `improvement > epsilon` gate, stratified by action,
horizon, demand, and incident regime. Include constructed cases with low mirror
error but high alternative error. Keep claims at "estimated" until those
predeclared criteria pass.

## MAJOR

### M1 - Aggregate result provenance is ambiguous and stale figures remain prominent

**Evidence.** `results/matrix/` contains two complete K=0/1/2 series (30 raw
run directories), while `results/matrix/matrix-summary.json` indexes only one
15-run series and `results/matrix/REPORT.md` reports 1.6169, 135.1413, and
145.6411 ms. `RESULTS.md`, `research/RESEARCH_CONTEXT.md`, and
`research/RESEARCH_STATUS.md` instead report 4.3614, 169.3680, and 189.9336
ms. `research/evidence/cycle1/results_analysis.md` identifies this discrepancy but does not
resolve it. The same pattern exists in `results/validation/`: paired directory
sets exist, and `validation-summary.json` indexes only one set while
`research/evidence/cycle1/counterfactual_validity.md` cites the other set for several controls.
`experiments/runner.py` and `experiments/validation.py` write their aggregate
JSON files directly at a reusable output root.

**Why this matters.** The raw run directories may be intact, but a reader can
choose incompatible timing figures without a canonical series identifier.
Replacing an aggregate index/report in a reused results root also conflicts with
the repository's immutable-evidence convention. This prevents a reviewer from
knowing which results are current or from reproducing the headline calculation
without reconstructing provenance manually.

**Alternative explanation.** The two series may be legitimate repeated smoke
runs under different instrumentation or host conditions. That would be useful
evidence if recorded as two named series, rather than an error.

**Resolution required.** Freeze both existing series under unique, immutable
series directories with a series manifest that lists member run IDs, generation
command, source/config hashes, timestamp range, and the exact derived report
hash. Update high-level documents to name one canonical series and move the
other to a clearly labelled replication or superseded-series note without
deleting it. Change matrix/validation runners to refuse an existing aggregate
destination or to create a fresh unique series directory by default.

### M2 - Replay verifies files but does not enforce the recorded software version

**Evidence.** `csc/store.py` records per-file `source_hashes`, but
`experiments/replay.py` verifies only `manifest["artifact_hashes"]` and then
imports the current `csc` implementation to reconstruct trajectories. No test
checks that the executing source matches the manifest hashes. The present
`results/measured-source/csc/` happens to match selected current transition
files, but this is an incidental snapshot, not a replay precondition.

**Why this matters.** A later model change can make a historical replay fail for
an unhelpful reason, or can preserve a limited trace while silently changing
unexercised behavior. "Artifact integrity VERIFIED" is sound for stored file
bytes, but it is not a complete claim of historical executable reproducibility.

**Alternative explanation.** Source hashes and the archived source copy allow a
careful reviewer to perform a manual check today. The issue is that this check
is not automated or required by replay.

**Resolution required.** Before replay, hash the active package and fail closed
on a transition-relevant mismatch. Prefer an immutable per-series source bundle
or container digest and launch replay from that bundle. Separate and report
`artifact_integrity`, `source_identity`, and `trajectory_replay` statuses; add a
test that a one-byte transition-source change causes a source-identity failure.

### M3 - The K timing result is dominated by a sequential, cold-process barrier

**Evidence.** `csc/runner.py` launches fresh local subprocesses each epoch and
waits in `manager.collect` before the following logical epoch. Matrix execution
in `experiments/runner.py` always orders each seed K=0, K=1, K=2. The indexed
report attributes almost all K=1/K=2 time to `barrier_ms`; worker CPU is commonly
zero at Windows clock resolution and worker RSS is null. The repository warns
about the barrier, but `RESEARCH_CONTEXT.md` and `RESEARCH_STATUS.md` still
present point timing figures that are vulnerable to warm-up, order, antivirus,
and host-load effects.

**Why this matters.** The measurements support overhead of this exact
spawn-and-wait harness, not a general relationship between K and CSC runtime
cost, production continuity, CPU consumption, or a warmed remote design.

**Alternative explanation.** Fresh-process creation may be a deliberate
conservative isolation cost. If so, report it as that specific configuration's
end-to-end cost rather than as CSC scaling.

**Resolution required.** Predeclare a randomized/counterbalanced K order across
independent repetitions, record wall time and child CPU/RSS with a suitable OS
collector, and compare cold local, warmed worker, and asynchronous production
modes. Report per-run paired effects and uncertainty. Do not characterize the
local barrier result as real-time or deployment performance.

### M4 - Non-actuation is only an application-level property of trusted code

**Evidence.** `csc/safety.py` gates `ProductionWorld.apply_plan` behind an
in-memory object capability and HMAC issuer. `csc/branches.py` serializes only
data to a worker and launches it with a reduced environment, but local workers
remain processes of the same user. The tests in `tests/test_core.py` test forged
tokens and direct world mutation, not filesystem, process-memory, network,
credential, or device attacks. The audit counter in `csc/runner.py` observes
only `world.audit`. The implementation and research status accurately disclaim
hostile-code and cluster validation.

**Why this matters.** "Zero unexpected authoritative commands" establishes only
that the trusted harness called its own gateway as intended. It does not show
that a malicious or compromised worker could not bypass the model process and
actuate a real external target. This must remain outside any security or
containment claim.

**Alternative explanation.** The intended research target may be a cooperative
first-party SEM, for which application-level separation is sufficient. The
threat model needs to say so explicitly.

**Resolution required.** Specify attacker capabilities and the trusted actuator
boundary. For hostile-code claims, deploy the supplied policy-enforcing
environment and run adversarial filesystem, egress, credential, process, and
device tests with independently collected actuator-side logs. Preserve a
separate local-cooperative result category if cluster validation is unavailable.

## MODERATE

### O1 - Validation fault coverage is narrower than the scenario names suggest

`BranchManager.launch` injects a requested fault only into the final SHADOW
branch at the configured epoch. `resource_budget` removes planned non-production
branches and `capture` truncates to production before launch. Thus preserved
production hashes establish logical independence under these controlled harness
paths, but not a crashing mirror, coordinator, gateway, worker pool exhaustion,
or real resource starvation. Resolve by recording the injected target in each
scenario and adding tests that fault every role and coordinator-side stage.

### O2 - `complete_fraction` is semantically misleading for K=0

`OutcomeComparisonEngine.compare` labels a production-only record
`PRODUCTION_ONLY`, while `summarize` defines completeness as equality to
`COMPLETE`. Every K=0 run therefore reports `complete_fraction: 0.0` despite no
missing branch. This is not a data-loss finding. Replace it with separately
named production validity and expected-branch completion measures, or define the
baseline expected state explicitly.

### O3 - Future-window availability and exogeneity are assumed by construction

`csc/runner.py` materializes the full horizon before production steps and sends
the same batch to all branches. `csc/sync.py` can validate supplied ordering and
membership, but cannot establish source authenticity, live availability, or
action independence. This is appropriate for a controlled offline-window model;
it is insufficient for a live control assertion. Resolve with input provenance,
availability-delay measurements, an action-dependence inventory, and abstention
when a required future window is unavailable.

### O4 - Some positive controls are implementation checks, not fidelity evidence

The exact-control and biased-SEM scenarios change relationships between two
authored models. They show the diagnostic can reach zero and respond to a chosen
mismatch. They do not independently validate model fidelity or establish a
mirror-to-alternative relationship. Relabel them consistently as positive
implementation controls and pair them with the C1 reference experiment.

## MINOR

### N1 - First-mirror selection and EWMA fallback need clearer interpretation

`OutcomeComparisonEngine` uses the first accepted mirror for epsilon and carries
an EWMA after a missing mirror. A second mirror can reveal deterministic
agreement but is not incorporated in uncertainty, and the EWMA is not
conditioned on state/action/horizon. This is acceptable for an exploratory
diagnostic; publish its source explicitly for every record and avoid calling it
current calibration.

### N2 - Text encoding and cross-document paths reduce reviewability

Several research files display mojibake in headings, and the validation review
cites run IDs outside the current validation index without explaining their
series membership. Normalize UTF-8 text and cite a series manifest plus raw run
ID wherever a measurement is reported.

## Evidence that survived this review

- Branch identity, anchor/window checks, virtual-actuation records, and gateway
  role/epoch/action checks are implemented in `csc/branches.py`, `csc/sync.py`,
  and `csc/safety.py`.
- The test suite covers deterministic shadows, invalid windows, local fault
  isolation, gateway misuse, artifact tamper detection, and localhost HTTP
  behavior (`tests/`). It does not establish the broader claims listed above.
- The indexed matrix artifacts record matching production/workload hashes across
  K for each listed seed and zero mismatches in their current replay report
  (`results/matrix/matrix-summary.json`, `results/matrix/replay-verification.json`).
  This supports deterministic local reconstruction for that selected series.

## Priority actions

1. Resolve M1 before reusing any timing figure in a presentation, paper, or
   decision.
2. Run the C1 independent-reference, all-actions protocol before interpreting
   discounted regret as decision evidence.
3. Enforce M2 source identity in replay and retain immutable series bundles.
4. Choose whether the threat model is cooperative-first-party or hostile-code;
   execute M4's deployment test only for the latter claim.

## Limitations and open questions

This review did not recompute every statistic, execute an adversarial worker,
or validate external sources. It found no evidence of fabricated results. The
largest issues are limits of inference and provenance organization, not a claim
that the stored raw run data were altered. The next review should inspect the
new series manifests and the held-out alternative-ground-truth results once they
exist.
