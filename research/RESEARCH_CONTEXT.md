# CSC shared research context

**Status:** Canonical current-state context after Cycle 5 closure (2026-10-06). Read this before research work, then read [RESEARCH_STATUS.md](RESEARCH_STATUS.md) and retrieve detailed evidence only when the task requires it.

## CSC in one paragraph

Counterfactual Shadow Continuum (CSC) is a local research prototype for collecting evidence about alternatives to a production decision. At each epoch the coordinator captures a canonical state anchor and a bounded exogenous-event window, commits one action in the authoritative production world, and runs non-actuating branches from the same declared inputs. The only implemented environment is the authored Junction J1 software traffic model. Production results are authoritative only in that environment. Mirror and alternative results are model estimates, not factual physical counterfactuals.

## Terms and boundaries

A **production** branch is the sole branch permitted to act on the authoritative software world. A **mirror** is a same-action shadow branch used to estimate model error. An **alternative** is a distinct non-actuating action branch. `K` is the number of distinct alternatives and excludes the mirror; traffic has three meaningful actions, so the measured domain supports K=0, 1, or 2. Shadows receive serialized anchors, declared actions, and event windows; they do not receive production authority. Local process boundaries and gateway tests are not hostile-code, operating-system, network, container, or cloud isolation.

The mirror utility gap is `epsilon`. Current-window epsilon, divergence, alternative utility, regret, and outcome comparison become available during or after the evaluated window. They are not established as pre-decision trust signals. Do not retune the Cycle 4 trust selector from these records.

## Current implementation state

The coordinator supports selectable synchronous and asynchronous local coordination. Synchronous mode retains a comparison barrier. Async mode commits production without waiting for shadow completion, tracks pending comparisons in a bounded hot ledger, applies expiry and duplicate handling, admits work with a fixed mirror-first policy, and finalizes ordered records. Coordinator polling, storage, and resource use still occur locally; logical decoupling is not resource non-interference.

Two local worker modes are implemented. **Cold** mode uses a fresh process per branch. **Warm** mode reuses a process after anchor hydration and checks the exact anchor identity, fresh per-assignment input buffers, deterministic RNG reset, declared metadata/environment integrity, and recycle limits. Tested contamination, malformed/stale/duplicate assignment, crash, timeout, and replacement paths destroy suspect workers. These gates cover the declared first-party deterministic model only. They do not prove safety for arbitrary adapters, retained globals, hostile code, or deployment workers.

Hot runtime records use bounded pending, completion, duplicate, and resource rings. Durable JSONL research evidence is append-only and intentionally grows with runs. Bounded record counts do not prove bounded process memory, physical executor queues, byte retention, storage capacity, or durable recovery.

## Evidence model and completed cycles

Early local smoke and validation series established deterministic replay, application-level actuation boundaries, and limited fault behavior. Confirmatory authored-reference studies did not establish alternative counterfactual validity. Cycle 3 decomposed failure modes without changing those immutable results. Cycle 4 found no qualified trust rule in its frozen development/calibration design; final held-out trust seeds were not generated. It also showed local async logical decoupling but poor evidence yield under delay.

**Trust remains Decision D:** current alternative-counterfactual validity is not established for policy use. **Learning remains BLOCKED:** `learning_enabled` is rejected, and no policy-learning experiment is authorized by existing evidence.

## Reproducibility and claim discipline

Every experiment series uses a unique result directory with manifests, source and
configuration hashes, seeds, workload identity, environment detail, and artifact
hashes. Deterministic replay and summary generation are evidence checks within
their stated scope; they do not prove physical behavior, security, timing, or
resource isolation. Existing `results/` directories are immutable. Never rewrite,
delete, or silently regenerate them. New performance work requires a fresh output
directory, fresh protocol identity, and a source boundary that makes comparison
honest.

Use claim labels precisely. “Implemented” describes code presence. “Locally
tested” describes a bounded local test or gate. “Measured” describes an immutable
experiment archive. “Deployment-validated” requires actual deployment evidence;
no such Cycle 5 claim exists. The design specification is a reference, not proof
that every aspirational capability is implemented or measured. The detailed claim
matrix keeps supported and unsupported claims separate.

Cycle 1/2 material established the prototype, local smoke harness, and early
reference-fidelity work. Cycle 3 is a read-only failure decomposition. Cycle 4
adds the frozen trust study and first async lifecycle experiment. Cycle 5 is the
completed local systems study and source-correction closure. Historical records
may preserve earlier terminology, timing series, or intermediate reviews; do not
mistake those records for current authority. Retrieve them only to answer a
historical or reproducibility question.

## Cycle 5: immutable measured archive versus current code

