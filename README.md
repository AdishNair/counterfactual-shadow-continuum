# Counterfactual Shadow Continuum (CSC)

CSC is a research runtime for evaluating alternative decisions beside an
authoritative production decision path. At each epoch it captures a versioned
state anchor and event window, executes production once, and evaluates a
same-action mirror plus up to `K` distinct alternatives without allowing those
shadow branches to actuate production.

The implemented domain is a deterministic software traffic model for Junction
J1. Production is authoritative only inside that model. Shadow outcomes are
estimates: they are not physical observations, factual counterfactuals, or a
basis for policy learning.

## Current research state

- Cycle 5 is closed. Its immutable local performance archive remains historical
  evidence from its exact measured source.
- Cycle 6 is the final systems-validation cycle and is currently executing its
  frozen controlled-host study.
- Counterfactual trust remains **Decision D: not established for policy use**.
- Learning and policy promotion remain **BLOCKED**.
- Local async coordination and cold/warm workers are implemented. Kubernetes,
  hostile-code containment, hard real-time behavior, physical traffic validity,
  process-memory boundedness, and general resource isolation are not established.

Start with [research/RESEARCH_CONTEXT.md](research/RESEARCH_CONTEXT.md), then
[research/RESEARCH_STATUS.md](research/RESEARCH_STATUS.md). The claim-to-evidence
map is [research/CLAIM_EVIDENCE_MATRIX.md](research/CLAIM_EVIDENCE_MATRIX.md).

## Repository map

| Path | Purpose |
|---|---|
| `csc/` | Runtime contracts, production/shadow execution, async coordinator, worker pool, storage, safety boundary, and resource instrumentation |
| `experiments/` | Reproducible campaign runners, pressure/fault helpers, replay, deterministic analysis, and verification |
| `tests/` | Correctness gates for authority, replay, async behavior, warm-worker reset, queue bounds, storage isolation, and campaign provenance |
| `configs/` | Small local example configurations |
| `deployments/` | Docker/K3s deployment intent and optional gVisor patch; configuration is not deployment evidence |
| `research/` | Canonical research state plus the active Cycle 6 workspace |
| `research/cycle6/` | Frozen Cycle 6 protocol, review, deployment registry, and eventual results/closure records |
| `research/evidence/` | Historical cycle evidence retrieved only when needed |
| `research/archive/` | Superseded reviews and maintenance history; not current authority |
| `research/tables/`, `research/figures/` | Deterministically generated outputs whose paths are referenced by prior work |
| `results/` | Local immutable raw experiment archives; excluded from normal Git commits because they are about 1 GiB |
| `docs/` | Focused architecture and interface notes |
| `ARCHITECTURE.md` | Current component and data-flow overview |
| `IMPLEMENTATION_STATUS.md` | What is implemented, tested, measured, or still unvalidated |
| `RESULTS.md` | Canonical measured-result index and scientific limitations |
| `AGENTS.md` | Repository rules and documentation authority order |

## Runtime model

An epoch follows this sequence:

1. Capture canonical state and verify its SHA-256 identity on hydration.
2. Select and authorize exactly one production action.
3. Commit the authoritative production transition.
4. Admit a mirror first, then distinct alternatives within item and serialized
   request-byte limits.
5. Run shadows with cold subprocesses or reset/hydrated warm workers.
6. Accept only correctly identified, finite, comparable results before deadline.
7. Record requested, admitted, and completed `K` separately.
8. Persist optional CFR/branch evidence through a bounded spool with explicit
   persistence or loss states.

`K` excludes the mirror. The traffic action space has three meaningful actions,
so its empirical range is K=0, K=1, and K=2.

## Local setup

Python 3.11 or newer is sufficient; the runtime uses the standard library.

```powershell
python -m unittest discover -s tests -v
python -m csc configs/baseline.json
python -m csc configs/csc_k1.json
python -m csc configs/csc_k2.json
```

Replay an existing local run with:

```powershell
python -m experiments.replay results/<series>/<run>
```

Replay verifies hashes and reconstructs recorded trajectories within the
declared deterministic boundary. Process timing, operating-system behavior, and
physical validity remain outside that boundary.

## Cycle 6 workflow

The active protocol is [research/cycle6/PROTOCOL.md](research/cycle6/PROTOCOL.md).
It freezes a 70-run Gate A registry: 54 paired factorial runs, 15 targeted
optional-storage fault runs, and one 10,000-epoch continuous run. The campaign
must execute from a fully archived source/configuration/analysis closure and be
verified before interpretation. Gate B requires a real policy-enforcing
container/Kubernetes environment; manifests or localhost processes cannot count
as enforcement evidence.

Do not run Cycle 6 conditions ad hoc or overwrite a result directory. Use the
frozen runner and a new unique output path.

## Evidence and provenance

Raw result archives are append-only research evidence. Each run records its
configuration and source hashes, workload identity, environment, artifacts,
production trajectory, resource samples, lifecycle state, and summary. The
campaign registry and verifier account for failed and unattempted identities as
well as successful runs.

The default `.gitignore` excludes raw `results/` to keep the source repository
manageable. See [results/README.md](results/README.md) for handling rules. A
numerical claim is valid only when it traces to its immutable archive or verified
derived analysis.

## Scientific and security boundaries

CSC currently supports systems research on local logical decoupling, evidence
yield, bounded named queues, worker lifecycle, failure behavior, and reproducible
software trajectories. It does not establish:

- factual or physically valid counterfactual outcomes;
- decision-time trust or learning benefit;
- hard real-time safety or zero resource interference;
- indefinite process-memory boundedness;
- hostile-container isolation or cloud deployment validation;
- domain independence, arbitrary K scaling, or production readiness.

Local workers are first-party cooperative processes. Do not execute hostile or
third-party code through the local worker mode.

## Working with the repository

Follow the authority order in [AGENTS.md](AGENTS.md). Keep runtime code in
`csc/`, runnable research methods in `experiments/`, current Cycle 6 material in
`research/cycle6/`, and raw output in a new `results/` directory. Preserve
negative findings and keep measured-source claims separate from later correctness
fixes.

The supplied [implementation specification](CSC-Agent-Implementation-Spec.md) is
the design reference. It describes intended architecture; it is not evidence
that every capability has been implemented or deployment-validated.
