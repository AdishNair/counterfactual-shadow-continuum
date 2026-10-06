# Cycle 4 local async outcome

**Status:** Implemented and locally evaluated, 2026-10-05. No deployment or
resource-isolation validation. Trust conclusions are scientifically separate.

## Question, implementation and evidence

Does production advance while earlier shadow work remains unfinished, and how
does local cadence respond to injected shadow delay? `csc/pending.py` owns a bounded
pending ledger; `csc/async_runner.py` journals production before dispatch, admits
whole batches without waiting for capacity, polls settled futures and finalizes
comparisons in epoch order. Expired running tasks keep permits until actual
settlement. Identity includes experiment/site, epoch, branch, anchor, action and
input window/hash. Late/duplicate/rejected output cannot actuate or resurrect
evidence. Synchronous remains the default selectable path.

`research/evidence/cycle4/async_state_machine_audit.md` and its machine transition summary cover
64 state pairs, fault, shutdown/new-run restart, duplicates, stale delivery,
single writer, expiry, ordering and mutation checks. The current full suite
passes 54 tests. The immutable experiment source and its test snapshot are the
measured source of record; subsequent current-tree hardening is separately tested.

`results/cycle4-async/local-20261005-v1` contains one preregistered 162-run series:
150 primary runs (five modes, six conditions, five paired seeds 901–905) and
12 microstudy runs (three seeds 906–908). Twelve epochs/run, two warmup epochs,
H=6, 40 ms pacing, three worker threads, finite task/epoch capacity and 300 ms
result deadline were fixed before outcomes. Delay, timeout, crash and saturation
were not selected from performance. Collection ran without concurrent CSC
experiment work; the host was not isolated from other applications/services.

## Cadence and evidence yield

| Mode | Normal cadence ms | Severe-delay cadence ms | Paired severe effect median [range] ms | Normal complete evidence fraction |
|---|---:|---:|---|---:|
| K=0 | 40.368 | 40.409 | -0.007 [-0.110, 0.138] | 0 (no shadows planned) |
| Sync K=1 | 147.027 | 266.100 | 119.463 [102.336, 125.219] | 1.000 |
| Sync K=2 | 163.376 | 280.209 | 112.554 [107.971, 133.243] | 1.000 |
| Async K=1 | 40.436 | 40.471 | 0.058 [-0.182, 0.174] | 0.100 |
| Async K=2 | 40.498 | 40.369 | -0.129 [-0.195, 0.211] | 0.000 |

Metrics reduce epochs within runs before seed medians. Five paired effects are
retained for every group. No equivalence margin or post-result pass percentage
was introduced. Moderate delay had paired median effects 44.817/43.011 ms for
sync K=1/K=2 and 0.025/0.001 ms for async. A shorter median under a fault is not
a speed benefit: a single fault affects tails, while the median can mostly
reflect unaffected epochs. Run p95/p99 have only ten measured epochs and are
descriptive, not real-time tail guarantees.

Async normal K=2 already exhausted capacity and deadlines: across the five
measured ten-epoch blocks, 60 branches expired and 90 dropped. K=1 had 61 expired,
30 dropped and median complete fraction 0.1. Severe-delay complete fractions
were zero for both. Thus production cadence was preserved substantially by
shedding evidence; the current worker/configuration is unsuitable for continuous
high-yield evidence collection at 40 ms. Full complete/partial/production-only
fractions, queues, completion times, faults and resources are in
`tables/cycle4_async_tables.md` and the archived `analysis.json`.

## Integrity, faults and resource microstudy

All 162 production runs completed with identical workload and authoritative
trajectory hashes within each seed across conditions/modes, no observed unexpected
actuation, and no missing production epochs. Verification replayed 3,964 successful
branches from 17 archived source files, checked artifact/config/journal joins and
regenerated summaries exactly; `tables/cycle4_async_verification.json`.
Unavailable/incomplete evidence never acquired a favourable regret value.

The three-seed CPU/memory/occupancy probe had paired median cadence effects
0.079/0.021/-0.001 ms. Logical nonblocking remained intact, but complete evidence
remained near zero. This small fixed load does not establish resource
non-interference. Worker CPU in the CPU probe was measurable (median 62.5 ms);
short Windows CPU samples quantized to zero elsewhere. RSS was unavailable;
tracemalloc is Python allocation only. Queued/running depths, serialized bytes
and observed PID counts are available, but expired worker/PID telemetry is
incomplete and shared CPU/scheduler/storage contention remains possible.

The red-team found numeric overflow cases in correctly identified malformed
shadow output. The current tree rejects oversized integer components,
overflowing weighted utility and nonfinite mirror distance before comparison;
the regression verifies rejection and next-epoch progress. These corrections
are locally tested and absent from the immutable measured source. One suite
attempt during concurrent verification had a localhost HTTP timeout; the clean
final suite passed 54 tests in 29.807 s. The cause of that transient was not
independently isolated and remains a validation limitation.

## Decision and limitations

**Local logical decoupling established for the tested finite cooperative runs;
local wall-clock decoupling evidence is descriptive.** The production path does
not wait for shadow completion; bounded polls, serialization, storage and comparison
still execute on that thread and can affect timing. Post-loop shutdown joins
finite-timeout transport threads and can delay experiment completion.

The store has one writer and atomic JSON replacement, but flushed JSONL is not
an fsync transaction. New-run restart rejects old identities; durable queue
recovery, arbitrary crash/power-failure recovery and distributed exactly-once
operation are unimplemented. Completed history retained in memory is bounded by
these finite runs, not by a service-wide retention policy. Traffic allows only
two distinct alternatives; K>2 requires a larger action space.

## Next action

Cycle 5 should preregister a longer warmed/reusable-worker async throughput,
coverage and resource-contention experiment, with finite retained history,
production-side independent timing, and interruption/restart characterization.
The first systems objective is useful evidence yield at preserved cadence.
Neither K3s containment nor real-time safety follows from these results.
