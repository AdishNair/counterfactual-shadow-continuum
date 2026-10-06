# Domain-adapter readiness

**Status:** Bounded architecture assessment, 2026-10-05; no second domain or
adapter implemented. This is preparation, not a domain-independence result.

## Question and method

Which existing traffic assumptions prevent substituting another domain? CodeGraph
context/source inspection of contracts, branch scheduler, world, comparison, and
replay supplies the evidence below. No domain performance experiment was run.

| Boundary | Current coupling / evidence | Required future contract |
|---|---|---|
| State capture | `csc/contracts.py`: `State` validates J1, two queues and signal phase; `Anchor.hydrate` constructs it | Versioned domain state codec/validation with canonical bytes and immutable anchor identity |
| Actions | `csc/contracts.py`: three fixed `ACTIONS`; branch IDs include J1 | Domain action enumeration/validation, stable site identity, distinct-action budget |
| Scheduler | `csc/branches.py`: `MultiBranchScheduler.decide` compares NS/EW queues; `plan` enumerates traffic alternatives | Production policy interface and domain candidate provider, with generic branch identities |
| Production | `csc/world.py`: `ProductionWorld` owns queues, phases, discharge and incidents | Authoritative environment adapter behind the existing capability/gateway boundary |
| Shadow | `csc/world.py` and `csc/branches.py`: model configuration and worker request use traffic state/actions | Versioned non-actuating model adapter with no production capability |
| Utility | `csc/compare.py`: queue, waiting-vehicle ticks and phase-switch weights | Declared domain metric/utility schema with units and version hash |
| Divergence | Cycle 3 `experiments/analyze_counterfactual_failure.py`: Euclidean NS/EW queue trajectory distances | Separately justified domain distance; never presume queue distance generalizes |
| Replay | `experiments/replay.py`: reconstructs `ProductionWorld`, `Config`, `Event`, and shadow execution directly | Source-pinned replay adapter; domain schema and input identity checks |
| Comparison | `csc/compare.py`: identity/comparability checks reusable; metric utility and epsilon interpretation domain-bound | Retain generic joins/exclusions; inject versioned metric semantics without changing authority |
| Experiment config | `csc/contracts.py` and `csc/world.py`: service rates, demand profiles and incident generation | Separate orchestration configuration from domain scenario/model configuration |

## Findings and limitations

Canonical anchors, branch roles, input-window identity, actuation boundaries,
artifact integrity and lifecycle bookkeeping are plausible reusable concepts.
That is a structural observation, not proof of portability. Traffic currently
has only two distinct alternatives to a production action; K above two cannot
be studied by duplicating branches. Queue accounting can be generic while the
available action set remains limited.

Source isolation in the authored reference must survive any adapter extraction:
sharing a codec is different from sharing transition implementation. A single
common domain dynamics adapter for production, shadow and reference would erase
the independence the trust study needs.

## Next action

Defer refactoring and second-domain implementation. If generalization becomes the
next evidence priority, freeze the codec/action/metric/replay contracts first,
retain J1 as a regression domain, and then test a second domain independently.
Async timing or J1 trust success would not establish this claim.
