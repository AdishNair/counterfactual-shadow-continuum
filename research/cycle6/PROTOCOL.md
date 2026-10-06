# Cycle 6 systems and cloud-edge validation protocol

**Status:** Frozen after the single preflight review and bounded correction,
2026-10-07. No Cycle 6 performance result has been collected. The exact tested
closure is recorded in `results/cycle6-gate/precollection-20261007-v1/manifest.json`.

## Question and fixed scientific boundary

Can the corrected CSC runtime sustain useful asynchronous counterfactual evidence
while preserving the authoritative production path under bounded local pressure,
long operation, worker failure, and evidence-storage failure, and can the same
source be evaluated in a policy-enforcing container/Kubernetes deployment when
infrastructure is available?

Cycle 5 is closed. Its 86-run archive and source identity remain historical
evidence only. The current v5 source has a 108-test correctness gate and no
corrected-source performance study. Trust remains Decision D; learning remains
BLOCKED. Cycle 6 will not alter trust, implement learning, claim physical traffic
validity, or interpret shadow outcomes as factual counterfactuals.

## Pre-collection implementation audit

The current source provides selectable async execution, cold and warm local
workers, bounded pending/completion/duplicate records, an owned bounded executor,
mirror-first admission, result validation before warm-worker reuse, finite
transport/shutdown handling, local RSS/CPU/handle/Python allocation sampling,
immutable run directories, and replay/provenance checks.

Two gaps block the declared measurements:

1. The executor measures physical item counts but not serialized bytes,
   per-queue high-water marks, or admission rejections. Cycle 6 will add direct
   item accounting and clearly labelled serialized-byte estimates without
   claiming Python object-resident memory measurement.
2. `PendingShadowLedger.finalize()` writes CFR/branch evidence synchronously.
   An evidence append error can still abort production. Cycle 6 will add a
   bounded evidence spool with explicit `PERSISTED`, `PENDING`, `FAILED`,
   `DROPPED`, and `UNAVAILABLE` accounting. Required production journals remain
   separate. No durable exactly-once claim is planned.

No broader runtime redesign is authorized. New code is limited to these two
gaps, their deterministic tests, Cycle 6 experiment orchestration, analysis,
verification, and safe deployment probes.

## Metric definitions

All distribution statistics use measured epochs after the declared warmup.
Independent run/seed is the replication unit; epochs within a run are repeated
observations.

### Production

- **Cadence:** milliseconds between consecutive production epoch starts. Report
  per run p50, p90, p95, p99, maximum, and count above the frozen 40 ms pacing
  target plus 10% scheduling tolerance (44 ms). The count is descriptive, not a
  hard real-time pass criterion.
- **Decision latency:** epoch start through authoritative actuation.
- **Trajectory integrity:** production semantic hash and workload hash within a
  paired seed, missing production epoch count, production errors, and unauthorized
  mutation count.

### Evidence

- `requested_k`: original number of distinct requested alternatives.
- `admitted_k`: alternatives admitted after mirror-first capacity allocation.
- `completed_k`: timely comparable alternatives accepted before the evidence
  deadline.
- Complete fraction uses the original requested mirror-plus-K set. Partial means
  at least one comparable nonproduction result without the complete requested
  set. Production-only means none.
- Report mirror and alternative availability, branch completion latency,
  evidence age, expiry, admission drops, execution failures, validation
  rejections, and persisted versus unavailable evidence records.
- Branch completion latency starts at production commit and ends when the
  coordinator accepts a terminal branch result. Comparison age starts at the
  same commit and ends when the comparison is finalized. Durable availability
  latency ends when the optional writer records persistence.
- The useful continuous-yield benchmark is at least 90% of all 9,500 post-warmup
  epochs having the requested mirror plus two distinct alternatives. Durable
  persistence is reported separately. Every scheduled measured epoch remains in
  both denominators; missing storage records cannot improve coverage. Report the
  full distribution whether the benchmark passes or fails.

### Resources

- Coordinator working-set RSS, worker RSS where available, Python current/peak
  allocation, process/worker count, Windows handles, and process CPU remain
  separate measures.
