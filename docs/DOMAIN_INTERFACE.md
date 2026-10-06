# Minimal CSC/domain interface

**Status:** Proposed architectural contract, 2026-10-06. Traffic remains the only
implemented domain. No adapter extraction or second domain is claimed.

## Question, evidence and method

What smallest interface separates reusable CSC lifecycle/accounting from traffic
without relaxing production authority or changing existing evidence semantics?
This contract derives from `research/evidence/cycle4/domain_adapter_readiness.md`, the
CodeGraph/source survey of `csc/contracts.py`, `csc/branches.py`,
`csc/world.py`, `csc/compare.py`, `csc/pending.py`, `csc/safety.py`, and
`experiments/replay.py`. No generalization experiment or code refactor was
performed for this artifact.

## Proposed contract

| Domain responsibility | Minimal interface and invariant |
|---|---|
| State codec | `capture_state() -> canonical bytes`; `validate_state(bytes, schema_version)`; `hydrate(bytes) -> fresh state`. Include domain/site ID, version, watermark, deterministic RNG state and policy context. Core hashes canonical bytes and binds them to epoch/run identity; hydration must preserve exact identity. |
| Actions | `validate_action(action)`; `alternatives(state, production_action) -> ordered distinct actions`. Stable IDs, declared semantics and priority. Exclude the production action and duplicates; report requested/admitted/completed K separately. |
| Production policy | `decide(state, policy_config) -> action`. The domain owns state interpretation. The core owns the authoritative identity/capability gateway and never gives that capability to a shadow adapter. |
| Inputs | Versioned event codec and window contract with site, sequence, epoch, canonical input hash and declared exogenous semantics. A fresh per-task input buffer consumes only its assigned window. |
| Authoritative environment | `snapshot_state`; `apply_action(action, capability, correlation_id)`; `step(event)`. Keep this adapter behind the production gateway. Domain state mutation is never an interface exposed to workers. |
| Non-actuating model | `evaluate(anchor, action, events, model_config, rng_contract) -> estimated outcome`. Create/reset a fresh model for each assignment; return no production credentials/handles. Retained caches require declared immutability/action-state independence or clearing. |
| Outcome metrics | Versioned named metrics, units, validity bounds and `utility(metrics, utility_config)`. The core validates finite bounded schemas and provenance; the domain defines the scientific meaning. Mirror epsilon is a domain utility difference, not a universal error bound. |
| Trajectory distance | Optional separately versioned distance over comparable trajectories, with units and timing contract. Traffic queue L2 does not become a generic uncertainty certificate. |
| Replay | Source-pinned production and shadow replay adapters reproduce declared deterministic outcomes from saved anchor/action/input/config/seed. Artifact, source, schema and input identity checks precede replay. |

The core owns run/epoch/branch identities, canonical hashes, branch roles,
lifecycle, bounded admission, workers/transport, deadlines, retained-history
policies, provenance/comparability joins, immutable artifacts, and restart
identity. A domain adapter supplies dynamics and semantics, never admission
authority or permission to promote estimated outcomes into production facts.
Runtime accounting may handle arbitrary distinct K; the traffic action set
`NS_GREEN`, `EW_GREEN`, `BALANCED` has at most two meaningful alternatives to
each production action.

## Findings and implementation boundary

Existing source still binds `State`/`Anchor.hydrate` to J1 queues, validates fixed
traffic actions, selects production actions from NS/EW demand, computes traffic
utility, and reconstructs traffic worlds during replay. The reusable core above
is a proposed separation of responsibilities, not an implemented plugin API.
Keep orchestration configuration (pool capacity, deadlines, retention) separate
from future domain/model configuration; include both version identities in every
assignment/result. Capability creation stays outside either serialized config.

The independent authored reference must not reuse the transition/metric
implementation of either production or SEM. Sharing a well-defined codec is
different from sharing dynamics; adapter extraction must preserve that boundary.

## Limitations, open questions and next actions

The interface has only been assessed against traffic. Arbitrary action schemas,
different event causality, continuous state, nondeterministic outcomes and live
environment capture remain untested. Before extraction, freeze contract versions
and cover present traffic behavior with cold/warm/replay/authority regression
tests. Then extract one boundary at a time without changing those outcomes.
Defer autoscaling and any second domain until that regression gate and a
separately authorized domain protocol exist. Neither async cadence nor warm
worker correctness establishes domain independence.