The immutable 86-run Cycle 5 performance archive is `results/cycle5-async/local-20261006-v1/`, collected with pre-correction source identity `9e473658ebd91e004e9caa9bb02971e95db98e22b76771bc45b7e9dd783b4cba`. It is the sole source for Cycle 5 cadence, evidence-yield, memory, resource, storage, and performance claims. Delivery audit verified all scheduled runs, factor coverage, hashes, and archived replay/summary checks.

In normal measured cells, cold K=1/K=2 had zero complete evidence; warm K=1 had complete fraction 1.000 and warm K=2 median 0.994. This is a narrow local normal-load improvement. Delay conditions had zero median complete coverage. Paired production/workload trajectory hashes matched within the measured seed units, but individual cadence outliers were substantial. The finite long probes capped named ledger/ring counts, yet all-online RSS and Python allocation slopes were positive. Process memory was not demonstrated bounded. Safe resource pressure did not establish resource non-interference. A transient CFR append fault stopped production after 1 of 12 planned epochs, so storage failure is not isolated to evidence. Fixed bounded admission records requested, admitted, and completed K, but loss of mirrors and delay-yield collapse mean general graceful degradation is not established.

After archive collection, source review found lifecycle, transport, validation, timing, analysis, and source-copy defects. They were repaired through separate v1-v5 correctness gates. The final v5 gate passed 108 tests in 28.362 seconds at `results/cycle5-validation/post-review-hardening-20261006-v5/`, source identity `c3e81bb6c4148f9b899970b5e71fe8a8b77226ba862ff3b7d1fd0f767cdda4be`. Its independent judgment found no CRITICAL, MAJOR, or MODERATE issue in that bounded scope and retained one MINOR integration-coverage limitation. This supports tested current-code behavior only; no corrected-source performance study was run. Historical seven-MAJOR findings belong to the pre-correction measured-source review and are not seven current-v5 blockers.

## Working pattern for future research tasks

Start with the authority hierarchy in `AGENTS.md`, then this context and the
status. Decide whether the task needs a current claim, an implementation detail,
or a historical measurement. For a current claim, consult the claim matrix and
result index. For implementation work, inspect the current code and implementation
status before reading historical reviews. For a numerical or methodological
question, retrieve the exact immutable result directory, source snapshot, protocol,
and verified analysis that produced it. Keep archive material scoped to the
question; do not use an old executive summary as a substitute for the current
state.

When documenting a new result, name its source identity, protocol/configuration,
seed/run unit, and limits. Keep production health, evidence health, and resource
measurements separate. A matched trajectory hash supports a local trajectory
check; it does not establish timing equivalence. A bounded ledger count supports
only that named count. A passing correctness gate supports its tested code path.
This discipline prevents later summaries from turning a local systems observation
into a validity, safety, or deployment claim.

## Where to retrieve evidence

Use the immutable result directory and its generated summaries for a numerical claim. The Cycle 5 executive summary is a concise closure decision; the results analysis contains distributions and limitations; the red-team record contains the historical measured-source review and final finding disposition. Warm-worker, retention, failure, timing, and loss-analysis documents answer their named questions. Do not merge quantities from different source identities or substitute a later test gate for a performance measurement. The claim matrix is the compact map from a statement to its evidence and remaining limitation.

Detailed material remains available because some experiment runners source-hash or regenerate it. Its presence beside current documents does not grant it current authority. Files under `research/archive/` are historical by policy. Result-source copies inside `results/` are immutable evidence snapshots, not editable working documentation. If a protocol, archive, and summary disagree, preserve the disagreement and report the exact artifact/source boundary rather than averaging or normalizing the records.

## Remaining systems questions and next gate

The next intended work is a separately preregistered controlled-host systems study, not an implementation task in this cycle. It must freshly measure production-path fault containment, physical queue and byte bounds, storage failure/recovery, hot RSS/Python trends, cadence tails, and requested/admitted/completed K under normal, delay, worker-capacity, and safe resource pressure. It should use fresh seeds, immutable output, declared 500-epoch conditions, and a separately declared 10,000-epoch continuous run. Do not claim real-time safety, resource isolation, hostile containment, physical validity, domain independence, bounded process memory, durable storage recovery, robust cadence, or delayed evidence yield without new evidence.

## Authority and evidence retrieval

Use [CLAIM_EVIDENCE_MATRIX.md](CLAIM_EVIDENCE_MATRIX.md) for claim status, [IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md) for code state, and [RESULTS.md](../RESULTS.md) for measured results. Detailed Cycle records are supporting evidence; archival material under `research/archive/` is historical and must be retrieved only for a task that needs it. Immutable result artifacts win if a current document conflicts with a measured number; report the conflict rather than silently reconciling it.