- Physical queue item count is measured directly under the executor lock.
  Physical queue/inflight bytes are the canonical serialized request byte lengths
  retained by queued/inflight assignments; they estimate payload representation,
  not interpreter object memory. Report current values, configured item/byte
  limits, high-water marks, and rejection counts.
- Also report pending epochs, retained completion/duplicate counts, worker-pool
  size, archive bytes, bytes written per epoch, and HTTP request/response bytes
  when applicable.
- Offline reduction memory is reported separately from online runtime memory.

### Failures

Record evidence-store failures, worker crashes/timeouts/kills, network failures,
stale or malformed results, queue saturation, cleanup uncertainty, spool status,
and production impact separately. No aggregate health score is defined.

## Gate A: controlled-host design

### Main paired factorial

- Fresh seeds: `26001`, `26002`, `26003`.
- 500 production epochs per run; first 50 are warmup.
- Pacing: 40 ms. Evidence deadline: 300 ms. Worker timeout: 2 s.
- Horizon: 6. Retained completion/duplicate history: 64. Pending-epoch limit:
  16. Normal physical task limit: 12. Normal workers: 3.
- Modes: K=0 production-only baseline with `mirror_count=0`; async warm K=1;
  async warm K=2. Evidence completeness is not applicable to K=0.
- K=0 conditions: normal, CPU, memory, storage pressure.
- Warm K=1/K=2 conditions: normal; one-time 120 ms per-assignment subdeadline
  delay; 400 ms overload delay; one-slot/one-task capacity; CPU; memory; storage
  pressure. The one-slot cell deliberately tests mirror-first admission, so it
  admits the mirror and no alternatives while occupied.
- Total: 18 cells x 3 paired run units = 54 runs. Condition order is shuffled
  deterministically within seed using fixed order seed `626001 + workload_seed`;
  the full registry is hashed before collection.

Pressure helpers are bounded: one CPU helper continuously evaluates integer
arithmetic until stopped; memory pressure allocates 128 MiB, touches every 4 KiB
page once, then touches one byte per page every 5 ms; storage pressure repeatedly
rewrites an 8 MiB file in the run scratch directory, flushes without fsync, and
waits 5 ms. Record helper CPU seconds, resident bytes, storage iterations, bytes
written, elapsed duty time, exit state, and cleanup. These conditions do not
represent host exhaustion or isolation. Paired contrasts are K=0 pressure minus
K=0 normal and each warm K/pressure cell minus the same K normal cell.

### Storage fault study

Fresh paired seeds `26101`-`26103`; 200 epochs, 20 warmup, async warm K=2. For
each seed run a no-fault control and four targeted optional-store cases: one
pre-append failure at write attempt 25; temporary unavailability for attempts
25-74 inclusive followed by recovery; sustained unavailability from attempt 25;
and one torn write at attempt 25 followed by truncation to the last valid newline
and retry. Thus this study has 5 cells x 3 seeds = 15 runs. The spool holds at
most 256 items and 16 MiB, tries each record at most three times with 10 ms
between attempts, and drains for at most 1 s at shutdown.

Required production/control streams are anchors, inputs, production journal,
resource, lifecycle, safety, environment, logs, manifest, and summary. Optional
evidence streams are CFR and branch metrics. The tested claim is logical
optional-evidence-sink isolation, not whole-disk isolation or exactly-once
delivery. Compare production/workload hashes, all 200 production epochs, spool
dispositions, queue/byte high-water marks, shutdown, and JSONL integrity.

### Continuous study

- Fresh seed `26201`; 10,000 consecutive production epochs; 500 warmup.
- Async warm K=2, 3 workers, 12 physical tasks, 16 pending epochs, 64 retained
  completions, 300 ms evidence deadline, 40 ms pacing, normal load.
- Sample resources every epoch; report start/end/min/max RSS, second-half
  Theil-Sen and ordinary least-squares slopes, Python current-allocation slopes,
  worker/process/handle trends, physical item/byte high-water marks, archive
  growth, evidence completeness, cadence distribution, and first-versus-last
  measured quartile summaries.
- Settle evidence for at most one evidence deadline, then perform bounded worker
  teardown. Exact offline reduction occurs after production and is measured
  separately.

