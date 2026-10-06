# Cycle 5 failure and recovery

**Status:** Locally tested first-party process and deterministic ledger fault validation, 2026-10-06.

## Question, evidence and method

Do explicit worker, delivery, retention, schema, storage and capacity faults preserve authoritative production, and what evidence is lost?
Evidence: `results/cycle5-validation/faults-20261006T135732Z-3827f22a/fault_results.json`, its pre-execution `protocol.json`, immutable source archive, raw synthetic ledger records and full-run manifests.
`experiments/cycle5_faults.py` generates every classification below. Each synthetic assertion uses a fake clock/deferred future; physical worker cases execute full authoritative local runs, compare paired trajectory/workload hashes and replay accepted trajectories.

Campaign checks passed: **True**; cases: **12**; source stable during collection: **True**. A passing check means the declared fault behavior was observed, not that availability survived every fault.

## Preserved earlier validation attempts

- `results/cycle5-validation/faults-20261006T135137Z-0498e3d5`: passed=False, source_stable=True, failed checks=['warm_transport_body_bound'].
- `results/cycle5-validation/faults-20261006T135327Z-0c35f07d`: passed=True, source_stable=True, failed checks=[].
- `results/cycle5-validation/faults-20261006T135552Z-b182ce77`: passed=False, source_stable=True, failed checks=['worker_dies_during_processing', 'worker_dies_after_completion_before_ack'].

Earlier runs retain their own source identities. A failed initial body-bound assertion expected pre-deadline FAILED delivery but observed EXPIRED/late delivery; the subsequent validation separates direct transport rejection from full-run deadline outcomes without extending the epoch deadline. Later worker loop-local cleanup produces a separate source variant and requires fresh validation, not alteration of archived evidence.

## Findings

The preserved `b182ce77` source-stable attempt also required a FAILED ledger
count for physical death even when its transport failure arrived after the
unchanged deadline. The final method requires visible terminal loss, worker
failure and replacement, while retaining the separate FAILED/EXPIRED/LATE
counts. Neither physical-death run is classified as recovered complete evidence
merely because its production trajectory remained equal.

| Fault | Method | Production impact | Evidence impact | Recovery | Checks |
|---|---|---|---|---|---|
| restart_queued_foreign_duplicate | deterministic ledger fixture; no OS process fault | fixture production unchanged | old queued work discarded; two foreign deliveries rejected | new identity; no durable old-queue resume | True |
| result_after_retention_eviction | deterministic ledger fixture; no OS process fault | fixture production comparisons unchanged | late old result cannot resurrect archived comparison | terminal package plus monotonic commit watermark | True |
| prolonged_saturation_100_epochs | deterministic ledger fixture; no OS process fault | all 100 fixture production comparisons finalized | 198 later branches dropped; two running branches expired | expired running futures retain permits | True |
| partially_unavailable_pool | deterministic ledger fixture; no OS process fault | fixture production retained | mirror accepted, alternative failed, regret unavailable | remaining slot can serve; failed result terminal | True |
| nan | deterministic ledger fixture; no OS process fault | fixture production retained | invalid estimate rejected; comparison incomplete | terminal rejection; next epoch can commit | True |
| huge_integer | deterministic ledger fixture; no OS process fault | fixture production retained | invalid estimate rejected; comparison incomplete | terminal rejection; next epoch can commit | True |
| oversized_body | deterministic ledger fixture; no OS process fault | fixture production retained | invalid estimate rejected; comparison incomplete | terminal rejection; next epoch can commit | True |
| overlong_trace | deterministic ledger fixture; no OS process fault | fixture production retained | invalid estimate rejected; comparison incomplete | terminal rejection; next epoch can commit | True |
| worker_dies_during_processing | physical warm-process death during full local authoritative run | all production epochs retained; paired trajectory hash equal | FAILED=1, EXPIRED=23, LATE=6; incomplete comparisons retain missingness; late fault transport need not become pre-deadline FAILED | worker discarded; later assignment launches replacement; no durable retry/ack protocol | True |
| worker_dies_after_completion_before_ack | physical warm-process death during full local authoritative run | all production epochs retained; paired trajectory hash equal | FAILED=1, EXPIRED=9, LATE=3; incomplete comparisons retain missingness; late fault transport need not become pre-deadline FAILED | worker discarded; later assignment launches replacement; no durable retry/ack protocol | True |
| warm_transport_body_bound | real full run plus isolated real-worker transport check at configured 6000-byte line bound | three production epochs retained; paired trajectory hash equal | no full-run branch accepted; direct oversized output rejected before JSON parsing; full-run failure/expiry counts retained | direct rejected worker discarded; no enlargement of the 300ms epoch deadline | True |
| storage_temporarily_fails | one-shot injected coordinator cfr append OSError during full run | authoritative run aborted after 1 recorded production epochs; production cadence not preserved | partial run retained as FAILED; no successful full-run summary | one-shot failure permits exception-path finalization; new immutable run needed; no storage failover | True |

**Negative availability finding:** A one-shot CFR storage write failure aborts the authoritative run; it is not isolated to evidence. The partial immutable run is marked FAILED when subsequent cleanup writes succeed. This is a production impact and must not be hidden in aggregated shadow-fault robustness.

## Limitations and open questions

The after-completion fault deliberately kills the worker and discards a real result between receipt and coordinator acceptance. It verifies visible loss/replacement, not a durable acknowledgment protocol or recovery of an unacknowledged completed result. Restart starts a fresh run identity and discards old queued work; it does not restore an old coordinator. Eviction rejection retains the active package's terminal state and a monotonic commit watermark; there is no network endpoint that accepts arbitrary old package objects.

Ledger fixture production checks establish immutability/finalization only; they do not measure OS scheduling, cadence or resource isolation. Physical worker death is tested in this cooperative local implementation, not hostile code. The actual warm line reader applies a byte bound before JSON parsing; the cold path captures subprocess output before checking size, and HTTP response parsing is not transport-body bounded. Oversized valid-identity synthetic output therefore tests coordinator rejection rather than universal transport memory safety.

The storage case is one transient failed append, not torn writes, disk exhaustion or persistent I/O failure. Persistent failures during exception cleanup can prevent a FAILED manifest update. JSONL flush is not fsync; atomic JSON replacement is not a multi-artifact transaction. All accepted full-run branches are replay checked; failed/incomplete branches have no invented outcomes.

## Next actions

Separate required production durability from speculative evidence persistence before claiming graceful degradation under storage outages. Define explicit fail-open/fail-closed requirements, bounded evidence spool/drop behavior and interrupted-run recovery. Bound cold/HTTP transport reads if those backends enter sustained or untrusted-output studies. Preserve trust Decision D and learning BLOCKED; no policy learning or second domain follows from these fault checks.
