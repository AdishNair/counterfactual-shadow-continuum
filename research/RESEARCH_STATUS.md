# CSC research status

**Status:** Canonical current research state after Cycle 5 closure (2026-10-06).

## What we know

| Topic | Current evidence | Current conclusion |
|---|---|---|
| Authoritative boundary | Application gateway, identity, and replay tests; local fault studies | Production is authoritative only in the declared Junction J1 software environment. Local application checks do not establish hostile containment. |
| Replay and determinism | Immutable matrix, fidelity, Cycle 4, and Cycle 5 archives with deterministic verification | Recorded first-party traces replay within their declared checks. This is not physical validity. |
| Async coordination | Cycle 4 and Cycle 5 local async implementations and finite experiments | Production does not await shadow completion in the tested async loop. Logical decoupling does not establish resource non-interference or real-time safety. |
| Cold versus warm evidence | Immutable Cycle 5 86-run archive | Warm workers materially improved complete evidence in normal local cells; cold K=1/K=2 was zero. Delay pressure reduced median complete yield to zero. |
| Warm reset correctness | Current-code v1-v5 gates, final v5: 108 tests | Tested reset, hydration, recycle, replacement, contamination, malformed/stale/duplicate assignment cases pass for the declared deterministic first-party model. |
| Retained state and memory | Cycle 5 finite long probes | Named hot counts were capped; positive all-online RSS/Python slopes prevent a bounded-process-memory or plateau claim. |
| Storage and recovery | Cycle 5 fault campaign | A transient append failure stopped production after 1/12 epochs. Durable storage recovery and production/evidence separation are not established. |
| Production cadence and resources | Cycle 5 paired local archive | Production hashes matched within seed units, but cadence had severe individual outliers. Resource non-interference and robust cadence are not established. |
| Trust | Frozen Cycle 4 source-isolated study and timing audit | **Decision D.** Alternative counterfactual trust is not established for policy use; current-window signals are post-window. |
| Learning | No learner; explicit runtime block | **BLOCKED.** No learning or policy-promotion claim is supported. |
| Domain transfer | Readiness/interface analysis only | Not established. The current model, actions, metrics, scheduler, and replay remain traffic-coupled. |

## What remains unknown

- Whether v5 sustains useful evidence at the intended cadence under controlled delay and safe shared-resource pressure.
- Physical executor queue counts/bytes, cancellation retention, and production-path fault containment under sustained failure.
- Whether process memory reaches a stable bounded region during a sufficiently declared continuous run.
- Storage availability, partial-write recovery, and an explicit separation of required production persistence from optional evidence persistence.
- Robust cadence tails under controlled load and the operating region where useful evidence and production health coexist.
- Hostile containment, physical traffic validity, domain independence, and cloud/K3s deployment behavior.

## Blocked or explicitly deferred

- **Trust:** remains Decision D. Do not generate Cycle 4 final held-out trust seeds or retune the failed selector.
- **Learning:** remains BLOCKED. Do not implement policy learning or policy promotion.
- **Deployment claims:** no resource isolation, real-time guarantee, hostile-container isolation, physical validity, or cloud validation claim is supported.

## Next experimental gate

Before any new performance claims, preregister a fresh controlled-host systems study from the v5 source. Use a new immutable output directory and fresh seeds. Measure production-path fault containment, physical queue/byte bounds, storage failure/recovery, hot memory trends, cadence tails, and requested/admitted/completed K across normal, delay, worker-capacity, and safe resource-pressure conditions. Declare condition duration, including the cited 500-epoch condition standard and a separately declared 10,000-epoch continuous test, before collection.

The 86-run archive remains immutable and is the only source for Cycle 5 performance numbers. Later v1-v5 gates validate current-code correctness paths only; they do not revise archive measurements.