For each memory series, OLS uses every second-half sample. Theil-Sen uses every
10th second-half sample, starting with the first, and reports bytes per epoch.
The practical equivalence regions are +/-104.8576 RSS bytes/epoch (1 MiB per
10,000 epochs) and +/-26.2144 Python-allocation bytes/epoch (0.25 MiB per 10,000
epochs). `supports a plateau at study resolution` requires both slopes inside
the relevant region and first-versus-last measured-quartile medians within 1 MiB
RSS or 0.25 MiB Python allocation. `positive trend remains` requires both slopes
above the upper bound; mixed cases are inconclusive. Finite survival never
establishes indefinite boundedness. Preflight requires 2 GiB free disk and 2 GiB
available memory; a watchdog stops collection before either falls below 1 GiB.
Offline reduction streams JSONL and retains fixed summaries plus the frozen
Theil-Sen subsample.

## Gate A integrity and decision

Gate A contains 54 main runs, 15 storage-fault runs, and one continuous run: 70
scheduled run identities. Every run must have a unique immutable directory, frozen source/config/protocol
hashes, fresh seed/workload identity, environment, completion/failure status, and
artifact hashes. The freeze closure includes every `csc/*.py` file; Cycle 6
runner, pressure, fault, analysis, and verification code; relevant tests and
gate logs; registry/configs; this protocol and its review; Dockerfile; and
deployment manifests. Collection executes the archived closure and checks its
identity before every run. A failed identity is never reused or replaced under
the same run ID. Verification checks registry coverage, duplicates, config and
source identity, artifact hashes, paired production/workload hashes, production
epoch coverage, replayable branches, and regenerated summaries.

Gate A stops only for invalid provenance, corrupted authority/trajectory,
unusable artifacts, or a source mismatch. Negative yield, cadence, memory, or
fault-isolation findings are retained and do not trigger reruns under the same
identity.

## Gate B: deployment design and current availability

Gate B uses the exact frozen Gate A source unless a separately recorded necessary
fix intervenes. Planned topology distinguishes coordinator/authoritative modules
from shadow-worker pods; emulated Kubernetes nodes are never called physical
machines. The deployment records image digest, manifests, namespace, runtime,
nodes, resource requests/limits, and raw artifacts.

When infrastructure exists, run the versioned tests in `GATE_B_REGISTRY.md` for
service-account/token absence,
actuation denial, NetworkPolicy ingress/egress, read-only root filesystem,
dropped capabilities, privilege escalation denial, host/device mounts, resource
limits, worker timeout/restart, worker/service/node loss where available, and
bounded CPU/memory/delay pressure. Each prohibited attempt records expected and
observed behavior. The image must be referenced by digest or every pod's runtime
`imageID` must match the recorded digest. A test lacking its enforcement
provider, runtime evidence, or safe workload is `NOT TESTED`; manifest inspection
alone never counts as a pass. gVisor is optional and reported separately.

Preflight on 2026-10-07 found the Docker Linux daemon unavailable, no kubectl
context, and no k3d, kind, K3s, or runsc executable. Reasonable checks and manifest
validation will continue, but absent a usable policy-enforcing cluster Gate B is
reported `UNEXECUTED/BLOCKED`; localhost results will not substitute for it.

## Analysis and claims

Report raw per-run metrics, medians/ranges/quantiles, and paired differences.
With three units, conclusions are descriptive; confidence intervals appear only
where their assumptions and purpose are justified. Preserve every completed,
failed, and anomalous run. Figures are generated deterministically from frozen
tables only when they answer a research question.

Supportable claims remain limited to the tested host/cluster, prototype, finite
duration, and exact fault/threat model. Cycle 6 cannot establish hard real-time
safety, universal or zero interference, indefinite memory boundedness, hostile
security beyond tested attacks, physical traffic validity, domain independence,
counterfactual truth, decision-time trust, learning benefit, production
readiness, arbitrary cloud portability, arbitrary K scaling, or formal safety.

## Finite governance and stopping rule

There is one protocol review and one final independent review. Only experiment-
blocking MAJOR or integrity-threatening CRITICAL preflight findings are fixed.
After final review, at most one bounded correction/gate is allowed; MODERATE and
MINOR findings are documented. Cycle 6 closes after Gate A, Gate B or its exact
blocker, deterministic verification, final review, and canonical updates. No
Cycle 6.x review chain or automatic next cycle is permitted.
