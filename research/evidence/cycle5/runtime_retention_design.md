# Cycle 5 runtime retention design

**Status:** Implemented; correctness tests locally tested. Long-run slope evidence
is reported separately in `cycle5_results_analysis.md`. This is a local
first-party process runtime, not hostile-code containment.

**Variant boundary:** Main Cycle 5 measurements used the frozen pre-review
variant. Its tracked ledger bounds did not bound the executor's physical cancelled
work-item backlog. Post-measurement hardening replaces that executor with a
physical-capacity FIFO and exposes its queue/inflight counts. The first correction
passed 80 tests in 30.089 seconds; after independent re-review, further ownership
and quarantine corrections passed 96 tests in 28.181 seconds. Later shutdown and
unresolved-process findings were reproduced and corrected; the final v4 gate
was followed by timing/analysis/source-copy corrections. The final v5 gate passed
108 tests in 28.362 seconds and its independent review found no remaining material
issue in that bounded scope. Current continuous performance remains
unmeasured. See `cycle5_post_review_hardening.md` through
`cycle5_post_review_hardening_v5.md`. Main count bounds and positive memory
slopes must retain their earlier-source provenance.

## Question and method

Can continuous async execution retain finite hot state without deleting research
evidence? The design separates bounded coordinator/worker state from append-only
run evidence. Bounds are explicit configuration and are sampled every epoch.
Source: `csc/pending.py`, `csc/async_runner.py`, `csc/branches.py`, `csc/warm.py`,
`csc/sync.py`, and `tests/test_cycle5_runtime.py`.

| Hot state | Retention semantics |
|---|---|
| Pending epoch packages | At most `max_pending_epochs`; oldest package expires on capacity pressure; every package has a fixed evidence deadline. |
| Active futures/packages | At most `max_pending_shadow_tasks`; expired running work retains its permit until actual completion. Cancelled queued work settles on polling. |
| Physical dispatch items (post-review variant) | At most `max_pending_shadow_tasks`, running plus queued; cancellation does not release a physical permit until dequeue. Sampled ledger counts in the earlier main archive do not measure this bound. |
| Finished summary records | Ring of `retention_completed_epochs`, default 64. No full trajectory cache. |
| Finalized duplicate IDs | Ordered cache of the same count. Monotonic committed epoch watermark rejects old/repeated commits after cache eviction. |
| Production resource history | Ring of the same count; full resource observations are durable JSONL. |
| Per-epoch synchronization | Delivery-local sets, dictionaries and lists; no persistent input buffer. |
| Worker lifecycle history | Cumulative integer counters plus current process set, bounded by worker slots. History events live on disk. |
| Warm assignment metadata | Version 1 allowlist; 128-ID ring plus latest epoch, experiment identity and completed-task integer. Prior IDs beyond the ring are stale by epoch. |
| Warm worker model state | Fresh model, actuator, hydrated state, config, events, trace and synchronization for each assignment. No model/task cache retained. |
| OS resource metrics | Current samples only; null remains unavailable. Windows working-set RSS, process times and handles measured through OS APIs. |
| Durable writer streams | One coordinator writer; fixed artifact names; one open stream per artifact. |
| Replay/index metadata | No continuous in-memory replay index; source/config hashes and artifact index have fixed file count. |

## Admission and completion

Async planning preserves requested distinct alternatives even when worker slots
are fewer than branches. Mirror-first admission processes branches individually,
then alternatives in their static domain action order. Admission drops on a full
bounded queue or zero worker capacity. Requested/admitted/completed K are
independent fields: K excludes mirrors. Completion requires every requested
branch in a comparable epoch, not merely one finished branch. Missing alternatives
leave regret unavailable. No learned scheduling or policy learning exists.

The epoch watermark requires strictly increasing commits within a run. Restart
uses a new experiment identity and a new immutable directory; pending work is
discarded. Late results cannot resurrect retired records. Durable exactly-once
distributed recovery is not implemented. Existing evidence is never evicted to
satisfy hot retention bounds.

## Storage and offline analysis

Archives grow with epochs: anchors, events, production journals, trajectories,
lifecycle and resource observations are append-only. This is **not bounded total
disk storage**. The local experiments provision finite run budgets and measure
growth; no indefinite finite-disk service claim follows. A future archive quota
and external checkpoint/export contract is needed before indefinite operation.

The store opens JSONL files exclusively, flushes each append, enforces a single
coordinator writer, and replaces JSON summaries/manifests using a temporary file.
Flush is not fsync; manifests are not cross-file transactions. Storage pressure
and serialization share coordinator time and can affect later production starts.
A write failure is an explicit run failure, not silently lost production evidence.
Persistent storage failure can prevent final failure-manifest generation; partial
RUNNING archives must remain visibly incomplete during verification.

After production stops, exact summary generation rereads durable CFR and resource
records. This offline phase currently loads the finite run into arrays to preserve
the existing exact distribution semantics. Its time/RSS/Python allocation peak
are separately recorded and excluded from bounded continuous-hot-state claims.

## Findings, limits and next actions

The gate checks 90 epochs with an eight-record ring, active/pending/process bounds,
90 preserved CFR records, and production trajectory equivalence with K=0. The
main measured variant additionally ran 3,000 normal and 1,000 saturation epochs.
Recorded rings reached 64, tracked active tasks at most 12 and pending epochs at
most eight. The physical executor backlog was not measured by those samples.
All-online-epoch RSS slopes remained positive: 559.572129 and 766.557836
bytes/epoch; second-half slopes were 339.915183 and 265.008787 bytes/epoch.
Python current-allocation second-half slopes were 23.340010 and 191.496683
bytes/epoch. The normal long run's offline summary RSS reached 488.429688 MiB.
These deterministic results are in `research/evidence/cycle5/cycle5_results_analysis.md` and
`research/tables/cycle5_review_packet.json`; they support finite tracked count
bounds, not an indefinitely stable memory plateau. Current physical-capacity
corrections were regression-tested after these measurements and do not alter them.
Count bounds do not guarantee a fixed RSS limit: Python allocation/fragmentation,
thread scheduling, OS working-set policy, result size and import caches remain
measured concerns. Warm framed responses are bounded before JSON decoding; cold
baseline `communicate()` accumulates response bytes before size rejection, and
HTTP decoding retains its prior transport limitations. No hostile-body memory
guarantee is claimed.

Next actions: inspect long-run current allocation/RSS/handle slopes and complete
evidence distribution; preserve negative storage results; implement archive quota
and streaming offline statistics only under a separate declared contract.
