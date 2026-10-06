# CSC core and domain-coupling audit

**STATUS:** AUDIT — no generalization claim has been tested.

## Question

Which parts of the current prototype are CSC-runtime semantics, and which are
specific to the J1 traffic demonstration?

## Evidence and method

Reviewed `csc/contracts.py`, `csc/runner.py`, `csc/branches.py`, `csc/world.py`,
`csc/sync.py`, `csc/safety.py`, and `csc/compare.py`, plus current tests. This is
a source audit; it does not demonstrate a second domain.

## Findings

The following mechanisms are plausibly reusable CSC core concepts:

| Candidate core responsibility | Current location | Coupling assessment |
|---|---|---|
| Branch role/identity, parent anchor, window | `contracts.Branch` | Mostly generic; `J1` is hard-coded in validation and IDs. |
| Immutable anchor and hash verification | `Anchor`, `StateCaptureEngine` | Generic pattern; serialization currently assumes a dataclass traffic state. |
| Ordered input checks and comparability | `sync.InputSynchronizationLayer` | Generic with event contract assumptions. |
| Virtual versus authorized actuation | `safety.VirtualActuator`, `ActuatorGateway` | Generic policy shape; gateway claims and target are traffic/J1-specific. |
| Branch timeout, result validation, cleanup | `branches.BranchManager` | Largely generic, but subprocess protocol imports J1 state/config. |
| Provenance, mirror epsilon, record exclusion | `compare.OutcomeComparisonEngine` | Conceptually generic; utility is traffic metrics and record shape exposes traffic traces. |
| Artifact manifests and replay | `store.KnowledgeStore`, `experiments/replay.py` | Generic intent; replay constructs `ProductionWorld` directly. |

Traffic is currently coupled into all decisive paths. `State` has NS/EW queues and
phases; `ACTIONS` is global; `Config` mixes runtime and traffic parameters;
`MultiBranchScheduler` ranks traffic queues; `ProductionWorld`,
`ShadowWorldModel`, `workload`, `domain_metrics`, and `outcome` use traffic
fields; `runner.run` directly constructs traffic state/world/workload. The remote
worker and replay paths inherit those assumptions.

## Interpretation

The repository demonstrates a **traffic-specific implementation of CSC
mechanisms**, not an existing domain-independent CSC runtime. The explicit anchor,
branch, synchronization, provenance, virtual actuation and comparison concepts
are reasonable candidates for a core. Their current code arrangement is not yet a
valid transferability result.

## Recommended smallest refactor

Do not claim generality or add a second domain before introducing an explicit
domain adapter boundary. The next implementation increment should pass a single
adapter into the runner and worker protocol while preserving `TrafficAdapter` as
the default. It should not change current JSONL semantics or regenerate prior
results. A second minimal adapter should be selected only after the refactor tests
the same core without domain-specific conditionals.

## Limitations

This is a structural audit, not a performance or correctness evaluation. A clean
interface can still hide semantics that do not generalize: what is an action,
which inputs are exogenous, how authoritative actuation is recognized, and how a
short-horizon shadow world is constructed are domain decisions.

## Open questions

1. Can a generic state codec safely capture state without a traffic dataclass?
2. Can the generic worker invoke a separately packaged SEM without gaining an
   authoritative actuation capability?
3. Is a second domain small enough to test the architecture rather than create a
   new project?

## Next actions

1. Review [DOMAIN_INTERFACE.md](../../../docs/DOMAIN_INTERFACE.md) with the
   counterfactual-validity and methodology findings.
2. Add adapter contract tests before refactoring `runner.py`.
3. Preserve the existing traffic adapter/output schema as a versioned baseline.
