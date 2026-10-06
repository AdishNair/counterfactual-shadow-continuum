# Cycle 5 warm worker correctness gate

**Status:** Implemented and locally tested before main performance collection.
The initial ten-test gate passed in 36.828 seconds. An initial full suite passed
all 66 tests in 88.258 seconds, including the eleven-test warm gate, before main
collection. Its immutable v1 archive precedes a final two-variable worker-loop
retention correction. The final frozen-source gate and full Python source closure
are in `results/cycle5-gate/runtime-20261006-v2/`: all 66 tests passed in 141.372
seconds after the loop correction, with configuration, seed,
environment and artifact hashes. These are tested
first-party worker conditions, not a hostile sandbox.

**Post-measurement correction:** Independent review found that the measured
manager returned warm processes before validating reported outcomes and omitted
blocking request writes from the service timeout. The current variant holds the
lease through validation, destroys corrupted processes, bounds writes/reads and
kills transports before dispatch joins. The first correction passed 80 tests in
30.089 seconds. Independent re-review found remaining destruction-exception,
validation/enrichment and constructor-ownership gaps; the second correction
passes 96 tests in 28.181 seconds, including 17 adversarial runtime tests.
Source-specific negative reproductions and regressions are in
`cycle5_post_review_hardening.md` and `cycle5_post_review_hardening_v2.md`.
Later re-review found a stranded lease waiter, unresolved cold-process capacity,
and downstream numeric/campaign gaps. The final correction uses closure-aware
leases, common cold/warm validation and finite aggregation bounds; its immutable
v5 gate passes 108 tests in 28.362 seconds. Independent v5 review closes the named
bounded paths, retaining a MINOR nonblocking integration-test limitation. Evidence
is in `cycle5_post_review_hardening_v3.md` through v5 and the corresponding
independent reviews. This expands local correctness evidence, not
the measured main performance claims.

## Question, contract and method

Can reusable subprocesses reproduce cold outcomes without cross-epoch model,
input, action, incident or RNG contamination? `tests/test_cycle5_runtime.py`
compares identical serialized anchor/action/window/config/seed requests in actual
fresh and persistent subprocesses. It requires exact equality of deterministic
trace, metrics, final state, anchor identity, observation window, input hash,
consumed sequence, comparability, virtual actuation, status and provenance. Runtime
timing, PID and lifetime counters are excluded from outcome equivalence.

No production world, gateway signing key or mutation capability enters either
worker. Both transports use a minimal environment whitelist and an ephemeral
directory. Warm readiness has its own bounded five-second handshake before a task;
the evidence deadline and service timeout are unchanged. Initial pool startup is
recorded separately from production, and replacement startup consumes executor
capacity rather than freeing an unfinished permit.

## Reset integrity beyond matching outputs

`csc/warm.py:WarmSession` rejects undeclared persistent attributes, unsupported
metadata versions, invalid metadata types, retained input buffers and changed
environment before executing a new assignment. The exact persistent allowlist is
`version`, `seen`, `last_epoch`, `experiment_id`, `completed_tasks`, `buffers`, and
`baseline_environment`. Only versioned bounded assignment metadata survives.
The warm protocol loop deletes its serialized input and output locals after each
flush, so it retains no preceding task record between assignments.

`csc/branches.py:execute_shadow` independently verifies anchor hash, experiment,
epoch, role and window. It instantiates new state/model/config/event-list/actuator/
trace/synchronization objects for every assignment. There is no retained model or
action-dependent cache. The model uses seeded local RNG where applicable; the
warm session resets global RNG from the anchor before execution and clears it
afterward. Environment integrity is checked after execution. Every reset,
assignment or execution error terminates the session; the manager kills/discards
the process, then creates a replacement on a later assignment. Periodic task-count
and lifetime recycling provide an additional finite lifetime, not the reset proof.

## Tested conditions and findings

| Condition | Test and required behavior |
|---|---|
| Repeated hydration and alternating actions/states | Twelve identical cold/warm request pairs span all three actions, alternating queue/phase regimes and incident/non-incident transitions; exact agreement, one reused PID. |
| Two-worker same-action determinism | Independent live warm PIDs agree exactly for the same request. |
| Intentionally contaminated input buffer | Injection fails integrity before execution; process destroyed; replacement PID completes next epoch. |
| Changed environment | Direct session integrity rejects added secret-like environment state. |
| Undeclared retained model state / changed metadata version | Direct integrity check rejects both before execution. |
| Task-count and lifetime recycle | Configurable recycling changes PID and preserves deterministic outcome. |
| Execution crash and service timeout | Original worker is destroyed; next request completes in replacement. |
| Physical worker death during processing | Real process kill after dispatch yields fault; replacement completes. |
| Duplicate and stale assignment | Assignment rejected and process destroyed; next valid epoch succeeds. |
| Malformed event, anchor and observation window | Assignment rejected and process destroyed; replacement succeeds. |
| Credentials | Environment construction excludes test production token and AWS secret; no authoritative object is serialized. |
| Continuous retention and production trajectory | Ninety epochs retain at most eight completed/duplicate/resource records, finite task/epoch/worker bounds, all durable records, matching K=0 production hash. |

Additional after-completion-before-ack loss, restart, stale delivery, prolonged
saturation, malformed numeric/body bounds and storage failures are classified by
`experiments/cycle5_faults.py`; their results remain independent of this gate.

## Negative attempts and methodological corrections

The first combined 26-test attempt had three failures. One used a 0.5-second
warm readiness timeout and intermittently could not start a replacement under
shared host load; readiness was separated into a bounded five-second initialization
contract without extending evidence deadlines. Two historical timing assumptions
failed with added resource telemetry: total three-epoch wall time exceeded an
arbitrary 100 ms assertion, and cancelled fake futures were counted as completed
shadows after a 20 ms expiry. The latter assertion now distinguishes cancelled
work from actual completion, preserving the no-completion-wait invariant. A later
historical rerun passed the 100 ms check but still exposed the cancellation issue.
The prefreeze full-suite attempt passed 65 of 66 tests in 64.912 seconds; the
same arbitrary 100 ms host-timing assertion observed 200.543 ms. It was replaced
with a direct guard on every async `Future.result` call requiring the future
already be done, while retaining zero barrier, trajectory identity and replay
checks. Cadence is measured by the main experiment instead of this test threshold.
Source review after the passing v1 gate found that the protocol loop's previous
`result` local persisted during the next execution. It was bounded and did not
influence model output, but conflicted with the strict retained-state contract.
The input/output locals were explicitly deleted after flush and the full suite
was rerun into a new v2 directory before performance collection. V1 is preserved.
These attempts are validation caveats, not experiment observations or evidence
of resource non-interference.

## Limitations and next actions

Finite deterministic equivalence and structural reset guards establish no detected
contamination under these tested first-party contracts. They do not prove absence
of arbitrary mutable module-global monkeypatching, hostile process memory access,
OS capability escalation or all possible model extensions. The current model is
deterministic and does not exercise a stochastic shadow transition. Future domain
adapters must declare every retained cache and random state explicitly and extend
the gate when their model contract changes. Performance studies may use warm
workers only after this gate passes; trust remains Decision D and learning blocked.
