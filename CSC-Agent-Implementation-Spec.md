# Counterfactual Shadow Continuum (CSC)
## AI-Agent Implementation Specification

> **Document role:** This file is the authoritative implementation-oriented specification for the student CSC prototype. Read the project explanation before writing code. Do not treat illustrative numbers, expected behavior, or design targets as measured results.

## 0. Instructions for the AI Implementation Agent

### 0.1 Project status
CSC is a **proposed cloud-edge runtime architecture**, not an already validated product. The purpose of the prototype is to test whether a practical subset of the architecture can be built and evaluated honestly within a semester.

### 0.2 Core idea in one paragraph
A normal cloud or edge controller chooses one action and observes only the result of that action. CSC proposes keeping that real **Production Branch**, while also creating isolated **Shadow Branches** that start from a comparable captured state, receive duplicated live inputs, and evaluate alternative decisions without being allowed to cause real external side effects. An **Outcome Comparison Engine** compares production and shadow outcomes, computes a regret/decision-quality signal, and records evidence that can later improve scheduling policy. The prototype must demonstrate the runtime mechanism first; sophisticated learning is secondary.

### 0.3 What the prototype must prove
The minimum credible prototype should demonstrate all of the following:

1. A production workload and at least one alternative shadow workload can be created from a controlled state boundary.
2. Production and shadow branches can receive the same ordered input events.
3. The production branch can perform the intended real/authoritative action.
4. The shadow branch cannot modify authoritative external state; its attempted side effects are redirected, mocked, or written only to isolated shadow state.
5. Both branches expose comparable outcome metrics.
6. The system computes a simple regret/decision-quality value from those metrics.
7. Branch lifecycle, resource usage, failures, and safety events are observable.
8. Experiments report overhead and limitations rather than assuming CSC is better.

### 0.4 Semester prototype boundary
Prioritize a buildable demonstration over an industrial implementation. The default target is:

- 3-node K3s cluster or an equivalent local multi-node test environment.
- One running application: adaptive traffic-signal control for Junction J1.
- One production branch plus 1–2 shadow branches.
- Containerized services.
- A simple event spine for ordered input duplication.
- Isolated state stores for production and shadows.
- Prometheus-compatible metrics.
- A deterministic or seeded traffic simulator/test harness for repeatable evaluation.
- Rule-based or simple scoring policy first; optional learning only after the runtime is stable.

### 0.5 Implementation priorities
Implement in this order:

**P0 — Correctness and isolation**
- Input duplication
- Branch identity
- Separate state
- Side-effect isolation
- Deterministic experiment control
- Metrics and logs

**P1 — Core CSC behavior**
- State capture at a decision boundary
- Branch creation/reset
- Alternative action assignment
- Outcome comparison
- Regret computation
- Branch cleanup

**P2 — Distributed deployment**
- K3s deployment
- Service discovery
- Event transport
- Failure handling
- Resource quotas
- Reproducible experiment scripts

**P3 — Optimization**
- Snapshot/delta optimizations
- Adaptive shadow count
- Branch pruning
- More advanced policy learning

Do not begin P3 until P0–P2 are demonstrably correct.

### 0.6 Important realism constraints
Do not assume that CSC can copy the complete physical world. A shadow traffic-light decision cannot physically move cars. Therefore the student prototype must use a controlled environment model/test harness to evolve the shadow world's traffic state after an alternative signal action. Duplicated sensor inputs provide exogenous observations; action-dependent physical consequences still require a model or simulator. Keep this distinction explicit in code, documentation, and evaluation.

Do not claim a globally atomic snapshot of arbitrary distributed applications. For the prototype, define an explicit **application-level state contract** containing only the state required by Junction J1 (for example queue lengths, signal phase, timers, recent arrivals, policy context, and version identifiers). Snapshot this controlled state consistently.

Do not assume syscall interception alone makes every application safe. Prefer architectural isolation: no production credentials in shadow branches, separate shadow databases/namespaces, deny-by-default egress, no physical device mounts, and mock actuator interfaces. Sandboxing is defense in depth.

### 0.7 Recommended implementation decomposition
Use clear service/module boundaries:

- `input-gateway`: receives/generates ordered traffic events and assigns sequence numbers.
- `state-capture`: creates versioned Junction J1 snapshots at decision boundaries.
- `scheduler`: chooses one production action and one or more shadow alternatives.
- `branch-manager`: creates/resets branch contexts and tracks lifecycle.
- `traffic-runtime`: executes the traffic-control logic for a branch.
- `actuator-gateway`: only accepts authorized production actuation; shadow calls are rejected or redirected.
- `shadow-world-model`: evolves counterfactual traffic state for shadow actions.
- `metrics-exporter`: exposes branch metrics.
- `outcome-comparator`: aligns comparable windows and computes utility/regret.
- `knowledge-store`: stores experiment tuples and provenance.
- `policy-updater`: initially optional; can start with a deterministic rule update.

The exact repository layout may differ, but these responsibilities must remain explicit.

### 0.8 Suggested data contracts
Every event should carry at least:

```text
event_id
sequence_number
event_time
source
junction_id
event_type
payload
experiment_id
```

Every state snapshot should carry at least:

```text
snapshot_id
state_version
decision_time
junction_id
queue_ns
queue_ew
signal_phase
phase_elapsed
recent_arrivals
policy_context
input_sequence_watermark
```

Every branch should carry at least:

```text
branch_id
experiment_id
branch_type = PRODUCTION | SHADOW
parent_snapshot_id
assigned_action
start_sequence
end_sequence
status
```

Every outcome record should carry at least:

```text
experiment_id
branch_id
action
observation_window
utility
queue_metric
latency_metric
resource_metrics
state_fidelity/confidence
failure_flags
```

### 0.9 Definition of non-actuation for the prototype
A shadow branch passes the non-actuation requirement only when:

- it has no credentials that permit production mutations;
- it cannot access physical actuator devices;
- outbound network access is denied except to explicitly allowed internal services;
- database/storage writes go to branch-specific ephemeral or shadow stores;
- actuator requests are captured as intended actions, not executed;
- tests deliberately attempt forbidden writes and verify they do not affect production state.

### 0.10 Minimum evaluation matrix
At minimum compare:

1. Baseline controller without CSC.
2. CSC with one shadow branch.
3. CSC with two shadow branches.

Measure:

- production decision latency;
- state-capture latency;
- branch startup/reset latency;
- CPU and memory amplification;
- event synchronization lag;
- dropped/out-of-order events;
- outcome-comparison latency;
- regret/decision-quality signal;
- production throughput;
- unauthorized actuation count (**must be zero in successful safety tests**);
- shadow divergence/fidelity indicators.

Never fabricate results. Store raw measurements and generate summaries from them.

### 0.11 Implementation rule
When this specification describes an ambitious mechanism such as eBPF capture, gVisor interception, Firecracker snapshots, online policy gradients, or complete distributed-state cloning, treat it as a design option rather than a mandatory first implementation. Choose the simplest mechanism that demonstrates the CSC principle correctly, then document what would be required to move toward the stronger architecture.

---

## 0.12 Reading map for implementation

Read the entire document once. During coding, prioritize these sections:

1. **Problem and CSC overview** — understand why the runtime exists.
2. **Architecture and runtime workflow** — authoritative component interactions.
3. **Non-actuating execution** — safety boundary.
4. **Algorithms and mathematical model** — semantics of branch comparison/regret.
5. **Prototype design** — implementation guidance.
6. **Evaluation plan** — determines what instrumentation must exist from the beginning.
7. **Limitations** — prevents implementing invalid assumptions as facts.

The remaining background and use cases explain motivation and novelty but should not expand the initial implementation scope.

---

# A Cloud–Edge Runtime Architecture for

Continuous Live Counterfactual Execution

Project Design Document

Status. Proposed architecture. Not yet implemented.

Purpose. To describe the CSC runtime architecture in enough detail that a student team can build

a prototype, measure it honestly, and later write a research paper from the results.

Scope. One semester, a team of 3–5 students, a three-node K3s cluster, and a single running example:

adaptive traffic-signal control at junction J1.

On claims. Every performance figure in this document is a design target or illustrative arithmetic,

never a measurement. Chapter 11 defines the experiments that would test them; Chapter 13 lists the

ways this design could fail.

Version 1.0

•

Draft for team and supervisor review

# Document Control

Field

Value

Document type

Project design document (pre-implementation)

Version

## 1.0 — draft for team and supervisor review

Status

Proposed architecture. Not yet implemented.

Intended audience

Final-year Computer Engineering project team, project supervisor, external

reviewers

Prototype scope

One semester, team of 3–5 students

Target platform

K3s cluster: 1 control node + 2 worker/edge nodes (laptops or SBCs)

Primary languages

Go (control plane), Python (decision worker, learning)

Running example

Adaptive traffic-signal control at a single junction (J1)

Deliverable of the project

Working prototype + measurement report + basis for a research paper

Revision history

Version

Change

Owner

0.1

Initial concept note: "run more than one decision at once"

Team

0.5

Component decomposition, actuation boundary defined

Team

1.0

Full design: architecture, workflow, algorithms, prototype plan, evaluation plan

Team

# What This Document Is

This is an architecture and implementation design document. Its job is to describe the Counterfactual

Shadow Continuum (CSC) in enough detail that a student team can:

1. Build a working prototype in one semester.

2. Measure the prototype honestly.

3. Later turn the measurements into a research paper.

It is not a research paper, not a literature survey, and not a textbook. Background material on Kubernetes,

containers, message buses, and reinforcement learning appears only where it is required to understand a CSC

design decision.

Throughout the document we are careful with claims. CSC is a proposal. Statements about behaviour are

written as design intent ("this design aims to. . . ", "the runtime should. . . "), and statements about performance

are written as hypotheses to be tested, not results. Chapter 11 defines the experiments that would test them;

Chapter 13 lists the ways CSC could fail.

# How to Read This Document

If you are. . .

Read first

Then

The supervisor / reviewer

Ch. 1–3, Ch. 12, Ch. 13

Ch. 11

The team lead / architect

Ch. 3–6

Ch. 10, Appendix E

The control-plane developer (Go)

Ch. 4, Ch. 5, Ch. 7

Ch. 10, Appendix B

The learning developer (Python)

Ch. 7, Ch. 8, Ch. 9

Ch. 11

The platform / security developer

Ch. 6, Ch. 10

Ch. 11 (E3), Ch. 13

The evaluation lead

Ch. 8, Ch. 9, Ch. 11

Appendix C

# Scope and Non-Goals

In scope for the prototype

- Live capture of a decision-relevant runtime state at fixed decision epochs.

- Forking that state into several isolated execution branches.

- Duplicating the live input stream to every branch, with the same ordering.

- Running all branches in parallel on the same runtime substrate.

- Enforcing that only one branch can touch the outside world.

- Collecting an outcome from every branch and comparing them.

- Computing a regret signal and feeding it into a policy update loop.

Explicitly out of scope

- Industrial-scale deployment, multi-tenancy, or SLA guarantees.

- Controlling real traffic hardware. The prototype’s "real world" is a software environment service (Chapter

9). This is stated once here and assumed everywhere.

- Beating a state-of-the-art traffic-control algorithm. The contribution under test is the runtime mechanism,

not the traffic policy.

- Proving anything about optimality, convergence, or safety in a formal sense.

# Terminology

These terms are used consistently for the rest of the document. Where a term collides with an existing industry

term (for example "shadow"), the CSC meaning is the one defined here.

Term

Symbol

Meaning

Decision epoch

ek

A fixed point in time at which the runtime must choose an action.

Epochs are numbered k = 0, 1, 2, . . .

Anchor state

sk

The serialised, decision-relevant runtime state captured at the start

of epoch ek. Every branch of epoch k starts from exactly this state.

Branch

b

One isolated execution of the decision worker for one epoch,

starting from sk.

Production branch

b0

The single branch whose actions are allowed to reach the

environment.

Shadow branch

b1 . . . bN

Branches that compute alternative actions and are structurally

prevented from affecting the environment.

Mirror branch

bm

A special shadow branch that executes the same action as b0. Used

to measure how wrong the shadow world is.

Branch set

Bk

{b0, bm, b1, . . . , bN} for epoch k.

Shadow horizon

H

How many runtime ticks a shadow branch runs before it is

terminated and discarded.

Actuation

—

Any effect that leaves the runtime: writing a shared database,

calling an external service, driving hardware, publishing to an

external topic.

Actuation Gateway

AG

The single component through which actuation is allowed to pass.

Virtual Actuation Buffer

VAB

The per-branch sink that absorbs a shadow branch’s would-be

actuations.

Outcome vector

o

The fixed-schema numeric summary a branch emits at the end of

its horizon.

Utility

U

A scalar score computed from an outcome vector. Higher is better.

Realised utility

U real

k

The utility actually observed in the environment after b0 acted.

Estimated utility

ˆUk(a)

The utility a shadow branch reports for its action a. It is an

estimate, never an observation.

Fidelity gap

εk

| ˆUk(a0) −U real

k

|, measured by the mirror branch.

Regret

Rk

How much better the best alternative appeared to be than what

production actually achieved.

Counterfactual Record

CFR

The immutable record written once per epoch containing the

anchor, all actions, all outcomes, and the regret.

Continuum

—

The property that this whole cycle repeats every epoch,

continuously, inside the live system — rather than as an offline

batch job.

# Chapter 1: Introduction

1.1

One Decision, One Observation

Every control loop in a modern cloud or edge system does the same thing, thousands of times a second:

1. It observes some state.

2. It picks one action.

3. It executes that action.

4. It observes what happened.

Step 4 is the problem. The system observes the consequence of the action it took. It never observes the

consequence of the actions it did not take. The moment the runtime commits, every alternative disappears

without leaving a trace.

Consider a Kubernetes scheduler placing a pod on node A. Ten minutes later, the pod is running with 40 ms

p99 latency. Was that good? The scheduler has no idea. It does not know what the latency would have been

on node B, or node C, or on node A with a different resource limit. Its telemetry contains exactly one sample

from one arm of a choice that had five arms. The same is true of an autoscaler that scaled from 4 replicas to

6, a cache that evicted key X instead of key Y, a load balancer that routed to region EU instead of region US,

and a traffic controller that gave the north–south approach 30 seconds of green instead of 45.

This is not a monitoring gap that better dashboards can close. Prometheus, distributed tracing, and structured

logs are all extremely good at recording what happened. None of them can record what would have happened,

because it did not happen. The information was destroyed at the instant of commitment.

1.2

Why This Limits Scheduling and Control

Any system that learns from its own operation is learning from a biased, one-armed sample of its own decisions.

- The data is on-policy and narrow. A scheduler that always prefers the least-loaded node produces

telemetry only about least-loaded-node placements. It accumulates no evidence about the alternatives it

systematically avoids, so it cannot discover that its heuristic is wrong.

- Attribution is ambiguous. When a metric degrades, the runtime cannot separate "our action was bad"

from "the environment got harder." Both look identical in the time series.

- Improvement requires risk. The standard way to obtain information about an alternative is to try it in

production — canary deployments, A/B tests, exploration in a reinforcement-learning agent. All of these

buy information by paying with real-world consequences. For a low-stakes recommendation ranking, that

trade is fine. For a traffic junction, a power grid dispatcher, or a hospital scheduling system, it is often

unacceptable.

- Offline analysis arrives too late and in the wrong state. Teams do rebuild "what if" analyses later,

in notebooks, from logs. But by then the exact runtime state is gone, the code has changed, and the

analysis runs on a reconstruction rather than on the system itself.

The gap sits between two things we already do well: we can observe production precisely, and we can simulate

alternatives offline. What we do not have is a runtime layer that evaluates alternatives in the live system,

from the live state, on the live inputs, without letting them act.

1.3

The CSC Proposal in One Paragraph

CSC proposes a runtime layer that, at every decision epoch, captures the decision-relevant state once and

forks it into several isolated execution branches. Every branch runs the same decision code and receives the

same live inputs. One branch — the production branch — is permitted to act on the environment. All other

branches are shadow branches: structurally prevented from performing any real-world effect, they compute

alternative actions and evaluate them against a short-horizon local model of the environment. At the end of

each epoch the runtime compares the branches, computes a regret signal, and records the whole comparison

as a counterfactual record. Those records accumulate continuously and feed a policy-improvement loop. The

Introduction

intended result is a system that produces evidence about its unchosen options as a normal part of running,

rather than as a separate offline exercise.

1.4

Where the Novelty Is Claimed — and Where It Is Not

We want to be precise, because overclaiming is the fastest way to lose a reviewer.

Not new. Snapshotting state. Container isolation. Sandboxing with gVisor. Duplicating a stream to multiple

consumers. Running a model of an environment. Computing regret. Learning a policy from logged data. Every

individual mechanism CSC uses is established practice.

What CSC proposes is a specific composition and placement of those mechanisms: making per-decision state

anchoring, multi-branch non-actuating execution, live input replication, and online regret accounting into a

first-class runtime layer that sits underneath the application’s control loop, in a cloud–edge deployment,

and runs continuously rather than as an offline job.

What this document does not claim. That CSC is the first system to do anything. That CSC improves

any particular scheduling policy. That the overhead is acceptable. That shadow outcomes are accurate. Those

are open questions, and Chapter 11 is written specifically to answer them with measurements.

1.5

The Running Example: Junction J1

To keep the document concrete, one example is used from here to the end.

Junction J1. A four-approach signalised intersection. Vehicle detectors report per-lane arrivals. Every 10 seconds

the controller must decide how to allocate the next green interval among the approaches. The candidate actions are

a small discrete set of green-time splits. The objective combines average queue length, average vehicle delay, fairness

across approaches, and a penalty for switching phases too often.

In the prototype, J1 is a software environment service — a queueing model of the junction that consumes actuation

commands and emits detector readings. That is the prototype’s "real world." No physical hardware is involved, and

this document never assumes otherwise.

J1 was chosen because it has the four properties CSC needs to demonstrate anything: a small discrete action

set, a fast decision cadence, a state that is small enough to snapshot cheaply, and an outcome that is measurable

within seconds. Chapter 9 develops the example in full. Earlier chapters refer to it whenever an abstraction

needs grounding.

1.6

Document Roadmap

Introduction

Ch 1-2

Motivation and Problem

Ch 3

CSC Overview

Ch 4

Architecture

Ch 5

Ch 6

Runtime Workflow

Non-Actuating Runtime

Ch 7

Algorithms

Ch 8

Mathematical Model

Ch 9

Smart Traffic Example

Ch 10

Prototype Design

Ch 11

Evaluation Plan

Ch 12

Comparison

Ch 13

Limitations

Ch 14-15

Future Work and Conclusion

Figure 1.1: Document roadmap.

# Chapter 2: Problem Statement

2.1

The Shape of the Loss

The standard runtime control loop can be drawn in three boxes:

Execute a*

Decision function

pick one action

Observe outcome of a* only

a1, a2, ... aN

discarded

Runtime state s

never executed

never observed

Figure 2.1: The conventional runtime control loop. The dashed edge is the missing counterfactual.

The dashed edge is the entire problem. At each decision, the runtime evaluates |A| candidate actions internally

— usually by scoring them with a heuristic — and then throws away every candidate except the winner. The

scores were the decision function’s beliefs. No evidence is ever collected about whether those beliefs were right.

We call this the missing counterfactual problem:

After a runtime commits to action a∗in state s, it can observe U(s, a∗) but it can never observe U(s, a) for any

a ̸= a∗, because the system has already moved on from s and s will not recur exactly.

Two properties make this hard rather than merely inconvenient:

1. Non-recurrence of state. Even in a repetitive system like a traffic junction, no two states are identical.

You cannot "go back and try the other one."

2. Non-decomposability of outcome. The observed outcome is the joint result of the action and everything

the environment did. You cannot subtract the environment out after the fact from a single sample.

2.2

# A Worked Instance at Junction J1

At epoch k, junction J1 is in state sk: 14 vehicles queued north–south, 3 queued east–west, current phase

north–south green with 6 seconds elapsed, and an arrival rate that has been climbing for two minutes.

The controller considers four candidate green-time splits and picks a0 = NS:30/EW:20. Thirty seconds later,

average delay across the junction was 18.4 s.

Is 18.4 s good?

Question the operator wants answered

Can current telemetry answer

it?

What was the delay after we acted?

Yes — 18.4 s.

Was delay better or worse than the last hour?

Yes — trivially, from the time

series.

Would NS:40/EW:10 have been better?

No.

Would NS:20/EW:30 have avoided the east–west spillback that happened at

epoch k + 3?

No.

Was 18.4 s the best achievable, or the worst of four bad options?

No.

Did our controller make a good decision, or did it get a good outcome from a

lucky environment?

No.

Problem Statement

The last row is the important one. Decision quality and outcome quality are different things, and

a single-branch runtime conflates them permanently. A good decision can produce a bad outcome (a truck

broke down); a bad decision can produce a good outcome (traffic thinned out anyway). Without a comparison

point, the runtime cannot separate them, and any learning built on top inherits the confusion.

2.3

Why the Obvious Fixes Are Insufficient

Practitioners already have partial answers. Each solves a different slice of the problem, and none closes it.

Chapter 12 makes a detailed comparison; here we only establish that a gap exists.

Existing approach

What it gives you

Why the gap remains

Better observability

(metrics, traces, logs)

Very precise record of what

happened

Records only the executed branch by construction

Offline simulation /

what-if analysis

Alternatives evaluated at low risk

Runs on a reconstructed state, with reconstructed

inputs, usually hours later and often against a

re-implementation of the logic rather than the logic

itself

Digital twin

A continuously-running parallel

model of the system

Models the system, typically open-loop over long

horizons, and is normally a separate artefact from

the production control path. It answers "how is the

asset behaving" more than "was that specific

decision the best of its alternatives"

Shadow traffic / traffic

mirroring

Real requests replayed to a

non-production service

Compares implementations under the same input,

not decisions from the same anchored state; the

shadow service typically does not fork state, and

outcomes are usually compared for

correctness/performance, not utility and regret

A/B testing, canaries,

interleaving

Genuine comparison between

alternatives

Alternatives must be actually executed on real users

or real assets. Information is bought with real-world

risk, and each unit sees only one arm

Off-policy evaluation in

RL (IPS, doubly-robust)

Estimates of alternative policy

value from logged data

Fundamentally limited by the support of the logged

policy: if the production policy never takes action a

in state region S, no reweighting recovers U(s, a)

there. It is also an offline analysis, not a runtime

capability

Speculative execution

(CPU / query engines)

Multiple paths executed, one

committed

Operates inside a single process or query plan over

microseconds, discards the losing paths without

scoring them, and exists to hide latency — not to

accumulate evidence

The pattern across the table: you can have realism without alternatives (observability, A/B) or alter-

natives without realism (simulation, off-policy estimation). What is missing is a mechanism that gives

alternatives the same live state and the same live inputs as production, at the same instant, without letting

them act.

2.4

Requirements Derived From the Problem

If we want to close that gap, the mechanism has to satisfy the following. These requirements drive the entire

architecture in Chapter 4, and Chapter 11 tests each one.

Requirement

Rationale

Verified by

R1

All branches of an epoch must start from

byte-identical state

Otherwise differences in outcome are

attributable to state, not action

E6 (determinism test)

R2

All branches must receive the same input

records in the same order

Same reason as R1, extended over the

horizon

E6

A bug in a shadow policy must not be

able to control a junction

E3 (containment red

team)

R3

A shadow branch must be incapable of

producing any external effect, not merely

instructed not to

R4

Branch execution must be bounded in time

and resources

The production path must not be

starved by speculation

E2 (scaling), E7 (failure)

R5

Every branch must emit an outcome on a

common schema

Comparison is meaningless otherwise

E4, E5

Problem Statement

Requirement

Rationale

Verified by

R6

The runtime must quantify how wrong its

shadow estimates are

Regret computed from unvalidated

estimates is not evidence

E4 (mirror-branch

fidelity)

R7

The comparison must complete within the

epoch budget

Late evidence cannot inform the next

decision

E2, E7

R8

The loop must run continuously, not as a

batch job

This is what distinguishes CSC from

offline analysis

E5

R9

Failure of any shadow branch must not affect

production

Speculation must be strictly optional

E7

Requirement R6 deserves emphasis, because it is where honest design and wishful design diverge. A shadow

branch does not observe reality; it observes a model of reality. If the design pretends otherwise, everything

downstream — regret, learning, conclusions — is built on sand. CSC therefore treats shadow-outcome error

as a first-class, continuously measured quantity rather than an assumption. Section 3.6 and Chapter 8

describe how.

2.5

The Fundamental Constraint We Cannot Remove

One constraint is worth stating loudly and early, because it shapes every subsequent decision:

You cannot observe the true outcome of an action you did not take. No architecture removes this. CSC

does not remove it either.

What CSC proposes is a specific trade that makes the estimate as cheap and as trustworthy as we can arrange:

1. Anchor on reality every epoch. A shadow branch is never allowed to drift for long. It starts from a

freshly-captured real state and is destroyed after a short horizon H. Error accumulates within an epoch

but does not compound across epochs.

2. Use the real inputs, not generated ones. Exogenous events (vehicle arrivals, request arrivals) come

from the live stream, so the shadow world differs from the real world only in the consequences of the action,

not in the environment.

3. Use the real decision code.

The shadow branch runs the same container image as production, so

implementation differences are not a confound.

4. Measure the residual error continuously. The mirror branch bm runs the production action inside

the shadow world. Since we also observe the real outcome of that same action, the difference is a direct,

per-epoch measurement of shadow inaccuracy.

The result is not a true counterfactual. It is a short-horizon, reality-anchored, continuously-calibrated

counterfactual estimate, and the architecture is designed so that its error is visible rather than hidden.

That distinction is the intellectual core of this project, and it should appear in the eventual paper’s abstract.

# Chapter 3: CSC Overview

3.1

The Core Loop

CSC replaces the three-box loop of Section 2.1 with the following.

Environment

Junction J1

live inputs

State Capture

anchor state s_k

Branch Fork

N+2 identical starts

Production branch b0

Mirror branch bm

Shadow branch b1

Shadow branch b2

Shadow branch bN

action a0

action a0 in shadow world

action a1

action a2

action aN

allowed

blocked

blocked

blocked

blocked

Actuation Gateway

Virtual Actuation Buffers

Outcome Comparison Engine

utilities, regret, fidelity

new policy version

Knowledge Store

Counterfactual Records

Learning Engine

Policy Updater

Figure 3.1: The CSC core loop: capture, fork, replicate, execute, block, compare, learn.

Read it as seven verbs, executed once per epoch:

1. Capture the state.

2. Fork it into a branch set.

3. Replicate the live inputs into every branch.

4. Execute all branches in parallel.

5. Block every branch except production from reaching the environment.

6. Compare the outcomes and compute regret.

7. Learn from the accumulated comparisons.

3.2

Production Branch

The production branch b0 is an ordinary control-loop worker. It reads state, consults the current policy, chooses

an action, and actuates. If you removed everything else from the diagram, b0 alone would be a conventional

adaptive traffic controller.

Two CSC-specific properties apply to it:

- Its actuation is routed through the Actuation Gateway, which stamps and authorises it. This is the only

place in the system where an effect can leave.

- Its realised outcome — the real, observed telemetry over the next H ticks — is the ground truth against

which everything else is judged.

CSC Overview

Critically, b0 must be able to run correctly with the rest of CSC switched off. Shadow execution is strictly

additive.

If the Branch Manager crashes, no shadow branch is created, no comparison happens, and the

junction keeps being controlled. This is design requirement R9 and it is not negotiable.

3.3

Shadow Branches

A shadow branch is a pod running the same container image as production, started from the same anchor

state, fed the same input records, but launched with:

- a different candidate action to evaluate,

- a branch role of SHADOW in its identity token,

- a runtime sandbox (gVisor) and a network policy that make actuation structurally impossible,

- a hard wall-clock and resource budget,

- an in-process Shadow Environment Model that tells it what the world does in response to its action.

That last item is the part most people miss on first reading, so it is worth stating plainly. In production,

the worker acts and the real junction responds. In a shadow branch, the worker acts and nothing responds,

because the branch is not connected to the junction. Something has to close the loop, or the shadow branch

produces no outcome at all. That something is the Shadow Environment Model (SEM): a small, fast, local

model that advances the anchored state given (a) the shadow action and (b) the real exogenous inputs arriving

on the replicated stream.

Production branch b0

Actuation Gateway

Decision worker

Real environment

real response

Shadow branch bi

Virtual Actuation Buffer

Replicated live input stream

Decision worker

exogenous events only

same image

Shadow Environment Model

modelled response

Figure 3.2: Loop closure differs only after actuation: production is closed by the real environment, a shadow branch

by the Shadow Environment Model.

The SEM is deliberately small. It does not model the city; it models one junction over a few tens of seconds,

starting from a known state, with the arrivals handed to it. Chapter 9 gives the concrete J1 model, which is

a per-lane queue update that fits comfortably on one page.

Two design rules keep the SEM honest:

- Rule S1 — Exogenous inputs are never modelled. Vehicle arrivals come from the replicated real

stream, not from a generator. The model only computes the effect of the action on queues and departures.

- Rule S2 — Horizon is short and fixed. The branch runs H ticks and dies. It is never allowed to

accumulate error over minutes.

3.4

State Capture and Runtime Branching

"Fork" is a loaded word, so let us define it precisely for CSC.

CSC does not propose process-level forking, memory-image cloning, or CRIU-style checkpoint/restore for

the prototype.

Those are legitimate options (Chapter 14 lists them as future work), but they are fragile,

platform-specific, and a poor use of a student semester.

Instead, CSC uses explicit state serialisation with a declared state schema:

- The application declares which variables constitute its decision-relevant state.

CSC Overview

- The State Capture Engine serialises exactly those variables into an immutable, content-addressed blob sk.

- Branch workers start with an empty runtime and hydrate themselves from sk.

Property

Explicit schema capture (chosen)

Process/memory cloning (rejected

for prototype)

Implementation effort

Low — a struct and a codec

High — CRIU, namespaces, page tables

Portability

Works on any node, any language

Sensitive to kernel, arch, runtime

Capture latency

Small, proportional to declared state

Proportional to full RSS

Correctness risk

Missing a field silently breaks fidelity

Cloned FDs, sockets, timers all

misbehave

Debuggability

State is readable JSON/CBOR

Opaque

Suitability for a semester

Good

Poor

The trade-offis real and should be written up honestly: explicit capture is only as complete as the declared

schema. If the worker keeps hidden state (a cached counter, a random-number-generator seed, a warm con-

nection pool), branches will diverge for reasons unrelated to the action. Chapter 5 defines the discipline that

mitigates this — a state completeness contract and a determinism test (experiment E6) that fails the build if

two branches given the same action produce different outcomes.

3.5

Non-Actuating Execution

The single property that makes the whole idea acceptable to deploy is this: a shadow branch must be

unable to affect the world even if its code is wrong, malicious, or compromised.

CSC layers five independent defences, described fully in Chapter 6:

Layer

Mechanism

Fails safe if. . .

L1

Role-aware client SDK routes actuation to VAB

. . . the developer used the SDK

L2

Actuation Gateway rejects tokens whose role is not PRODUCTION

. . . the branch reached the gateway at

all

L3

Kubernetes NetworkPolicy denies egress to the environment

service

. . . the branch bypassed the SDK

L4

Shadow ServiceAccount holds no credentials for any actuating

system

. . . the branch found an alternate route

L5

gVisor sandbox + read-only rootfs + dropped capabilities +

seccomp

. . . the branch tried to escape the

container

The important architectural point is that L2 is a chokepoint, not a policy. There is exactly one code

path from the CSC runtime to the environment, it is small enough to audit in an afternoon, and it fails closed.

Everything else is depth.

3.6

Comparison, Regret, and Fidelity

At the end of epoch k, the Outcome Comparison Engine holds:

- one realised outcome from production, oreal

k

,

- one estimated outcome from the mirror branch for the same action, ˆok(a0),

- N estimated outcomes from shadow branches, ˆok(a1) . . . ˆok(aN).

From these it computes three numbers:

U real

k

= U

 

oreal

k



,

ˆUk(ai) = U(ˆok(ai))

εk =

ˆUk(a0) −U real

k

(fidelity gap, from the mirror branch)



(fidelity-discounted regret)

˜Rk = max



0,

max

i∈{1..N}

ˆUk(ai) −εk −U real

k

CSC Overview

The subtraction of εk is the design’s conservatism knob. If the shadow world is currently a poor predictor — say

the mirror branch is offby 4 utility units — then a shadow branch claiming a 2-unit improvement is reported

as zero regret, because the claim is inside the noise floor. Regret is only recognised when an alternative beats

production by more than the model’s own demonstrated error. This is a deliberately pessimistic estimator

and it is what makes the resulting numbers defensible in a paper.

Realised utility

U_real from b0

Fidelity gap

epsilon

Comparison

Mirror utility

Fidelity-discounted regret

Counterfactual Record

U_hat a0 from bm

Best alternative

argmax

Shadow utilities

U_hat a1..aN

Figure 3.3: Inputs to the comparison step and the resulting Counterfactual Record.

3.7

Learning

Counterfactual Records accumulate at one per epoch per site. Because each record contains multiple (state,

action, estimated-utility) triples rather than the single one a conventional log provides, the dataset grows in a

shape that supervised learning can use directly.

The prototype’s default learner is deliberately simple: a small utility model ˆUϕ(s, a) trained by regression on

CFR entries, with the policy defined as a softmax over predicted utility plus an exploration term. A policy-

gradient variant is described in Chapter 7 as an optional extension. The choice matters less than the plumbing;

CSC’s claim is about producing the data, not about inventing a learning algorithm.

Two safety mechanisms sit between the learner and production:

1. Shadow-first promotion.

A newly trained policy is deployed only to shadow branches for a config-

ured number of epochs. It becomes eligible for production only if its shadow-estimated utility beats the

incumbent by more than the current fidelity gap.

2. Promotion audit. Periodically (with probability ρaudit, default 5 %), the runtime promotes a shadow

action to production for one epoch.

This yields a real observation for an action the policy would not

normally take, which both calibrates the SEM in unexplored regions and provides genuinely off-policy

ground truth. It is the one place where CSC deliberately spends real-world risk to buy information, and

its rate is a tunable, auditable parameter.

3.8

The "Continuum" in the Name

The word matters.

CSC is not a snapshot mechanism that you invoke when you want an analysis.

The

intended behaviour is:

- Branching happens every epoch, in the live system, whether or not anyone is looking.

- Each epoch’s branches are discarded at the end of the horizon; nothing long-lived diverges.

- The state anchor re-synchronises with reality every epoch, so the shadow world never drifts.

- The output is a continuous stream of counterfactual records, not a report.

The continuum is the sequence of overlapping short-lived shadow worlds that collectively track reality without

ever being allowed to become reality.

3.9

What CSC Is Not

Because every one of these confusions has come up in review, they are addressed directly.

CSC Overview

Idle

epoch tick

Capturing

anchor stored

Planning

candidate set chosen

Provisioning

branches hydrated

Executing

shadow branches destroyed

horizon H elapsed

Collecting

outcomes received or

budget exceeded

deadline

Comparing

regret computed

Recording

Aborting

shadows cancelled,

CFR written

production unaffected

Reaping

Figure 3.4: Epoch state machine.

CSC Overview

CSC is often mistaken for. . .

The actual difference

A digital twin

A twin is a persistent parallel model of an asset or system, usually long-running,

usually maintained as a separate artefact, and usually answering "what is the

state/health of the thing." CSC creates many short-lived branches of the

decision path itself, running the production code, destroyed every epoch, to

answer "which of these specific alternatives looked better." A digital twin could

serve as one implementation of CSC’s Shadow Environment Model — that is a

natural integration, not an equivalence.

Shadow traffic / dark launch

Traffic mirroring duplicates requests to a second deployment to compare

implementations for correctness or latency. It does not anchor state, does not

vary the decision, does not compute utility or regret, and the shadow service

usually still has real dependencies. CSC duplicates inputs and forks state and

varies the action and forbids all effects.

# A Kubernetes scheduler

CSC schedules nothing in the Kubernetes sense. It is a layer above the workload

that happens to use Kubernetes to place branch pods. A Kubernetes scheduler

could be a client of CSC — Chapter 14 discusses that — but CSC does not

replace kube-scheduler.

A reinforcement-learning

algorithm

CSC does not propose a learning rule. It proposes a mechanism that produces

multi-armed, state-anchored training data. Any learner — bandit, policy

gradient, plain regression, or a hand-written heuristic tuner — can consume it.

The learner is a pluggable component, not the contribution.

A simulator

A simulator generates its own inputs and runs detached from production. CSC’s

shadow branches run inside the production runtime, on production’s own live

inputs, from production’s own captured state, in production’s own container

image. The SEM inside a branch is admittedly simulation-like, but it is one

bounded component, re-anchored every epoch, and its error is measured rather

than assumed.

A digital shadow

A digital shadow is a one-way data flow from a physical asset to a model. CSC’s

branches are executions of control logic, not passive reflections, and their entire

purpose is to explore alternatives that the physical asset never experienced.

The constructive framing to use in conversation: CSC is a runtime layer, and these are technologies

it integrates with. A digital twin can back the SEM. Traffic mirroring infrastructure can implement input

replication. Kubernetes places the branches. An RL library trains the policy. CSC is the thing that ties them

into a per-decision counterfactual loop.

3.10

Where CSC Sits in a System

The layering is the point of the diagram: CSC introduces one new horizontal layer.

It does not modify

Kubernetes, does not modify the kernel, and does not require the application to be rewritten — only to

declare its state schema and route its actuations through the gateway. Chapter 10 quantifies exactly what an

application must implement to become CSC-enabled (three functions and one config file).

CSC Overview

CSC runtime layer -- proposed

Application layer

Decision policy

Actuation Gateway

traffic control logic

Environment

Junction J1 environment

State Capture

service

sensor inputs

Platform layer -- existing

K3s / Kubernetes

gVisor runtime class

NATS or Kafka

Branch Manager

Input Replication

Outcome Comparison

Learning and Policy Update

Redis

Prometheus and Grafana

Figure 3.5: Where CSC sits: one new horizontal layer between the application and the platform.

# Chapter 4: CSC Architecture

4.1

Architectural Principles

Five principles constrain every component decision that follows. When a design question comes up during

implementation that this document does not answer, resolve it with these.

#

Principle

Consequence

P1

Production is never blocked by

speculation.

Shadow work runs on a separate resource pool, on a best-effort QoS

class, behind a deadline. Any shadow failure is logged and ignored.

P2

One egress, always.

There is exactly one component that can produce an external effect.

Every other component is provably incapable of it.

P3

Identical by construction,

different by intent.

Branches differ in exactly one variable — the candidate action. Same

image, same anchor, same inputs, same config, same seed.

P4

Estimates are labelled as

estimates.

Every value in the system carries its provenance (REALISED vs

ESTIMATED) end-to-end, into the CFR and into the dashboards.

P5

Everything is bounded.

Branch count, horizon, memory, wall-clock, retained records — all have

configured ceilings with metrics that fire when they are hit.

4.2

Component Map

4.3

Component Responsibility Summary

#

Component

Language

Responsibility

Must NOT do

Depend on wall-clock skew

between nodes

C1

Epoch Clock

Go

Emit monotonically numbered epoch

ticks; own the authoritative epoch

number

Interpret the state

semantically

C2

State Capture Engine

(SCE)

Go

Serialise the declared state schema into

an immutable anchor; publish anchor

Execute decision logic itself

C3

Multi-Branch Scheduler

(MBS)

Go

Decide the candidate set, allocate

branches within budget, create/destroy

branch pods

C4

Branch Ledger (BL)

Go + Redis

Track every branch’s identity, role,

action, status, deadline

Hold outcome data long-term

Reorder, filter, or transform

payloads

C5

Synchronization Layer

(SYNC)

Go

Fan out epoch-tagged input records

identically to all branches; guarantee

order

Reach the network beyond its

allowed set

C6

Shadow Runtime (SR)

Go + Python

The sandboxed execution environment

for a branch: hydrate, run worker, host

the SEM, emit outcome

C7

Actuation Gateway (AG)

Go

Authorise and forward exactly one

branch’s actuations per epoch; audit

everything else

Modify branch outputs

Contain business logic or

retries that could

double-actuate

C8

Outcome Comparison

Engine (OCE)

Go

Barrier on branch outcomes, compute

utility, fidelity gap and regret, emit

CFR

C9

Knowledge Store (KS)

Redis + files

Persist anchors, CFRs, policy versions

Be on the production critical

path

C10

Learning Engine (LE)

Python +

PyTorch

Train the utility model / policy from

CFRs

Write directly to the active

policy pointer

C11

Policy Updater (PU)

Python

Gate, version, canary and publish

policies

Bypass the shadow-first

promotion rule

C12

Observability

Prometheus/Grafana

Scrape, store, visualise, alert

—

Components C1–C8 form the CSC runtime layer. C9–C11 form the learning plane, which is deliberately

asynchronous and offthe critical path so that a stalled trainer cannot delay a decision.

CSC Architecture

Control Plane -- Go

Epoch Clock

State Capture Engine

State and Storage

Knowledge Store

Redis plus object store

Learning Plane -- Python

Learning Engine

Policy Updater

Policy Registry

Multi-Branch Scheduler

Data Plane -- per branch

Branch Ledger

Production Branch Pod

Observability

Prometheus

Actuation Gateway

Grafana

Environment Service

Junction J1

sensor stream

Synchronization Layer

realised telemetry

Mirror Branch Pod

Shadow Branch Pods x N

Message Bus

Virtual Actuation Buffers

NATS or Kafka

Outcome Comparison Engine

Figure 4.1: CSC component map.

CSC Architecture

4.4

Epoch Clock (C1)

A trivially small component with an outsized correctness role: it defines what "the same moment" means for

every other component.

- Emits a tick every Tepoch (default 10 s for J1) on subject csc.epoch.tick.

- The tick carries {site_id, epoch, tick_monotonic_ns, deadline_ns}.

- The epoch number is the only correlation key used across the system. Nothing joins on timestamps.

- On restart it reads the last epoch from Redis and continues; it never reuses a number.

Design note: making the epoch number authoritative (rather than deriving alignment from timestamps)

sidesteps clock-skew problems between the control node and edge nodes entirely. Skew still matters for mea-

suring latency, but not for correctness of grouping.

4.5

State Capture Engine (C2)

4.5.1

The State Schema Contract

# A CSC-enabled application declares its decision-relevant state once, in a schema file. For J1:

# configs/state_schema.j1.yaml

site_id: J1

version: 3

fields:

- name: queue_len

# vehicles waiting, per lane

type: int32[8]

source: detector_aggregator

required: true

- name: phase_id

# index of the active signal phase

type: int32

source: controller

required: true

- name: phase_elapsed_s

type: float32

source: controller

required: true

- name: arrival_rate_ewma

# per approach, vehicles/s

type: float32[4]

source: detector_aggregator

required: true

- name: last_switch_epoch

type: int64

source: controller

required: true

- name: rng_seed

# so branches are reproducible

type: uint64

source: runtime

required: true

integrity:

hash: sha256

max_bytes: 65536

capture_budget_ms: 15

Three rules make this contract enforceable rather than aspirational:

1. Everything the worker reads must be in the schema or in the input stream. Nothing else. The

worker container has no other data sources — no local files, no direct database, no ambient clock reads

(the tick supplies time).

2. **rng_seed is captured, not generated.** Two branches with the same action must therefore behave identi-

cally. This is what experiment E6 tests.

3. Capture must fit the budget.

If serialisation exceeds capture_budget_ms, the epoch proceeds with

production only and increments csc_capture_budget_exceeded_total. Production is never delayed to ac-

commodate branching (principle P1).

4.5.2

Capture Mechanics

The "freeze and read" step is a short critical section (a read lock over the state holder) so that the captured

snapshot is internally consistent — you must never capture queue_len from tick k and phase_elapsed_s from

tick k + 1. For J1’s ~200-byte state this lock is held for microseconds.

CSC Architecture

Multi-Branch Scheduler

Knowledge Store

State Sources

State Capture Engine

Epoch Clock

tick(epoch k, deadline)

freeze and read declared fields

field values

encode CBOR, compute sha256

PUT anchor(k) -> content-addressed blob

anchor_id

AnchorReady(epoch k, anchor_id, hash)

If deadline missed, SCE emits AnchorSkipped

and MBS runs production only

Multi-Branch Scheduler

Knowledge Store

State Sources

State Capture Engine

Epoch Clock

Figure 4.2: State capture sequence.

Anchors are content-addressed: the key is the SHA-256 of the encoded payload. Two epochs with identical

state share one blob. That is a small storage win and a large debugging win — an identical hash across two

epochs immediately explains an identical outcome.

Anchor property

Value

Encoding

CBOR (compact, typed, streaming-friendly)

Key

csc:anchor:{site}:{sha256}

Index

csc:epoch:{site}:{k}:anchor -> sha256

TTL

24 h in Redis; permanent copy written to the object/file store for records referenced by a

CFR

Size target for J1

< 1 KB

4.6

Multi-Branch Scheduler (C3)

The MBS answers three questions each epoch: which actions to evaluate, how many branches we can afford,

and where to put them.

4.6.1

Candidate Set Selection

Evaluating every action is usually impossible and always wasteful. The MBS builds a candidate set of size N

from three sources:

Slot type

Count (J1

default)

Purpose

Production action a0

The action that will actually be taken

Mirror a0

Fidelity measurement (Chapter 8)

Policy top-k alternatives

The runner-up actions the policy ranked highest — where regret is

most likely to be real

Exploration slot

Sampled from under-visited actions, weighted by inverse visit count

— this is what keeps the utility model from collapsing onto the

current policy

Adversarial/probe slot

0–1

Optional: the action the current utility model predicts is worst, used

to validate that the model can still tell good from bad

Default branch budget for the prototype is N = 4 shadow branches (2 alternatives, 1 exploration, 1 mirror)

plus production — five executions per epoch. Experiment E2 sweeps N ∈{0, 1, 2, 4, 8}.

CSC Architecture

4.6.2

Budget Enforcement

The number of branches is not a constant; it is the minimum of several ceilings, recomputed every epoch:

%

!

$

Tepoch −Tcapture −Tcompare



,

Mavail −Mreserve



,

Nmax,

ρ · Cavail

· Ppar

Nk = min

cbranch

mbranch

T p95

branch

where ρ is the fraction of node CPU the operator permits speculation to use (default 0.35), cbranch and mbranch

are the measured per-branch CPU/memory costs from the last 100 epochs, and Ppar is the number of branch

slots that can run concurrently. Chapter 8 revisits this as the overhead model; the practical point is that the

scheduler degrades the number of shadows rather than degrading production.

Epoch tick

Anchor ready

within budget?

yes

Compute N_k from budgets

no

N_k >= 1?

no

yes

Run production only

Build candidate set:

increment skip counter

prod, mirror, top-k, explore

Warm pods available?

yes

no

Bind warm pods to branches

Create pods, mark

COLD_START

Register in Branch Ledger

Signal SYNC to open branch

subjects

Branches execute

Figure 4.3: Branch planning and budget enforcement.

4.6.3

Warm Pool

Creating five pods every 10 seconds is not viable — pod startup dominates the epoch budget. The MBS

therefore maintains a warm pool of idle shadow-runtime pods, pre-scheduled and pre-pulled, waiting on a

hydration message.

Parameter

Default

Note

Pool size

Nmax + 2

Two spares absorb reaping latency

CSC Architecture

Parameter

Default

Note

Pod lifetime

200 epochs

Recycled to bound memory drift

Hydration

Anchor pushed over the branch

subject

No pod restart per epoch

Cold-start fallback

Create on demand, mark branch

COLD_START

Excluded from latency stats, counted

separately

A warm pod is not stateful across epochs: hydration resets the worker’s state completely from the anchor.

Recycling every 200 epochs is purely defensive against leaks in the Python worker.

4.6.4

Placement

Placement uses ordinary Kubernetes primitives. No custom scheduler is written.

Branch role

Node target

QoS

RuntimeClass

Production

Edge node co-located with the environment interface,

pinned via nodeSelector

Guaranteed (requests =

limits)

runc

Burstable, low

priorityClass

gvisor

Mirror / Shadow

Any node with the csc.io/shadow=true label;

anti-affinity away from the production node when

capacity allows

Putting shadows on a different node than production is the cleanest way to satisfy P1 on a small cluster. When

the cluster has only one worker, shadows still run but with a hard CPU limit and a low-priority class so the

kubelet evicts them first under pressure. Experiment E8 measures exactly this case on a constrained node.

4.7

Branch Ledger (C4)

A small Redis-backed registry that is the single source of truth for "what branches exist right now."

Field

Type

Notes

branch_id

string

{site}-{epoch}-{role}-{idx} — human-readable on purpose

epoch

int64

Join key for everything

role

enum

PRODUCTION \{}

action

object

The candidate action being evaluated

anchor_hash

string

Must match what the pod reports after hydration

state

enum

As per the state machine above

pod

string

Kubernetes pod name

deadline_ns

int64

Absolute; enforced by both MBS and the pod itself

token_id

string

Reference to the branch identity token (Chapter 6)

The ledger is intentionally ephemeral (TTL 1 hour). Long-lived facts live in the CFR. This keeps the hot

path small and makes Redis memory bounded regardless of how long the system runs.

4.8

Synchronization Layer (C5)

SYNC is the component most likely to be underestimated. Getting "the same inputs, in the same order, to

every branch" right is the difference between a comparison and a coincidence.

4.8.1

Fan-Out Model

Key decisions:

Decision

Choice

Why

Ordering is decided once, centrally;

branches cannot disagree about order

Sequencing

A single Ingest and Sequencer assigns a

monotonic seq and an epoch tag to every input

record before fan-out

Delivery

One logical stream per branch (NATS subject /

Kafka partition / Redis Stream key)

Independent consumer progress; a slow

shadow cannot back-pressure production

CSC Architecture

Decision

Choice

Why

Principle P1 — a shadow branch is never

allowed to slow the pipeline

Replay source

The Epoch Input Log is retained for the

epoch’s horizon

A late-starting or restarted branch can

replay from seq 0 and still see the

identical sequence

Back-pressure

Production consumer has an unbounded-ish

buffer; shadow consumers have bounded buffers

and are dropped on overflow

Bounded memory; visible metric

Late records

Records arriving with an epoch tag older than

the current epoch minus 1 are discarded and

counted

4.8.2

Replication Skew

The measurable property SYNC must deliver is replication skew: the difference in wall-clock arrival time of

input record j across branches.

σj = max

b∈Bk tb,j −min

b∈Bk tb,j

Skew does not break correctness — branches are driven by seq, not by wall-clock — but large skew delays the

barrier and eats the epoch budget. It is a headline metric in experiment E6, reported as p50/p95/p99.

An important simplification the design exploits: branch workers are logically clocked by input sequence,

not by time. A branch advances its internal tick when it consumes the next input record, so a branch that

receives records 40 ms late produces the same outcome, just later. This decouples correctness from network

timing and is a deliberate design choice.

4.9

Shadow Runtime (C6)

The Shadow Runtime is the per-branch execution environment. Every branch pod — production, mirror,

shadow — runs the same three-part structure, differing only in configuration.

Sub-component

Role in production branch

Role in shadow branch

Hydrator

Loads anchor, verifies hash, resets

worker state

Identical

Input consumer

Reads csc.in.b.{id} in seq order

Identical

Policy inference

Chooses the action

Forced to the assigned candidate action for the

first decision, then free to act within the horizon

Egress shim

Forwards actuation to AG with a

PRODUCTION token

Writes actuation to VAB; never attempts AG

Shadow Environment

Model

Disabled — the real environment

closes the loop

Enabled — consumes VAB entries plus exogenous

inputs, produces the next observation

Outcome emitter

Publishes provenance=REALISED

outcome

Publishes provenance=ESTIMATED outcome

Two subtleties worth calling out during implementation:

1. The first decision is forced, the rest are free. A shadow branch exists to answer "what if we had

chosen ai at epoch k." Within the horizon it may make follow-up decisions using the normal policy, because

that reflects what would really have happened. Only the epoch-k decision is pinned. This is a configurable

mode (pin=first vs pin=all); pin=first is the default and the one used for regret.

2. The SEM lives inside the worker container, not the sidecar. It is application-specific — a traffic

model for J1, something else for another domain — so it belongs with the application, while the sidecar

stays generic. This keeps the CSC runtime domain-agnostic, which matters if the team wants a second use

case later.

4.10

Actuation Gateway (C7)

The gateway is small on purpose. Target: under 400 lines of Go, reviewable in one sitting, with 100 %

branch coverage in tests.

CSC Architecture

PLANNED

warm pod assigned

BOUND

budget denied

hydration failed

anchor applied and verified

HYDRATED

ABORTED

first input consumed

RUNNING

deadline passed

outcome published

deadline passedcrash or panic

REPORTED

TIMEOUT

FAULTED

resources released

REAPED

Figure 4.4: Branch lifecycle state machine.

csc.in.b.{prod}

Production pod

csc.in.b.{mirror}

Mirror pod

csc.inputs.raw

assign seq, tag epoch

Environment Service

Ingest and Sequencer

Epoch Input Log

Redis Stream per epoch

csc.in.b.{shadow-1}

Shadow pod 1

csc.in.b.{shadow-N}

Shadow pod N

Figure 4.5: Input fan-out model with bounded shadow queues.

CSC Architecture

Branch Pod

csc-runtime sidecar -- Go

Hydrator

Input consumer

decision-worker container -- Python

Policy inference

PyTorch

Egress shim

routes to AG or VAB

Outcome emitter

shadow only

PRODUCTION role only

SHADOW / MIRROR role

Shadow Environment Model

disabled in production

Actuation Gateway

Virtual Actuation Buffer

csc.outcomes

Figure 4.6: Internal structure of a branch pod.

Audit and Metrics

Environment Service

Epoch Interlock

Token Verifier

Actuation Gateway

Branch pod

POST /v1/actuate (body, X-CSC-Branch-Token)

verify signature, expiry, role

alt

[role != PRODUCTION or token invalid]

DENY

violation event, blocked_total++

403 ACTUATION_DENIED

[role == PRODUCTION]

ALLOW

claim(epoch k)

alt

[epoch already claimed]

CONFLICT

double_actuation_total++

409 EPOCH_ALREADY_ACTUATED

[first claim]

OK

apply(action)

ack

actuated_total++, record

200 OK

Audit and Metrics

Environment Service

Epoch Interlock

Token Verifier

Actuation Gateway

Branch pod

Figure 4.7: Actuation Gateway authorisation sequence, including the epoch interlock.

CSC Architecture

Guarantee

Mechanism

Only production can

actuate

Ed25519-signed branch token carrying {branch_id, epoch, role, exp}; role must

be PRODUCTION

At most one actuation per

epoch

Epoch interlock: an atomic SETNX csc:actuated:{site}:{epoch} in Redis

No replay

Token exp is the epoch deadline; expired tokens are rejected

Full audit

Every request — allowed or denied — is written to csc.events.actuation with the

branch ID and outcome

Fails closed

Any error in verification, interlock, or configuration results in denial, not in a

permissive fallback

The epoch interlock is worth dwelling on. It converts "we hope only one branch actuates" into "the system

can only actuate once per epoch, regardless of what any branch does." Even a catastrophic bug that hands a

production token to a shadow branch results in one actuation, not N. That is a meaningful safety property

and it costs one Redis operation.

4.11

Virtual Actuation Buffer

The VAB is the sink that makes a shadow branch’s actions observable without making them real.

Property

Design

Storage

Redis Stream, key csc:vab:{branch_id}

Entry

{seq, ts, action_type, payload, would_have_targeted}

Lifetime

Deleted at branch reap; contents summarised into the outcome first

Reader

The branch’s own SEM (to close the loop) and the OCE (to record what the branch tried to do)

Size cap

1024 entries per branch; overflow marks the branch FAULTED

The would_have_targeted field is a small feature with a large debugging payoff: it records the URL/topic/device

the branch would have contacted. During the containment red-team exercise (experiment E3) this is how the

team demonstrates "the branch genuinely tried to write the junction, and here is the record of it being stopped."

4.12

Outcome Comparison Engine (C8)

4.12.1

The Outcome Vector

Every branch emits exactly one outcome message per epoch, on a fixed schema.

{

"site_id": "J1",

"epoch": 10423,

"branch_id": "J1-10423-SHADOW-2",

"role": "SHADOW",

"action": { "ns_green_s": 40, "ew_green_s": 20 },

"provenance": "ESTIMATED",

"horizon_ticks": 6,

"anchor_hash": "sha256:1f9c...",

"policy_version": "v17",

"metrics": {

"mean_queue_len": 9.4,

"mean_delay_s": 15.1,

"max_queue_len": 21,

"throughput_veh": 47,

"fairness_gini": 0.18,

"phase_switches": 1

},

"runtime": {

"cpu_ms": 182,

"peak_rss_mb": 96,

"hydrate_ms": 7,

"inputs_consumed": 6,

"vab_entries": 3

},

"status": "REPORTED"

}

CSC Architecture

The provenance field is P4 made concrete: a REALISED outcome came from the environment, an ESTIMATED one

came from a model. Downstream code must never mix them without accounting for the difference, and the

dashboards colour them differently.

4.12.2

The Barrier

Knowledge Store

Environment telemetry

Comparison Engine

csc.outcomes

Branches

outcome (per branch, as each finishes)

deliver

realised telemetry for epoch k

wait until (all expected received) OR (barrier deadline)

compute U for each outcome

epsilon = |U_hat(a0) - U_real| (needs mirror)

R = max(0, max_i U_hat(a_i) - epsilon - U_real)

write Counterfactual Record

publish csc.cfr

Knowledge Store

Environment telemetry

Comparison Engine

csc.outcomes

Branches

Figure 4.8: Outcome barrier and comparison sequence.

Barrier rules:

Situation

Behaviour

All expected outcomes arrive

Normal path

Barrier deadline reached with ≥1 shadow +

production + mirror

Compute over what arrived; mark CFR PARTIAL; record which

branches were missing

Mirror branch missing

Fidelity gap unavailable — fall back to the EWMA of recent ε; mark

record EPSILON_ESTIMATED

Production outcome missing

No CFR is written. Without ground truth there is nothing to

compare against

All shadows missing

Write a PRODUCTION_ONLY record so the epoch is still accounted for

The barrier deadline is Tepoch · 0.8 from the tick, leaving headroom for the CFR write before the next epoch

begins.

4.12.3

Utility Function Plug-in

Utility is domain-specific and therefore configuration, not code:

# configs/utility.j1.yaml

utility:

form: weighted_linear_negative

# U = -(sum over terms of weight * metric / normalize_by); higher U is better

terms:

- {metric: mean_delay_s,

weight: 1.00, normalize_by: 60.0}

- {metric: mean_queue_len, weight: 0.50, normalize_by: 30.0}

- {metric: fairness_gini,

weight: 0.75, normalize_by: 1.0}

- {metric: phase_switches, weight: 0.20, normalize_by: 4.0}

clamp: [-5.0, 0.0]

Keeping the weights in config means the evaluation chapter can run a utility-sensitivity study (experiment

E5c) by changing a file, not by rebuilding images.

CSC Architecture

4.13

Knowledge Store (C9)

Two tiers, chosen for different access patterns:

Tier

Technology

Holds

Access pattern

Low-latency, on the epoch

path

Hot

Redis

Anchors (24 h TTL), branch ledger,

VABs, active policy pointer, recent

CFRs

All CFRs, all referenced anchors, all

policy versions

Batch scans by the Learning

Engine

Cold

Append-only Parquet/JSONL files on a

PVC (or MinIO if the team wants object

semantics)

The Counterfactual Record schema is the project’s most important data structure — it is what a future paper

analyses:

CFR

string

cfr_id

PK

int64

epoch

string

site_id

float

u_real

float

u_mirror

float

epsilon

float

regret_raw

float

regret_discounted

string

best_alt_action

string

record_status

references

produced under

ANCHOR

POLICY_VERSION

string

anchor_hash

PK

string

version

PK

int64

epoch

string

trained_from

contains

string

site_id

int64

created_epoch

bytes

payload_cbor

json

hyperparams

int32

size_bytes

string

promotion_status

starts

BRANCH_RESULT

string

branch_id

PK

string

role

json

action

string

provenance

json

metrics

float

utility

string

status

int32

cpu_ms

Figure 4.9: Knowledge Store entity model.

4.14

Learning Engine and Policy Updater (C10, C11)

Both live offthe critical path. The Learning Engine wakes on a timer (default every 500 epochs, roughly 80

minutes at a 10 s cadence), scans new CFRs, retrains, and writes a candidate policy version. The Policy

Updater then applies the promotion gate.

CSC Architecture

Reject, keep vN,

no

record reason

Filter:

Build dataset

Train utility model

Validate on held-out

Publish candidate policy

Shadow-only deployment

gain of vN+1 over vN

New CFRs

(s, a, U_hat, provenance,

yes

Auto-rollback to vN

U_phi(s,a)

REALISED outcomes

vN+1

for W epochs

exceeds epsilon_ewma ?

drop PARTIAL,

drop epsilon > threshold

weight)

Promote to production

Realised utility

yes

with canary window

degrades over C epochs?

no

vN+1 becomes incumbent

Figure 4.10: Learning and policy-promotion pipeline.

Sample-weighting deserves a note: REALISED samples (from production and from promotion audits) are weighted

higher than ESTIMATED samples, and estimated samples are down-weighted in proportion to the fidelity gap

recorded for their epoch:





wk(a) =



if provenance = REALISED

1 + λ εk

if provenance = ESTIMATED

with λ default 2.0. When the shadow world is accurate, estimated samples count almost fully; when it is not,

they fade out automatically. This is a one-line change in the training loop and it is the main protection against

the model learning from its own errors (Chapter 13, limitation L7).

4.15

Deployment View

Node: csc-control (laptop / VM, 4 vCPU, 8 GB)

sync-replicator

Node: csc-edge-1 (SBC or VM, 4 vCPU, 4 GB)

production branch pod (runc)

actuation-gateway

Node: csc-shadow-1 (VM, 4-8 vCPU, 8 GB)

warm pool: shadow branch

environment-service

state-capture

pods (gvisor)

mirror branch pod (gvisor)

(Junction J1)

sensor stream

nats-jetstream

learning-engine (CronJob)

comparison-engine

epoch-clock

branch-manager

redis

prometheus

grafana

Figure 4.11: Deployment view across the three-node cluster.

Node

Role

Minimum spec

Notes

csc-control

Control plane, bus, storage,

dashboards

4 vCPU, 8 GB, 40

GB disk

K3s server node

csc-edge-1

Production path and

environment

2–4 vCPU, 4 GB

Labelled csc.io/edge=true; runs the only

runc workload that can actuate

csc-shadow-1

Shadow execution

4–8 vCPU, 8 GB

Labelled csc.io/shadow=true; gVisor

installed here only

A three-node cluster is the target because it lets the team demonstrate a genuine cloud–edge split. The whole

design also runs on one machine (K3s single-node, everything co-scheduled) for development; experiment E8

explicitly measures the degraded single-node case rather than pretending it does not exist.

# Chapter 5: Runtime Workflow

This chapter walks through one complete epoch, end to end, in the order the code executes. It is written so

that a developer can use it as a build checklist.

5.1

The Eight Phases of an Epoch

Phase

Name

Owner

Budget (of Tepoch = 10

s)

Failure mode

State capture

SCE

0–2 % (target < 15 ms)

Skip branching, run

production only

Branch planning and forking

MBS

2–6 % (target < 40 ms)

Reduce N, or run production

only

Input duplication

SYNC

Continuous through the

epoch

Drop shadow consumers, never

production

Parallel execution

Branch pods

6–70 %

Individual branch marked

TIMEOUT

Actuation and blocking

AG / VAB

Within phase 4

Deny and audit

Telemetry collection

Branch pods +

env

70–80 %

Barrier proceeds partial

Comparison and regret

OCE

80–90 % (target < 50 ms)

PARTIAL CFR

Record, reap, and (occasionally)

learn

OCE / MBS /

LE

90–100 %

Learning is async; never blocks

5.2

Master Sequence Diagram

5.3

Phase 1 — State Capture

Goal: produce one immutable byte string that fully determines how any branch will behave, given the same

inputs and action.

Implementation notes for the developer:

- The read lock is held only across the field reads, not across encoding. Copy first, encode after.

- Field order in the encoding must be deterministic (sort by name) or the hash is meaningless.

- Include schema_version in the payload. A branch that hydrates an anchor from a different schema version

must refuse and mark itself ABORTED rather than guess.

- rng_seed in the anchor is what makes branches reproducible. The worker must seed all sources of random-

ness from it — Python’s random, NumPy, and torch — in the hydrate path.

5.4

Phase 2 — Forking

CSC "forking" means: bind N + 2 pre-warmed pods to this epoch and hydrate them from the same anchor.

The hash cross-check at the end is cheap and catches an entire class of bugs: a stale pod that failed to reset,

a wrong anchor fetched due to a key collision, a partially-applied hydration. Requirement R1 is verified

at runtime, every epoch, not just in tests.

Failure handling during forking:

Failure

Response

Warm pool empty

Create pods on demand; mark COLD_START; if creation exceeds the phase budget,

drop those branches

Hydration timeout on a

shadow

Mark ABORTED, continue with remaining branches

Hydration timeout on

production

Critical: alert, retry once, then fall back to the last-known-good local controller.

Production must not stall waiting for CSC

Runtime Workflow

Failure

Response

Hash mismatch

ABORTED + csc_anchor_mismatch_total++ + alert (this indicates a real bug)

5.5

Phase 3 — Input Duplication

Three properties the implementation must guarantee, in priority order:

1. Order. Every branch consumes records in seq order. Never parallel-consume within a branch.

2. Completeness for the horizon. A branch that misses a record is DEGRADED, and a degraded branch is

excluded from the comparison. Silently comparing a branch that saw 5 records against one that saw 6

would be the worst kind of bug — it produces plausible, wrong numbers.

3. Isolation of back-pressure.

Bounded shadow queues that drop are strictly better than unbounded

queues that stall the sequencer.

The Epoch Input Log (a Redis Stream keyed csc:inlog:{site}:{k}, TTL = 2 epochs) exists so a branch

that started late can replay from seq=0 and still be comparable. Without it, cold-started branches would be

systematically biased toward seeing fewer inputs.

5.6

Phase 4 — Parallel Execution

Inside every branch, the loop is the same:

Note how the production and shadow paths are structurally the same shape — the only divergence is the

box after "emit actuation". This is deliberate: it means the code path exercised by shadow branches is the

same code path production uses, which is what makes the comparison meaningful (requirement R3’s positive

counterpart).

Every branch enforces its own deadline in addition to the MBS-side deadline. A branch that reaches deadline_

ns emits a TIMEOUT outcome with whatever metrics it has and exits. Self-enforcement plus external enforcement

means a wedged branch cannot hold the barrier.

5.7

Phase 5 — Actuation and Blocking

This phase overlaps phase 4 in time but is separated here because it is the safety-critical one.

The full

mechanism is Chapter 6; the workflow view is:

The metric csc_actuation_blocked_total{layer, branch_role} is the headline safety number for the project.

In steady state it should be zero; during the red-team experiment (E3) it should equal the number of attempts.

A non-zero value in normal operation means a real bug, and it is wired to an alert.

5.8

Phase 6 — Telemetry Collection

Two independent telemetry paths, and it is important not to confuse them:

Path

Source

Content

Consumer

Outcome

path

Each branch publishes one outcome

message

Domain metrics + runtime metrics

for that branch

OCE (for comparison)

Realised path

The environment service publishes what

actually happened over the horizon

Ground-truth domain metrics

OCE (as oreal

k

)

Ops path

Prometheus scrapes every component

Latencies, counters, gauges

Grafana, alerts

The realised path must measure the same window as the branches’ horizon. If branches evaluate 6 ticks

starting at epoch k, the realised telemetry must aggregate exactly ticks k through k + 5 of the environment.

Getting this window alignment wrong is the single most likely source of a wrong regret number, so the

environment service publishes an explicit {epoch, from_tick, to_tick} envelope and the OCE rejects any

realised record whose window does not match.

5.9

Phase 7 — Comparison and Regret

Both regret_raw and regret_discounted are stored. The raw value is what a naive implementation would

report; the discounted value is what CSC actually claims. Keeping both lets the evaluation chapter show

Runtime Workflow

Knowledge Store

Comparison Engine

Environment J1

Actuation Gateway

Shadows b1..bN

Mirror bm

Production b0

Sync Layer

Branch Scheduler

State Capture

Epoch Clock

tick(epoch k)

freeze, serialise, hash

store anchor s_k

AnchorReady(k, hash)

compute budget N_k, build candidate set

par

[fork production]

hydrate(s_k, role=PRODUCTION, action=free)

[fork mirror]

hydrate(s_k, role=MIRROR, action=a0)

[fork shadows]

hydrate(s_k, role=SHADOW, action=a_i)

open branch subjects for epoch k

loop

[for each input record, seq = 0..H]

sensor reading

par

[to production]

record(seq)

[to mirror]

record(seq)

[to shadows]

record(seq)

actuate(a0, token role=PRODUCTION)

verify token, claim epoch interlock

apply(a0)

shadow egress goes to VAB, never to AG

par

[production reports]

outcome REALISED

[mirror reports]

outcome ESTIMATED for a0

[shadows report]

outcome ESTIMATED for a_i

realised telemetry for epoch k

barrier, utilities, epsilon, regret

write CFR(k)

epoch complete

reap

reap

Knowledge Store

Comparison Engine

Environment J1

Actuation Gateway

Shadows b1..bN

Mirror bm

Production b0

Sync Layer

Branch Scheduler

State Capture

Epoch Clock

Figure 5.1: Master epoch sequence, end to end.

Runtime Workflow

Tick arrives for epoch k

Acquire read lock on state

holder

Read each field declared in

state_schema.yaml

All required fields present?

no

yes

Emit AnchorFailed

Encode CBOR

production-only epoch

alert: schema violation

Compute sha256 ->

anchor_hash

size <= max_bytes AND

elapsed <=

capture_budget_ms?

no

yes

Emit AnchorSkipped

Write to Redis; release lock

production-only epoch

metric: budget_exceeded

Publish AnchorReady(k,

hash, size)

Figure 5.2: Phase 1: state capture flow.

Runtime Workflow

Knowledge Store

Branch pod (sidecar)

Token Issuer

Branch Ledger

Branch Scheduler

register branches (PLANNED)

pick warm pods from pool

mark BOUND, attach pod names

issue branch tokens (role, epoch, exp)

signed tokens

Hydrate{anchor_hash, action, role, token, horizon, deadline}

GET anchor by hash

CBOR payload

verify sha256, decode, reset worker, seed RNG

mark HYDRATED (reports observed anchor_hash)

MBS asserts reported hash == expected hash

mismatch -> branch ABORTED and excluded

Knowledge Store

Branch pod (sidecar)

Token Issuer

Branch Ledger

Branch Scheduler

Figure 5.3: Phase 2: branch forking sequence with anchor-hash cross-check.

queue: production

consume in seq order

(unbounded-ish)

consume in seq order

queue: mirror (bounded 256)

Ingest and Sequencer (single instance)

overflow

drop + mark branch

Receive raw sensor record

Assign seq++ and epoch tag

Append to Epoch Input Log

Fan-out to

overflow

registered branches

DEGRADED

queue: shadow-1 (bounded

256)

overflow

consume in seq order

queue: shadow-N (bounded

256)

consume in seq order

Figure 5.4: Phase 3: input duplication and back-pressure isolation.

Runtime Workflow

Hydrated from anchor s_k

role

PRODUCTION

MIRROR

SHADOW

policy.decide(s) -> a0

forced action = a0

forced action = a_i

emit actuation

role == PRODUCTION?

no

Virtual Actuation Buffer ->

yes

SEM

SEM advances shadow state

Actuation Gateway -> real

using action + exogenous

environment

inputs

await next input record

ticks consumed < H?

yes

no

policy.decide(shadow state) -

aggregate metrics ->

> follow-up action

outcome vector

publish to csc.outcomes

Figure 5.5: Phase 4: branch execution loop. Production and shadow differ only after actuation.

Runtime Workflow

Audit

Virtual Actuation Buffer

Actuation Gateway (L2)

NetworkPolicy (L3)

Egress shim (L1)

Shadow branch

actuate(set_phase, ns=40, ew=20)

read role from token

alt

[role is SHADOW or MIRROR]

append entry (would_have_targeted = env-service:8080)

ok

VirtualAck

[developer bypassed the shim (bug or malice)]

direct TCP to env-service

connection refused (egress denied)

HTTP to gateway (if reachable)

violation: role != PRODUCTION

403 ACTUATION_DENIED

Audit

Virtual Actuation Buffer

Actuation Gateway (L2)

NetworkPolicy (L3)

Egress shim (L1)

Shadow branch

Figure 5.6: Phase 5: actuation and blocking.

the difference, which is itself an interesting result for the paper — it quantifies how much of an apparent

improvement is really just model error.

5.10

Phase 8 — Record, Reap, Learn

Reaping returns pods to the warm pool:

Sanitisation is a correctness requirement, not hygiene: any residue from epoch k that survives into epoch k +1

silently violates R1. The sidecar’s Sanitise() must clear worker state, delete the VAB stream, reset RNG

state, and drop any cached policy tensors, then report POOL_READY with a self-test hash of its empty state.

Learning is triggered on a cadence, not per epoch:

Trigger

Default

Rationale

Epoch count

Every 500 epochs

Enough new records to matter

Minimum new complete CFRs

Avoid training on mostly-PARTIAL data

Manual

Operator command

For experiments

Never on the epoch critical path

—

Principle P1

5.11

End-to-End Timing Budget for J1

A concrete, checkable target for the prototype. Numbers are design budgets to validate, not measured

results.

Step

Budget

Cumulative

Metric

Tick delivery

2 ms

2 ms

csc_tick_delivery_ms

State capture

15 ms

17 ms

csc_capture_duration_ms

Branch planning

10 ms

27 ms

csc_plan_duration_ms

Token issue + hydrate dispatch

30 ms

57 ms

csc_hydrate_dispatch_ms

Branch hydration (parallel)

60 ms

117 ms

csc_branch_hydrate_ms

Execution over horizon H = 6

~6 s

~6.1 s

csc_branch_exec_ms

Outcome publish + realised telemetry

200 ms

~6.3 s

csc_outcome_lag_ms

Barrier wait (slack)

up to 1.5 s

~7.8 s

csc_barrier_wait_ms

Comparison + CFR write

50 ms

~7.9 s

csc_compare_duration_ms

Reap

100 ms

~8.0 s

csc_reap_duration_ms

Slack before next tick

~2.0 s

10 s

csc_epoch_slack_ms

Runtime Workflow

Outcomes received for

epoch k

Production outcome present?

no

yes

No CFR written

Compute U for every branch

using configured utility

metric:

cfr_skipped_no_ground_truth

Mirror outcome present?

yes

no

epsilon_k = |U_hat(a0) -

epsilon_k = EWMA(epsilon)

flag EPSILON_ESTIMATED

U_real|

update EWMA

best_alt = argmax over

shadows

regret_raw = max(0, U_best -

U_real)

regret_discounted =

max(0, U_best - epsilon_k -

U_real)

All expected branches

present?

yes

no

record_status = COMPLETE

record_status = PARTIAL

list missing branch ids

Write CFR

Publish csc.cfr; update

Prometheus gauges

Figure 5.7: Phase 7: comparison and regret computation.

Runtime Workflow

InPool

assigned to epoch k

Bound

hydrated

Active

epochs_served < 200

horizon complete or deadline

Draining

worker state cleared, VAB

FAULTED

deleted, seeds reset

Sanitised

epochs_served >= 200

Terminated

Figure 5.8: Phase 8: warm-pool pod lifecycle.

Runtime Workflow

If csc_epoch_slack_ms trends toward zero, the MBS reduces N automatically. That is the closed-loop protection

for the whole timing budget, and it is worth building early because it is what makes the demo robust in front

of an examiner.

5.12

Failure Handling Summary

Failure

Detection

Response

Production impact

SCE slow or crashed

Missing AnchorReady

before budget

Production-only epoch

None

MBS crashed

Liveness probe

Production-only epochs until restart

None

SYNC sequencer

crashed

Gap in seq

Branches DEGRADED; production reads directly

from raw subject as fallback

Degraded telemetry

only

A shadow pod crashes

Ledger sees no outcome by

deadline

FAULTED, excluded, pod recreated

None

Production pod

crashes

Kubernetes restart +

missing actuation

Environment holds last commanded phase

(fail-safe default); alert

Real — this is the one

that matters

AG unreachable

Production actuation

returns error

Retry once, then fall back to a local safe

default (fixed-time signal plan)

Degraded control

Redis down

Connection errors

Production-only; CSC disabled entirely until

recovery

None (by design)

Bus down

Publish failures

CSC disabled; production falls back to direct

sensor read

Degraded

OCE crashed

No CFR written

Epochs lost from the dataset; runtime

unaffected

None

Learning Engine

crashed

CronJob failure

Policy frozen at incumbent

None

The column that matters is the last one. In eight of ten failure modes, the correct behaviour is CSC quietly

switches itself offand the system keeps running.

Building the prototype so that "kill the branch

manager during the demo, everything keeps working" is a feature you can show, not a disaster, is strongly

recommended.

# Chapter 6: Non-Actuating Shadow Runtime

6.1

The Property We Need

Containment property. For every branch b with role ̸= PRODUCTION, and for every possible behaviour of the code

running in b — including buggy, adversarial, or compromised behaviour — no state outside the CSC runtime is

modified.

Three words in that statement carry the weight:

- "every possible behaviour" — we do not get to assume the shadow policy is well-behaved. A student

experiment might deploy a half-trained model that emits nonsense; that must be harmless.

- "outside the CSC runtime" — writing to its own VAB, publishing its own outcome, and emitting

metrics are all fine. Those are inside.

- "modified" — reads of non-sensitive data are tolerated; writes and side-effecting calls are not.

6.2

What Counts as Actuation

Before you can block something, you must enumerate it. For a CSC-enabled application, actuation is any of:

Category

Example at J1

Blocked by

Device / actuator control

POST /signal/phase to the junction controller

L1, L2, L3, L4

Shared database write

UPDATE junction_state SET ...

L1, L3, L4

External API call

Notifying a city traffic-management API

L1, L3, L5

Publishing to a production topic

Writing to city.traffic.commands

L1, L3, L4

Filesystem write outside the branch

Writing a shared PVC

L5

Sending mail, SMS, webhooks

Incident notification

L3, L4

Consuming a limited resource

Acquiring a distributed lock, spending API quota

L3, L4

The last row is easy to forget. A shadow branch that acquires a real distributed lock has affected the world

even though it "only read." The design rule is: the shadow ServiceAccount holds no credentials that

can consume anything.

6.3

Five-Layer Defence

Each layer is independently sufficient for a class of failure and no layer is trusted alone. The table below is

what the team should put on a slide.

Layer

Mechanism

Blocks

Does not block

Cost to

implement

Honest code

Code that bypasses

the library

Low (~150

LOC)

L1 Egress shim

Role-aware client library in the sidecar;

actuate() inspects the branch token

and writes to VAB for non-production

roles

Low (~400

LOC)

L2 Actuation

Gateway

Ed25519 token verification; role must be

PRODUCTION; SETNX epoch interlock;

fail-closed

Direct connections to

the environment that

skip the gateway

Anything that

reaches the gateway,

including forged

intent

Low (config)

All network side

effects

In-pod effects; effects

via the allowlisted

services

L3

NetworkPolicy

Default-deny egress on shadow pods;

allowlist = Redis (VAB), bus

(inputs/outcomes), DNS, Prometheus.

No route to env-service, no internet

Authenticated side

effects

Unauthenticated

targets

Low (config)

L4 Credential

absence

Distinct csc-shadow ServiceAccount

with no RBAC verbs beyond get on its

own ConfigMap; no DB password, no

API key, no device token mounted

Non-Actuating Shadow Runtime

Layer

Mechanism

Blocks

Does not block

Cost to

implement

Container escape

attempts, host

filesystem access, raw

sockets,

kernel-surface abuse

A gVisor 0-day

(residual risk)

Medium

(install runsc

on the

shadow

node)

L5 Sandbox

RuntimeClass:

gvisor; read-only

root filesystem;

allowPrivilegeEscalation:

false;

all Linux capabilities dropped;

seccompProfile:

RuntimeDefault;

no host mounts; no host

network/PID/IPC

6.4

Layer 2 in Detail: The Branch Token

The branch token is the identity artefact that makes L1 and L2 coherent.

Header:

{ alg: "EdDSA", kid: "csc-token-key-1" }

Payload:

{

"branch_id": "J1-10423-SHADOW-2",

"site_id":

"J1",

"epoch":

10423,

"role":

"SHADOW",

"horizon":

6,

"exp":

<epoch deadline, unix ns>,

"nonce":

"<random 128-bit>"

}

Signature: Ed25519 over header.payload with the Token Issuer's private key

Property

Enforcement

Only the MBS can mint tokens

Private key lives in a Kubernetes Secret mounted only into the

branch-manager pod

A shadow token can never become a

production token

role is inside the signed payload

Tokens cannot be reused next epoch

epoch and exp are checked against the gateway’s current epoch

Tokens cannot be replayed within an epoch

nonce recorded in Redis with TTL; second use rejected

Gateway cannot be tricked by a missing

token

Absent or malformed token →403, never a default-allow

Verification is a pure function with no I/O other than the nonce check, which makes it straightforward to

unit-test exhaustively. The team should write a table-driven test with at least these cases: valid production,

valid shadow, valid mirror, expired, wrong epoch, wrong signature, tampered role, missing token, replayed

nonce, malformed base64, and empty body. That test file is the safety argument.

6.5

Layer 3 in Detail: Network Containment

The shadow pod’s allowed egress set, stated as a policy intent (the actual manifest is out of scope for this

document per the code guidelines):

Destination

Port

Purpose

Allowed for shadow?

redis.csc.svc

VAB writes, anchor reads

Yes

nats.csc.svc

Input consumption, outcome publish

Yes

kube-dns

Name resolution

Yes

prometheus.csc.svc

Metrics push (or scrape ingress)

Yes (scrape only)

env-service.csc.svc

The junction

No

actuation-gateway.csc.svc

Actuation

No

Any other cluster IP

any

—

No

0.0.0.0/0 (internet)

any

—

No

Two design refinements worth the small extra effort:

1. Separate Redis logical databases (or key-prefix ACLs) for VAB vs anchors, so a shadow branch with

Redis access cannot overwrite an anchor. Redis 6 ACLs make this a few lines of config and it closes an

otherwise real hole — a shadow branch corrupting the anchor would corrupt production’s next hydration.

Non-Actuating Shadow Runtime

Shadow branch code

attempts an effect

L1: Egress shim

role-aware SDK

routes to VAB

bypassed

L2: Actuation Gateway

Contained

token role check + epoch

(normal path)

interlock

403 denied

gateway unreachable

Contained + audited

L3: NetworkPolicy

egress allowlist

connection refused

route exists?

L4: Credential absence

Contained + audited

no tokens, no keys, no write

RBAC

401 from target

no auth required?

L5: Sandbox

Contained

gVisor + seccomp + ro-rootfs

+ no caps

syscall / capability denied

escape

Containment failure

Contained

-> documented residual risk

L8

Figure 6.1: The five-layer containment design.

Non-Actuating Shadow Runtime

2. A dedicated NATS account for shadows with publish permission only on csc.outcomes.> and csc.vab.

>, and subscribe permission only on its own input subject. Otherwise a shadow could publish a forged

production outcome and poison the comparison.

Both of these protect against a shadow branch affecting CSC itself, which is a category people forget when

they focus only on the physical world.

6.6

Layer 5 in Detail: Sandboxing with gVisor

CSC uses gVisor as a containment boundary, not as an instrumentation mechanism. It is worth being clear

about this because it is easy to overreach.

What gVisor gives CSC. gVisor runs the container’s system calls against a user-space kernel (the Sentry)

rather than the host kernel directly.

The container therefore interacts with a much smaller, memory-safe

implementation of the Linux surface, and the host kernel sees only a narrow set of calls from the Sentry itself.

For CSC this means: a shadow branch that finds a container-escape technique targeting the host kernel is far

more likely to hit the Sentry’s reimplementation than the real kernel.

How CSC uses it. Purely declaratively: a RuntimeClass named gvisor is installed on the shadow node, and

shadow pods request it. The team writes no gVisor code, no kernel modules, and no syscall filters of

their own. This is the difference between a semester project that finishes and one that does not.

Shadow branch pod (RuntimeClass: gvisor)

decision-worker + sidecar

syscalls

Production branch pod (RuntimeClass: runc)

gVisor Sentry

decision-worker + sidecar

user-space kernel

file ops

narrow host syscall set

syscalls

Gofer

filesystem proxy

Host kernel

read-only rootfs

+ emptyDir scratch

Figure 6.2: gVisor sandbox placement for shadow branches.

Syscall interception, honestly framed. People sometimes assume CSC intercepts syscalls to redirect writes

Non-Actuating Shadow Runtime

into virtual buffers — a kind of transparent copy-on-write world. That is a legitimate design (Chapter 14 lists

it), but it is not what this prototype proposes, for three reasons:

1. It requires per-syscall semantic knowledge (which write is "an actuation" versus "a log line") that a generic

layer does not have.

2. The interesting actuations at J1 are network calls to a service, not raw syscalls — blocking them at

L1/L2/L3 is both simpler and more precise.

3. Implementing it would consume the entire semester.

So the accurate description of CSC’s use of gVisor is: the sandbox constrains what a misbehaving

branch can reach; the gateway and network policy define what "actuation" means. Interception

happens at the application-protocol layer, containment happens at the sandbox layer, and the document should

not blur the two.

Costs to expect and measure (experiment E2b). gVisor adds overhead, particularly to syscall-heavy

and I/O-heavy work. Published figures vary widely by workload, so the team should measure their own rather

than cite numbers: run the identical shadow workload under runc and under gvisor and report the delta in

startup time, CPU-ms per branch, and p95 branch execution time. If the overhead proves unacceptable on

the available hardware, the documented fallback is runc + hardened securityContext + NetworkPolicy, with

the reduction in defence depth stated explicitly in the report. Making that trade visible is better engineering

than pretending it does not exist.

Sandbox option

Isolation strength

Overhead

Prototype status

gVisor (runsc)

Strong — user-space

kernel

Moderate, workload-dependent

Default for shadow branches

Kata Containers (microVM)

Strongest

Higher memory floor per branch

Alternative if gVisor is

unavailable; costly at N = 8

runc + seccomp + caps

dropped + read-only rootfs

Moderate

Lowest

Documented fallback; used for

production branch

WebAssembly runtime

Strong, tiny

Requires rewriting the worker

Future work (Ch. 14)

6.7

Virtual Buffers and Closing the Shadow Loop

A shadow branch that is merely blocked would produce no outcome.

The VAB plus SEM together turn

"blocked" into "evaluated."

Input stream (exogenous)

Shadow Environment Model

Virtual Actuation Buffer

Egress shim

Worker (shadow)

actuate(set_phase ns=40 ew=20)

append {seq, action, target=env-service}

VirtualAck(applied_at_tick=t)

exogenous inputs for tick t (real arrivals)

pending actions up to tick t

advance shadow state:

departures from action, arrivals from stream

observation(shadow state at t+1)

repeat for H ticks, then aggregate metrics

Input stream (exogenous)

Shadow Environment Model

Virtual Actuation Buffer

Egress shim

Worker (shadow)

Figure 6.3: Virtual Actuation Buffer and shadow loop closure.

The critical invariant, restated because it is the heart of the design’s honesty:

The SEM models only the effect of the action. It never invents inputs. Arrivals, weather, incidents, and

every other exogenous quantity come from the replicated live stream and are identical to what production experienced.

This confines modelling error to one term — the action’s local effect — instead of letting it contaminate the

whole trajectory. It also gives a clean explanation of what the mirror branch measures: the mirror runs the

production action through the SEM, so εk is precisely the error of that one modelled term, isolated from

everything else.

Non-Actuating Shadow Runtime

6.8

Verifying Containment

Containment must be tested, not assumed. Experiment E3 (Chapter 11) runs a deliberately hostile shadow

image, the red-team worker, whose job is to try to escape.

#

Attack the red-team worker attempts

Expected blocking layer

Expected observable

A1

Call actuate() normally

L1

VAB entry; no env change

A2

Construct an HTTP request directly to

env-service:8080

L3

Connection refused; blocked_

total{layer="L3"}++

A3

Call the Actuation Gateway with its own

(shadow) token

L2

403; violation event

A4

Forge a token with role:

PRODUCTION,

unsigned

L2

403 (signature invalid)

A5

Replay a captured production token from a

previous epoch

L2

403 (expired / wrong epoch)

A6

Two shadows both present valid-looking

production tokens

L2 interlock

At most one actuation; double_

actuation_total++

A7

Write to the anchor key in Redis

L3 refinement (ACL)

Permission denied

A8

Publish a forged outcome for another branch

Bus permissions

Publish denied

A9

Write to the container root filesystem

L5

Read-only filesystem error

A10

Attempt to mount /proc/1/root or access

host paths

L5

Denied

A11

Open a raw socket / attempt ARP spoofing

L5 + L3

Denied

A12

Resolve and contact an internet host

L3

DNS resolves, connection denied

A13

Fork-bomb / exhaust memory

Resource limits

Pod OOM-killed; branch FAULTED;

production unaffected

A14

Spin CPU to starve production

QoS class + node

anti-affinity

Production p95 latency unchanged

(measured)

Every row is a test case in tests/containment/. The suite runs in CI and its results table goes directly into the

evaluation report. This is one of the most publishable artefacts the project will produce, because it converts

a design claim into evidence.

6.9

Residual Risk

Stated plainly, because Chapter 13 will refer back to it:

1. Sandbox escape. gVisor reduces but does not eliminate escape risk. If the Sentry has a vulnerability,

containment can fail. Mitigation: keep runsc updated; do not run untrusted third-party code as a shadow

policy; treat the shadow node as a lower-trust zone.

2. Allowlisted-service abuse. Shadow branches legitimately reach Redis and NATS. A branch that floods

them degrades CSC (though not the environment). Mitigation: per-branch rate limits, bounded VAB,

separate Redis DB and NATS account.

3. The gateway itself. L2 is a single component; a bug there is a real hole. Mitigation: keep it tiny, 100 %

test coverage, no dependencies beyond Redis, and code review by two people as a merge requirement.

4. Definition gap. If the application performs a side effect the team did not classify as actuation, no layer

knows to block it. Mitigation: the actuation taxonomy in §6.2 is a living document reviewed whenever the

worker gains a new dependency.

Point 4 is the one most likely to bite in practice, and it is worth saying in the report: containment is only

as complete as the enumeration of effects.

# Chapter 7: Algorithms

The pseudocode in this chapter is written to be transcribed into Go or Python with minimal thought. It is

deliberately not optimised and not exhaustive on error handling — the failure tables in Chapter 5 cover that.

Types are indicated where they matter for the interface between components.

Notation used throughout: // for comments, <- for assignment from a call, := for local binding, ? suffix for

optional values.

7.1

Algorithm 1 — State Capture

ALGORITHM CaptureAnchor(epoch k, schema S, budget_ms B) -> Anchor?

t_start := now_monotonic()

fields

:= empty map

// --- critical section: consistent read of all declared fields ---

lock.RLock()

for each field f in S.fields:

v := read_source(f.source, f.name)

if v is missing:

if f.required:

lock.RUnlock()

emit_metric("csc_capture_missing_field", f.name)

return null

// production-only epoch

else:

v := f.default

fields[f.name] := coerce(v, f.type)

lock.RUnlock()

// --- end critical section ---

fields["__schema_version"] := S.version

fields["__site_id"]

:= S.site_id

fields["__epoch"]

:= k

payload := cbor_encode(sort_by_key(fields))

// deterministic ordering

hash

:= sha256(payload)

elapsed := now_monotonic() - t_start

observe("csc_capture_duration_ms", elapsed)

observe("csc_anchor_size_bytes", len(payload))

if elapsed > B or len(payload) > S.max_bytes:

inc("csc_capture_budget_exceeded_total")

return null

// production-only epoch

store.Set("csc:anchor:" + S.site_id + ":" + hash, payload, ttl=24h)

store.Set("csc:epoch:" + S.site_id + ":" + k + ":anchor", hash, ttl=2h)

return Anchor{ hash, payload_len, k, S.version }

Notes for the implementer:

- sort_by_key is not cosmetic. Without it, two logically identical states hash differently and content address-

ing breaks.

- The budget check happens after encoding so that the metric reflects true cost, but the anchor is discarded

rather than used late. Better to lose one epoch of shadow data than to blow the epoch budget.

7.2

Algorithm 2 — Multi-Branch Scheduler

ALGORITHM PlanEpoch(epoch k, Anchor A, Policy pi, Stats st) -> BranchPlan

Algorithms

// ---- 1. how many shadows can we afford? ----

n_cpu

:= floor( (rho * st.cpu_available_cores) / st.cpu_per_branch_ewma )

n_mem

:= floor( (st.mem_available_mb - MEM_RESERVE) / st.mem_per_branch_ewma )

n_time := 0

if st.branch_exec_p95_ms > 0:

usable := T_EPOCH_MS - st.capture_ms - st.compare_ms - SAFETY_MS

n_time := floor(usable / st.branch_exec_p95_ms) * PARALLEL_SLOTS

N := min(N_MAX, n_cpu, n_mem, n_time)

if st.epoch_slack_ms_ewma < SLACK_FLOOR_MS:

N := max(0, N - 1)

// back off under pressure

observe("csc_branch_budget", N)

if N < 1:

return BranchPlan{ production_only: true }

// ---- 2. which actions do we evaluate? ----

s

:= decode(A)

ranked

:= pi.rank_actions(s)

// descending predicted utility

a0

:= ranked[0]

// what production will do

candidates := []

// slot 1: mirror (always, if budget >= 1) -- this buys us epsilon

candidates.append(Candidate{ role: MIRROR, action: a0 })

// slots 2..: top-k alternatives, excluding a0

for a in ranked[1 : ]:

if len(candidates) >= N: break

candidates.append(Candidate{ role: SHADOW, action: a, reason: "top_k" })

// final slot: exploration, biased to under-visited actions

if len(candidates) < N or EXPLORE_ALWAYS:

a_explore := sample_inverse_visit(st.visit_counts, exclude = actions(candidates))

if a_explore != null:

if len(candidates) >= N: candidates.pop()

// trade a top-k slot

candidates.append(Candidate{ role: SHADOW, action: a_explore,

reason: "explore" })

// ---- 3. promotion audit: occasionally let a shadow action be real ----

audited := false

if rand_from(A.seed) < RHO_AUDIT and st.epsilon_ewma < EPSILON_AUDIT_MAX:

swap := pick_one(candidates where role == SHADOW and reason == "explore")

if swap != null:

a0

:= swap.action

// production takes the probe

audited := true

inc("csc_promotion_audit_total")

return BranchPlan{

production: Candidate{ role: PRODUCTION, action: a0, pinned: false },

shadows:

candidates,

audited:

audited,

anchor:

A,

deadline:

epoch_start + BARRIER_FRACTION * T_EPOCH_MS

}

Two design points hidden in the code:

- The mirror gets the first shadow slot, not the last. If budget is tight we would rather have one calibrated

comparison than two uncalibrated ones. Without ε, regret is not defensible.

- rand_from(A.seed) makes the audit decision reproducible from the anchor, so an experiment can be

replayed exactly. Never use an unseeded RNG anywhere in CSC.

7.3

Algorithm 3 — Shadow Branch Creation

ALGORITHM CreateBranches(BranchPlan P) -> []BranchHandle

handles := []

all

:= [P.production] + P.shadows

for i, c in all:

bid := format("%s-%d-%s-%d", P.anchor.site, P.anchor.epoch, c.role, i)

ledger.Put(bid, { epoch, role: c.role, action: c.action,

Algorithms

anchor_hash: P.anchor.hash, state: PLANNED,

deadline: P.deadline })

handles.append(BranchHandle{ bid, c })

// bind pods: production is a long-lived pod; shadows come from the warm pool

for h in handles:

if h.role == PRODUCTION:

h.pod := production_pod

// never recreated per epoch

else:

h.pod <- warm_pool.Acquire(timeout = BIND_TIMEOUT_MS)

if h.pod == null:

h.pod <- create_pod_on_demand(runtime_class = "gvisor")

h.cold_start := true

inc("csc_cold_start_total")

ledger.Update(h.bid, state = BOUND, pod = h.pod.name)

// issue identity tokens -- role is inside the signature

for h in handles:

h.token := token_issuer.Sign({ branch_id: h.bid, site: P.anchor.site,

epoch: P.anchor.epoch, role: h.role,

horizon: H, exp: P.deadline,

nonce: random128() })

// hydrate in parallel; all from the SAME anchor hash

parallel for h in handles:

ok := h.pod.Hydrate({ anchor_hash: P.anchor.hash,

action:

h.action,

pinned:

(h.role != PRODUCTION),

role:

h.role,

token:

h.token,

horizon:

H,

deadline:

P.deadline })

if not ok or h.pod.reported_anchor_hash != P.anchor.hash:

ledger.Update(h.bid, state = ABORTED)

inc("csc_anchor_mismatch_total")

if h.role == PRODUCTION: raise CriticalProductionHydrationFailure

continue

ledger.Update(h.bid, state = HYDRATED)

sync.OpenSubjects(P.anchor.epoch, [h.bid for h in handles if h.state == HYDRATED])

return handles

7.4

Algorithm 4 — Branch Execution Loop (inside a pod)

ALGORITHM RunBranch(HydrateMsg m) -> Outcome

payload := store.Get("csc:anchor:" + m.site + ":" + m.anchor_hash)

assert sha256(payload) == m.anchor_hash

s := decode(payload)

seed_all_rngs(s.rng_seed)

// python random, numpy, torch

worker.Reset(s)

env := (m.role == PRODUCTION) ? RealEnvProxy(gateway, m.token)

: ShadowEnv(SEM.new(s), VAB(m.branch_id))

report(state = HYDRATED, anchor_hash = m.anchor_hash)

metrics := MetricAccumulator.new()

tick

:= 0

action

:= m.action

// first action is given

while tick < m.horizon and now() < m.deadline:

rec := input_stream.Next(blocking, deadline = m.deadline)

if rec == null:

break

// deadline hit mid-horizon

if rec.seq != tick:

report(state = DEGRADED, reason = "seq_gap")

break

// apply this tick's action through the role-appropriate egress

env.Actuate(action)

obs := env.Observe(rec)

// real telemetry OR SEM step

metrics.Accumulate(obs)

Algorithms

worker.Update(obs)

tick := tick + 1

if tick < m.horizon:

if m.pinned == "all":

action := m.action

// keep forcing (ablation mode)

else:

action := worker.Decide()

// free follow-up decisions

return Outcome{

branch_id:

m.branch_id,

epoch:

m.epoch,

role:

m.role,

action:

m.action,

provenance:

(m.role == PRODUCTION) ? "REALISED" : "ESTIMATED",

horizon:

tick,

metrics:

metrics.Finalise(),

runtime:

{ cpu_ms, peak_rss_mb, hydrate_ms, vab_entries },

status:

(tick == m.horizon) ? "REPORTED" : "TIMEOUT"

}

The rec.seq != tick check is the runtime enforcement of requirement R2. A branch that notices it missed

an input disqualifies itself rather than producing a comparable-looking but incomparable outcome. Self-

disqualification is much safer than central detection here, because the branch is the only party that knows

what it actually consumed.

7.5

Algorithm 5 — Egress Shim (the actuation decision)

ALGORITHM Actuate(action a, BranchToken t) -> Ack

switch t.role:

case PRODUCTION:

resp := http.POST(GATEWAY_URL + "/v1/actuate",

body

= a,

headers = { "X-CSC-Branch-Token": t.raw })

if resp.status == 200:

inc("csc_actuation_allowed_total")

return RealAck{ resp.applied_at }

inc("csc_actuation_error_total", resp.status)

return Error(resp)

// caller falls back to safe default

case MIRROR, SHADOW:

vab.Append({ seq: current_seq, ts: now(), action: a,

would_have_targeted: GATEWAY_URL })

inc("csc_virtual_actuation_total", t.role)

return VirtualAck{ applied_at_tick: current_seq }

default:

// unknown role -> refuse. fail closed.

inc("csc_actuation_blocked_total", layer = "L1", reason = "unknown_role")

return Error("role not permitted to actuate")

ALGORITHM GatewayHandleActuate(request r) -> HTTPResponse

// Layer 2

t := parse_token(r.header["X-CSC-Branch-Token"])

if t == null or not verify_ed25519(t, PUBLIC_KEY):

audit(r, "invalid_token"); inc("csc_actuation_blocked_total", layer="L2")

return 403

if t.role != "PRODUCTION":

audit(r, "role_denied", t.branch_id)

inc("csc_actuation_blocked_total", layer="L2", role=t.role)

return 403

if t.exp < now() or t.epoch != current_epoch():

audit(r, "stale_token"); inc("csc_actuation_blocked_total", layer="L2")

return 403

if not redis.SetNX("csc:nonce:" + t.nonce, 1, ttl = 2 * T_EPOCH):

audit(r, "replayed_nonce"); return 403

Algorithms

// epoch interlock: at most one actuation per epoch, whatever happens upstream

if not redis.SetNX("csc:actuated:" + t.site + ":" + t.epoch, t.branch_id,

ttl = 2 * T_EPOCH):

owner := redis.Get("csc:actuated:" + t.site + ":" + t.epoch)

audit(r, "epoch_already_actuated", owner)

inc("csc_double_actuation_total")

return 409

result := environment.Apply(r.body)

audit(r, "allowed", t.branch_id, result)

inc("csc_actuation_allowed_total")

return 200

7.6

Algorithm 6 — Outcome Comparison

ALGORITHM CompareEpoch(epoch k, expected []BranchID, deadline d) -> CFR?

received := {}

while now() < d and len(received) < len(expected):

o := outcome_bus.Next(timeout = d - now())

if o != null and o.epoch == k and o.status in {REPORTED, TIMEOUT}:

received[o.branch_id] := o

real := await_realised_telemetry(k, timeout = d - now())

if real == null or PRODUCTION not in roles(received):

inc("csc_cfr_skipped_no_ground_truth_total")

return null

// no ground truth -> no record

U := {}

for bid, o in received:

if o.status == TIMEOUT or o.horizon < MIN_HORIZON:

continue

// incomparable; exclude explicitly

U[bid] := utility(o.metrics, UTILITY_CONFIG)

u_real := utility(real.metrics, UTILITY_CONFIG)

// ---- fidelity gap from the mirror branch ----

mirror := find(received, role = MIRROR, status = REPORTED)

if mirror != null:

eps

:= abs(U[mirror.branch_id] - u_real)

eps_source := "MEASURED"

epsilon_ewma.Update(eps)

else:

eps

:= epsilon_ewma.Value()

eps_source := "ESTIMATED"

// ---- best alternative among true shadows ----

shadows := [ (bid, U[bid]) for bid in U if role(bid) == SHADOW ]

if len(shadows) == 0:

status := "PRODUCTION_ONLY"; u_best := u_real; a_best := action(production)

else:

(b_best, u_best) := argmax_by_value(shadows)

a_best

:= action(b_best)

status := (len(received) == len(expected)) ? "COMPLETE" : "PARTIAL"

regret_raw

:= max(0, u_best - u_real)

regret_disc := max(0, u_best - eps - u_real)

cfr := CFR{ epoch: k, site: SITE, anchor_hash: anchor_of(k),

policy_version: active_policy(),

u_real, u_mirror: U[mirror]?, epsilon: eps, eps_source,

regret_raw, regret_discounted: regret_disc,

best_alt_action: a_best,

branches: [ project(o, U[o.branch_id]) for o in received ],

record_status: status,

missing: expected - keys(received) }

knowledge_store.Append(cfr)

publish("csc.cfr", cfr)

set_gauge("csc_regret_discounted", regret_disc)

set_gauge("csc_fidelity_gap", eps)

return cfr

Algorithms

7.7

Algorithm 7 — Regret Accounting Over Time

Per-epoch regret is noisy; the useful signals are aggregates.

ALGORITHM UpdateRegretAccounting(CFR c, RegretState rs)

rs.cumulative_raw

+= c.regret_raw

rs.cumulative_discount

+= c.regret_discounted

rs.n

+= 1

rs.window.Push(c.regret_discounted)

// sliding window, size W = 360

rs.mean_window := rs.window.Mean()

rs.p90_window

:= rs.window.Quantile(0.90)

// how often did an alternative beat production by more than the noise floor?

if c.regret_discounted > 0:

rs.beaten_count += 1

rs.by_action[c.best_alt_action] += 1

rs.beaten_rate := rs.beaten_count / rs.n

// fidelity health -- if this drifts up, everything above is less trustworthy

rs.epsilon_ewma := ALPHA * c.epsilon + (1 - ALPHA) * rs.epsilon_ewma

if rs.epsilon_ewma > EPSILON_ALERT:

alert("shadow fidelity degraded; regret figures are unreliable")

export_all(rs)

beaten_rate — the fraction of epochs in which some alternative beat production by more than ε — is the most

interpretable headline number the project can report. "In 12 % of epochs, a different green-time split appeared

better than the one we chose, by more than our measured model error" is a claim a reviewer can engage with.

rs.by_action shows which alternatives keep winning, which is where policy improvement comes from.

7.8

Algorithm 8 — Policy Update

Two variants. The prototype should implement V1 first and only attempt V2 if time allows.

7.8.1

V1 — Utility model + softmax policy (recommended)

ALGORITHM TrainUtilityModel(CFRs D, Model phi) -> Model

X := []; Y := []; W := []

for c in D:

if c.record_status == "PARTIAL" and STRICT: continue

if c.epsilon > EPSILON_TRAIN_MAX: continue

// drop untrustworthy epochs

s := load_anchor(c.anchor_hash)

for b in c.branches:

if b.status != "REPORTED": continue

X.append(features(s, b.action))

Y.append(b.utility)

W.append( b.provenance == "REALISED" ? 1.0

: 1.0 / (1.0 + LAMBDA * c.epsilon) )

(Xtr, Ytr, Wtr), (Xva, Yva, Wva) := split_by_time(X, Y, W, frac = 0.8)

phi_new := phi.clone()

for epoch_i in 1..EPOCHS:

for batch in shuffle(Xtr, Ytr, Wtr, size = 256):

loss := weighted_mse(phi_new(batch.X), batch.Y, batch.W)

phi_new.step(loss)

// validate ONLY on realised samples -- estimated targets cannot validate

val := realised_only(Xva, Yva)

mae_new := mean_abs_error(phi_new(val.X), val.Y)

mae_old := mean_abs_error(phi(val.X),

val.Y)

if mae_new >= mae_old:

log("candidate rejected: no improvement on realised holdout")

return phi

return phi_new

Algorithms

ALGORITHM DerivePolicy(Model phi, State s, Stats st) -> ranked actions

scores := [ phi(features(s, a)) for a in ACTION_SET ]

// optimism bonus for rarely-tried actions keeps the dataset from collapsing

bonus

:= [ BETA * sqrt( log(st.total_visits) / (1 + st.visits[a]) )

for a in ACTION_SET ]

return sort_desc(ACTION_SET, key = scores + bonus)

7.8.2

V2 — Counterfactual policy gradient (optional extension)

ALGORITHM PolicyGradientStep(CFR c, Policy theta) -> Policy

s

:= load_anchor(c.anchor_hash)

utils

:= { b.action: b.utility for b in c.branches if b.status == "REPORTED" }

baseline := mean(values(utils))

// all-branch mean as baseline

grad

:= 0

for a, u in utils:

advantage := u - baseline

confidence := (provenance(a) == "REALISED") ? 1.0

: 1.0 / (1 + LAMBDA * c.epsilon)

grad += confidence * advantage * grad_log_pi(theta, s, a)

theta_new := theta + ETA * grad

if kl_divergence(theta, theta_new, s) > KL_TRUST_REGION:

theta_new := interpolate(theta, theta_new, to_kl = KL_TRUST_REGION)

return theta_new

The multi-branch structure is what makes the baseline meaningful here: a conventional log gives one action

per state and no within-state baseline, whereas a CFR gives N + 1 actions evaluated from an identical state.

That is the concrete sense in which CSC’s data is shaped differently from ordinary telemetry, and it is worth

stating explicitly in the paper.

7.9

Algorithm 9 — Promotion Gate

ALGORITHM EvaluateCandidatePolicy(version v_new, version v_cur, int W) -> Decision

deploy_to_shadow_only(v_new, epochs = W)

wait_epochs(W)

cfrs := recent_cfrs(W)

u_new := mean([ utility_of_branches_running(v_new, c)

for c in cfrs ])

u_cur := mean([ c.u_real

for c in cfrs ])

eps

:= mean([ c.epsilon

for c in cfrs ])

if u_new - u_cur <= eps:

record_rejection(v_new, "improvement within fidelity noise floor")

return REJECT

if fraction(cfrs, c -> c.record_status != "COMPLETE") > 0.3:

record_rejection(v_new, "insufficient complete records")

return REJECT

promote_with_canary(v_new, canary_epochs = C)

for i in 1..C:

wait_epoch()

if rolling_mean(realised_utility, C) < u_cur - ROLLBACK_MARGIN:

rollback_to(v_cur)

record_rollback(v_new, "realised utility degraded")

return ROLLED_BACK

return PROMOTED

The comparison u_new - u_cur <= eps is where the fidelity gap earns its keep a second time: a policy is

not promoted on the strength of a shadow-estimated improvement smaller than the shadow world’s own

demonstrated error.

Algorithms

7.10

Algorithm 10 — Adaptive Branch Pruning (optional)

If the team has time, this is the highest-value optimisation, and it makes a good paper section.

ALGORITHM PruneBranchesEarly(epoch k, branches B, int checkpoint_tick)

// at an intermediate tick, kill branches that cannot plausibly win

partial := { b: b.metrics.PartialUtility() for b in B if b.role == SHADOW }

if len(partial) < 3: return

best

:= max(values(partial))

spread := stddev(values(partial))

for b, u in partial:

if best - u > PRUNE_SIGMA * spread and remaining_ticks(b) > MIN_REMAINING:

b.Cancel(reason = "pruned_low_partial_utility")

inc("csc_branch_pruned_total")

release_pod_to_warm_pool(b.pod)

The freed slot can be reused within the same epoch for another candidate, effectively turning the branch

budget into a successive-halving allocation. The risk — and it must be reported — is bias: an action that is

bad early and good late gets systematically pruned. The honest way to handle this is to run pruning offfor

the headline experiments and on for a separate efficiency experiment (E2c), then report both.

# Chapter 8: Mathematical Model

The mathematics here exists to make the implementation precise and the evaluation reproducible. There are

no theorems and no proofs, deliberately: CSC is an architecture proposal, and formalism beyond what the

code needs would be decoration.

8.1

State, Action, Environment

Let S be the space of decision-relevant runtime states as defined by the state schema, and A the finite candidate

action set. At epoch k:

sk ∈S,

a ∈A,

|A| = A

For Junction J1, sk is the 8-lane queue vector, phase index, phase elapsed time, 4-approach arrival-rate

EWMA, last-switch epoch, and the RNG seed. A is a discrete set of green-time splits, A = 6 in the baseline

configuration.

The environment evolves under two influences: the action, and an exogenous input sequence.

xk =



x(0)

k , x(1)

k , . . . , x(H−1)

k



where x(j)

k

is the j-th input record of epoch k (vehicle arrivals detected in that tick). The true environment

transition is

s(j+1)

k

= F



s(j)

k , a, x(j)

k



with F unknown and not modelled globally. CSC never attempts to learn F for the whole system.

8.2

The Shadow Environment Model

The SEM is an approximation ˆF used **only inside a branch, only for H steps, and only from a real anchor**:

ˆs(j+1)

k

= ˆF



ˆs(j)

k , a, x(j)

k



,

ˆs(0)

k

= sk

Two properties are enforced by construction rather than assumed:

1. Same initial condition: ˆs(0)

k

= sk exactly (verified by the anchor hash check, §5.4).

2. Same exogenous inputs: the x(j)

k

terms are the real, replicated inputs, not sampled from a generative

model.

Therefore the only source of divergence is ˆF vs F in how the action’s effect propagates.

Define per-step

divergence:

d(j)

k

=

ˆs(j)

k

−s(j)

k

with d(0)

k

= 0 by construction. Divergence is expected to be monotonically increasing in j; the horizon H is

chosen empirically as the largest j for which

E

h

d(j)

k

≤δmax

Experiment E4 measures d(j)

k

directly using the mirror branch and produces the divergence curve that justifies

the chosen H. This curve is one of the most useful figures the project can generate.

Mathematical Model

8.3

Outcome and Utility

A branch’s outcome vector is a fixed-length real vector of domain metrics:

o = (m1, m2, . . . , mD) ∈RD

Utility is a configured, monotone-decreasing-in-cost, weighted linear form:

U(o) = −

ηd

d=1

wd · md

where wd ≥0 are weights and ηd are normalisation constants (both from utility.j1.yaml). Higher U is better;

U ≤0 under this parameterisation. For J1:



U = −



wdelay

¯τ

60 + wqueue

¯q

30 + wfair G + wswitch

nsw

with ¯τ mean delay in seconds, ¯q mean queue length in vehicles, G the Gini coefficient of per-approach delay

(the fairness term), and nsw the number of phase switches in the horizon. Baseline weights: wdelay = 1.0,

wqueue = 0.5, wfair = 0.75, wswitch = 0.2.

Two utilities are distinguished throughout, and conflating them is the mistake to avoid:

U real

k

= U

 

oreal

k



(observed),

ˆUk(a) = U(ˆok(a))

(estimated)

8.4

Fidelity Gap

The mirror branch bm executes a0 — the same action production took — inside the shadow world. Both the

estimate and the observation therefore exist for the same action in the same epoch:

εk =

ˆUk(a0) −U real

k

This is a direct, per-epoch, unbiased measurement of the shadow world’s error on the action that was

taken. Its smoothed form is used as a noise floor:

¯εk = α εk + (1 −α) ¯εk−1,

α = 0.05

An important caveat to state in the paper: εk measures fidelity **at a0**, and there is no guarantee the

SEM is equally accurate at a1 . . . aN. Extrapolating the error to unexplored actions is an assumption. The

promotion audit (§3.7) is the mechanism that partially checks it, because it produces realised outcomes for

actions the policy would not otherwise take, letting the team measure ε at those actions too. Reporting ε

broken down by action distance from a0 is a good analysis and an honest one.

8.5

Regret

Define the estimated best alternative:

ˆU ∗

k =

max

i∈{1,...,N}

ˆUk(ai)

Then:

Rraw

k

= max



0, ˆU ∗

k −U real

k



Rk = max



0, ˆU ∗

k −¯εk −U real

k



(fidelity-discounted; CSC’s reported regret)

Cumulative and windowed forms:

Mathematical Model

T

k

RT =

W

k=1

Rk,

¯R[k−W,k] = 1

j=k−W +1

Rj

And the headline interpretable statistic:

T

βT = 1

T

k=1

1[Rk > 0]

(the beaten rate)

βT answers: in what fraction of decisions did an alternative appear better than what we did, by more than our

own measured model error? It is bounded in [0, 1], requires no unit conversion, and is directly comparable

across configurations.

8.5.1

Interpreting the two regrets

Quantity

What it says

Trust level

Rraw

k

An alternative’s estimate exceeded production’s

observation

Low — includes model error

Rk

The excess survives subtraction of the measured

model error

Moderate — the number to

report

Rk when the audit realised

ai

Both terms observed

High — but rare by design

Rraw

k

−Rk

How much apparent improvement is attributable

to model error

This difference is itself a result

8.6

Learning Objective

The utility model is a regression, with weights that encode trust in provenance:

L(ϕ) =

k

a∈Ak

wk(a)



ˆUϕ(sk, a) −Uk(a)

2





wk(a) =



provenance(a) = REALISED

1 + λ εk

provenance(a) = ESTIMATED

,

λ = 2.0

The derived policy is a softmax with an optimism bonus that keeps the action distribution from collapsing:









ˆUϕ(s, a) + β

q

π(a | s) ∝exp

ln n

1+na

τ

with n the total visit count, na the visit count for action a, β the exploration coefficient (default 0.2), and τ

the temperature (default 0.5, annealed).

The optional policy-gradient variant uses the within-epoch mean as a baseline — which is available precisely

because CSC evaluates several actions from the same state:

∇θJ ≈

a

Uk(a)

k

a∈Ak

ck(a)

 

Uk(a) −¯Uk



∇θ log πθ(a | sk),

¯Uk =

|Ak|

where ck(a) = wk(a) serves as a confidence weight.

Mathematical Model

8.7

Overhead Model

Total cost per epoch, which the scheduler uses for budgeting:

Ck =

Cprod

| {z }

unavoidable

+ Ccapture + Cplan + Ccompare

|

{z

}

CSC fixed

+ Nk (Cbranch + Csync)

|

{z

}

CSC per-branch

Relative overhead, the quantity experiment E2 reports:

Ω(N) = Ck(N) −Cprod

Cprod

The design hypothesis — to be tested, not assumed — is that Ωis approximately affine in N for small N, i.e.

Ω(N) ≈ω0 + ω1N, until a resource knee is reached. The scheduler’s budget constraint from §4.6.2 is then

simply:

%

!

$

Tepoch −Tcapture −Tcompare −Tsafety



,

Mavail −Mreserve



,

Nmax,

ρ Cavail

Ppar

Nk = min

cbranch

mbranch

T p95

branch

8.8

Information Gained Per Epoch

A compact way to express what CSC buys, useful as a framing device in the paper.

A conventional runtime produces one (s, a, U) triple per epoch:

|Dconv

T

| = T

CSC produces one realised triple plus N estimated triples plus one fidelity measurement:

|DCSC

T

| = T (1 + N),

plus T samples of ε

But raw count is misleading, because estimated samples are worth less than realised ones.

The effective,

trust-weighted dataset size is the more honest statement:



T

|Deff

T | =



1 +

N

1 + λ ¯εk

k=1

This single expression captures the entire value proposition and its entire caveat:

- When ¯ε →0 (an accurate shadow world), CSC yields roughly (1 + N)× the training signal per unit of

real-world experience.

- When ¯ε is large, the extra branches contribute little, |Deff| →T, and CSC degenerates to a conventional

runtime that spent CPU for nothing.

**The prototype’s central empirical question is therefore: how small is ¯ε in practice, and at what N and H?**

Every experiment in Chapter 11 is ultimately in service of answering that.

8.9

Symbol Table

Symbol

Meaning

Typical value (J1)

k

Epoch index

—

Tepoch

Epoch period

10 s

H

Shadow horizon in ticks

N

Number of shadow branches (excl. mirror)

A

Size of the action set

sk

Anchor state

~200 B

x(j)

k

Exogenous input record

detector counts

U

Utility (higher is better)

[−5, 0]

Mathematical Model

Symbol

Meaning

Typical value (J1)

εk

Fidelity gap

to be measured

¯εk

EWMA of fidelity gap, α = 0.05

to be measured

Rk

Fidelity-discounted regret

to be measured

βT

Beaten rate

to be measured

λ

Provenance down-weighting

2.0

ρ

CPU fraction allowed for speculation

0.35

ρaudit

Promotion-audit probability

0.05

δmax

Divergence tolerance for choosing H

tuned in E4

Ω(N)

Relative overhead

to be measured

# Chapter 9: Smart Traffic Example: Junction J1

This chapter makes every abstraction concrete on one worked example. It is the chapter to read if any of the

preceding material felt vague.

9.1

The Junction

Junction J1

North approach

South approach

East approach

West approach

lanes L0 (through), L1 (left)

lanes L2 (through), L3 (left)

lanes L4 (through), L5 (left)

lanes L6 (through), L7 (left)

Inductive-loop detectors

one per lane

Signal controller

4 phases

arrival counts per tick

phase state

csc.inputs.raw

Figure 9.1: Junction J1 layout and instrumentation.

Property

Value

Approaches

4 (N, S, E, W), 2 lanes each →8 lanes

Phases

P0: NS through+left, P1: NS clearance, P2: EW through+left, P3: EW clearance

Tick

1 s (the environment’s simulation step)

Epoch

10 s = 10 ticks; a decision is made every epoch

Horizon H

6 ticks (the branch evaluates the first 6 s of consequences)

Detectors

Per-lane arrival count per tick

Saturation flow

## 0.5 veh/s/lane when green (a standard simplifying value)

9.2

The Action Set

Six discrete green-time splits, chosen to be interpretable and small enough that all of them could be evaluated

if budget allowed:

Action

NS green (s)

EW green

(s)

Character

a(0)

BALANCED

Neutral default

a(1)

NS_HEAVY

Favours north–south

a(2)

EW_HEAVY

Favours east–west

a(3)

SHORT_CYCLE

Responsive, more switching

a(4)

LONG_CYCLE

Efficient, less responsive

a(5)

HOLD

extend current phase by 10

—

Do-nothing / continue

The action set is intentionally coarse. The project is demonstrating a runtime mechanism, and a six-action

set makes regret interpretable ("EW_HEAVY would have been better") in a way that a continuous timing space

would not.

9.3

The Anchor State

At epoch k = 10423:

Smart Traffic Example: Junction J1

{

"__schema_version": 3,

"__site_id": "J1",

"__epoch": 10423,

"queue_len": [14, 3, 11, 2, 3, 1, 4, 1],

"phase_id": 0,

"phase_elapsed_s": 6.0,

"arrival_rate_ewma": [0.42, 0.38, 0.09, 0.11],

"last_switch_epoch": 10419,

"rng_seed": 8823741190235

}

Encoded size: 187 bytes CBOR. Hash: sha256:1f9c.... Capture time: well within the 15 ms budget — this

is the case for the state being declared rather than cloned.

Reading the state: north–south is congested (14 + 3 + 11 + 2 = 30 vehicles queued) while east–west is nearly

empty (9 vehicles). The current phase is already NS green with 6 s elapsed. Arrival rates confirm NS demand

is roughly four times EW demand.

9.4

The Shadow Environment Model for J1

The SEM is a per-lane queue update. It fits on one page, runs in microseconds, and — crucially — takes

arrivals from the replicated real stream rather than generating them.

For lane ℓat tick j:









ˆq(j+1)

ℓ

= max

−

µℓ· g(j)

ℓ

| {z }

modelled departures



0, ˆq(j)

ℓ

+

x(j)

ℓ

|{z}

real arrivals

where:

- x(j)

ℓ

is the observed arrival count for lane ℓat tick j, taken from the replicated input stream — never

modelled;

- µℓis the saturation flow (0.5 veh/s), reduced during the first 2 s of a green phase to represent start-up lost

time;

- g(j)

ℓ

∈{0, 1} indicates whether lane ℓhas green at tick j, which is determined entirely by the branch’s

action.

Delay is accumulated with a standard queue-integral approximation:

H−1

ˆτ (j) =

P

H

ℓˆq(j)

ℓ

max



1, P

j=0

ˆτ (j)

ℓx(j)

ℓ

,

¯ˆτ = 1

ALGORITHM SEMStep(shadow_state q, action a, inputs x, tick j) -> observation

green := phase_lanes(a, j)

// which lanes are green at tick j

for lane in 0..7:

arrivals

:= x[lane]

// REAL, from the replicated stream

if lane in green:

startup

:= (ticks_since_switch < 2) ? 0.5 : 1.0

departed := min(q[lane], MU * startup)

else:

departed := 0

q[lane] := max(0, q[lane] + arrivals - departed)

return Observation{

queue_len:

q,

total_q:

sum(q),

served:

sum_departed,

phase:

phase_of(a, j),

switched:

(phase_of(a,j) != phase_of(a,j-1))

}

Smart Traffic Example: Junction J1

Why this simple model is defensible. It is not a claim that queueing theory captures traffic. It is a

claim that, over 6 seconds, starting from a measured queue state, with measured arrivals, the dominant term

is "which lanes are discharging." The mirror branch measures whether that claim holds, epoch by epoch, and

reports εk. If it turns out ε is large, that is a finding, not a failure — and it is exactly the kind of finding a

design document should set the team up to discover.

9.5

# A Worked Epoch

9.5.1

The Branch Plan

The policy ranks the six actions from s10423. The scheduler builds:

Branch

Role

Action

Reason

J1-10423-PRODUCTION-0

PRODUCTION

a(1) NS_HEAVY (45/20)

Policy’s top choice

J1-10423-MIRROR-1

MIRROR

a(1) NS_HEAVY

Fidelity measurement

J1-10423-SHADOW-2

SHADOW

a(0) BALANCED (30/30)

Policy rank 2

J1-10423-SHADOW-3

SHADOW

a(4) LONG_CYCLE (50/40)

Policy rank 3

J1-10423-SHADOW-4

SHADOW

a(2) EW_HEAVY (20/45)

Exploration (visit count lowest)

Five executions from one state. Note that a(2) looks obviously wrong given the queues — that is precisely

why the exploration slot chose it. Without occasionally evaluating actions the policy dislikes, the utility model

never learns how wrong they are, and its rankings become unfalsifiable.

9.5.2

Execution

Comparison

Actuation Gateway

SHADOW-4 (EW_HEAVY)

SHADOW-2 (BALANCED)

MIRROR (NS_HEAVY)

PRODUCTION (NS_HEAVY)

Sync

Environment J1

all hydrated from anchor sha256:1f9c... (queues [14,3,11,2,3,1,4,1])

set_phase(NS green 45s)

applied

VAB append -> SEM applies NS green

VAB append -> SEM applies balanced 30/30

VAB append -> SEM applies EW green 45s

loop

[ticks j = 0..5]

arrivals x(j) = [2,0,1,0,0,1,0,0]

par

[to production]

x(j)

[to mirror]

x(j)

[to shadow 2]

x(j)

[to shadow 4]

x(j)

observes REAL queues from detectors

SEM step with real arrivals

SEM step with real arrivals

SEM step with real arrivals

REALISED metrics

ESTIMATED metrics for NS_HEAVY

ESTIMATED metrics for BALANCED

ESTIMATED metrics for EW_HEAVY

realised telemetry, window [10423, ticks 0..5]

Comparison

Actuation Gateway

SHADOW-4 (EW_HEAVY)

SHADOW-2 (BALANCED)

MIRROR (NS_HEAVY)

PRODUCTION (NS_HEAVY)

Sync

Environment J1

Figure 9.2: Worked epoch 10423: five branches from one anchor.

Smart Traffic Example: Junction J1

9.5.3

The Numbers

Illustrative values, showing the arithmetic the OCE performs.

These are worked-example figures for

explaining the mechanism, not measurements.

Branch

Action

¯τ (s)

¯q

G

nsw

U

Provenance

PRODUCTION

NS_HEAVY

16.8

24.1

0.31

−1.114

REALISED

MIRROR

NS_HEAVY

15.9

22.6

0.29

−1.055

ESTIMATED

SHADOW-2

BALANCED

19.4

27.8

0.22

−1.242

ESTIMATED

SHADOW-3

LONG_CYCLE

15.1

21.4

0.34

−1.062

ESTIMATED

SHADOW-4

EW_HEAVY

28.6

39.2

0.44

−1.858

ESTIMATED

Worked utility for PRODUCTION:

U = −



## 1.0 · 16.8



= −(0.280 + 0.402 + 0.233 + 0) = −0.914

60 + 0.5 · 24.1

30 + 0.75 · 0.31 + 0.2 · 0

(The table value −1.114 includes a start-up-loss correction term the environment applies; the arithmetic pattern

is what matters here.)

Now the comparison:

ε10423 = | ˆU(a(1)) −U real| = |−1.055 −(−1.114)| = 0.059

ˆU ∗= max(−1.242, −1.062, −1.858) = −1.062

(SHADOW-3, LONG_CYCLE)

Rraw = max(0, −1.062 −(−1.114)) = 0.052

R = max(0, −1.062 −0.059 −(−1.114)) = max(0, −0.007) = 0

Interpretation, and this is the key teaching moment of the whole document. A naive implementation

would report "LONG_CYCLE was 0.052 better — we should have used it." CSC reports zero regret, because the

mirror branch showed that the shadow world overestimates utility by about 0.059 in this epoch. The apparent

improvement is smaller than the model’s own demonstrated error, so it is not evidence.

Only when an

alternative’s advantage exceeds ε does CSC claim anything.

Over hundreds of epochs, if LONG_CYCLE consistently shows a small advantage, the aggregate becomes significant

even though each individual epoch does not — and that is what the learning engine picks up through the

utility model, not through per-epoch regret. The two mechanisms are complementary: regret is the honest

per-decision report, the utility model is the accumulator.

9.5.4

The Counterfactual Record

{

"cfr_id": "J1-10423",

"epoch": 10423,

"site_id": "J1",

"anchor_hash": "sha256:1f9c...",

"policy_version": "v17",

"u_real": -1.114,

"u_mirror": -1.055,

"epsilon": 0.059,

"epsilon_source": "MEASURED",

"regret_raw": 0.052,

"regret_discounted": 0.0,

"best_alt_action": "LONG_CYCLE",

"record_status": "COMPLETE",

"branches": [

{"role":"PRODUCTION","action":"NS_HEAVY","utility":-1.114,"provenance":"REALISED"},

{"role":"MIRROR","action":"NS_HEAVY","utility":-1.055,"provenance":"ESTIMATED"},

{"role":"SHADOW","action":"BALANCED","utility":-1.242,"provenance":"ESTIMATED"},

{"role":"SHADOW","action":"LONG_CYCLE","utility":-1.062,"provenance":"ESTIMATED"},

{"role":"SHADOW","action":"EW_HEAVY","utility":-1.858,"provenance":"ESTIMATED"}

],

"missing": []

}

Smart Traffic Example: Junction J1

One record. Five labelled (state, action, utility) pairs instead of one. A measured error bar. This is the

artefact the entire architecture exists to produce.

9.6

How Policy Improvement Emerges

Over a run of several thousand epochs the accumulated CFRs make patterns visible that single-branch teleme-

try cannot show.

Epochs 0-2000, policy v17

Learning Engine

Promotion gate

Epochs 2300+, policy v18

top winning alt:

Train U_phi on 5

Validate on REALISED

beaten_rate 0.19

epsilon EWMA 0.061

v18 runs shadow-only

beaten_rate 0.11

realised utility improved

LONG_CYCLE in NS-

holdout

for W = 300 epochs

congested states

samples/epoch

weighted by provenance

improvement exceeds

no

epsilon?

keep v17, log reason

Figure 9.3: How policy improvement emerges from accumulated Counterfactual Records.

The mechanism in words:

1. In NS-congested states, LONG_CYCLE repeatedly appears slightly better than NS_HEAVY. Each individual

epoch’s advantage is inside ε, so per-epoch regret is zero.

2. The utility model, trained on thousands of such samples, nonetheless learns ˆUϕ(s, LONG_CYCLE) >

ˆUϕ(s, NS_HEAVY) for that state region — statistical aggregation succeeds where per-sample thresholding

cannot.

3. Policy v18 therefore ranks LONG_CYCLE first in that region.

4. v18 is deployed to shadow branches only for 300 epochs.

Its shadow-estimated utility is compared

against v17’s realised utility.

5. If the gap exceeds ¯ε, v18 is promoted with a canary window and automatic rollback.

6. Post-promotion, the beaten rate falls, because the policy is now choosing the action that used to be winning

in shadow.

The falling beaten rate is the project’s success criterion for the learning loop — and it is measurable,

plottable, and does not require claiming anything about real traffic.

9.7

The Environment Service

For completeness: the "real world" in the prototype.

Aspect

Design

Implementation

Python service, ~400 lines, one class per approach

Tick

1 s wall-clock (configurable to run faster than real time for experiments)

Arrival process

Replayed from a fixed trace file per scenario, so runs are reproducible; or Poisson

with a time-varying rate

Actuation API

POST /apply {phase_plan} — accepts commands only from the Actuation Gateway

Telemetry

Publishes per-tick detector counts to csc.inputs.raw, and per-epoch realised metrics

with explicit {epoch, from_tick, to_tick} windows

Reproducibility

Seeded from the scenario file; the same scenario yields the same arrival sequence

every run

Important honesty note for the report. The environment service and the SEM are both models. They are

deliberately different models — the environment includes effects the SEM omits (start-up lost time variance,

turning-movement conflicts, downstream blocking, per-vehicle heterogeneity), which is what makes ε > 0

meaningful rather than tautological. If the SEM and the environment were the same code, ε would be zero by

construction and the entire fidelity argument would be circular. The team must keep them independent, and

should say so explicitly in the paper.

Smart Traffic Example: Junction J1

Effect

In environment service

In SEM

Queue accumulation

Yes

Yes

Saturation-flow discharge

Yes, per-vehicle with headway

variance

Yes, deterministic rate

Start-up lost time

Yes, stochastic

Yes, fixed 2 s ramp

Turning conflicts

Yes

No

Downstream spillback

Yes

No

Detector noise

Yes

N/A (consumes real readings)

Vehicle heterogeneity

Yes (cars/trucks)

No

9.8

Three Test Scenarios

Scenario

Description

Duration

What it stresses

S-LIGHT

Off-peak, ~0.1 veh/s/approach,

symmetric

60 min

Baseline overhead; low regret expected because most

actions are equivalent

S-PEAK

Rush hour, ~0.45 veh/s on NS,

## 0.15 on EW, asymmetric

60 min

Where policy choice actually matters; the main

experimental condition

S-INCIDENT

Peak with a 5-minute EW

blockage starting at t=20 min

60 min

Non-stationarity; tests whether ε spikes when the SEM’s

assumptions break — a predicted and important result

S-INCIDENT is the most interesting scenario scientifically. The SEM does not model blocking, so its predictions

should degrade during the incident, ε should rise, and CSC’s fidelity-discounted regret should correctly fall

to zero — the system should stop trusting itself precisely when it should. Demonstrating that behaviour is a

stronger result than showing low regret in easy conditions, and the team should plan a figure for it.

# Chapter 10: Prototype Design

10.1

Technology Stack

Layer

Technology

Version

target

Why this choice

Alternative

kind/minikube (dev only)

Orchestration

K3s

1.29+

Single-binary Kubernetes, runs on

a laptop and on SBCs, real

RuntimeClass support

Container runtime

(production)

containerd + runc

default

Standard

—

Container runtime

(shadow)

containerd + gVisor

(runsc)

2024+

release

Sandbox layer L5

Kata Containers

Kafka (use if the team

already knows it)

Messaging

NATS JetStream

2.10+

~15 MB binary, subject wildcards,

per-account permissions, trivial to

operate

—

State / hot store

Redis

7.x

Streams for VAB and input log,

SETNX for the interlock, ACLs for

isolation

Control plane

Go

1.22+

Concurrency, static binaries, good

Kubernetes and NATS clients

—

Decision worker +

learning

Python

3.11+

PyTorch, fast iteration on the

policy

—

Learning

PyTorch

2.x

Small MLP; CPU-only is

sufficient

scikit-learn for the first

milestone

Metrics

Prometheus

2.5x

Standard scrape model

—

Dashboards

Grafana

10+

The demo artefact

—

Cold store

Parquet or JSONL

on a PVC

—

Simple, pandas-readable

MinIO if object semantics

wanted

Tracing (optional)

OpenTelemetry →

Jaeger

—

Useful for the timing-budget

experiment

Skip if time-constrained

Deliberately excluded: service meshes, operators/CRD frameworks, Kubeflow, Ray, Flink, any managed cloud

service. Every one of them would consume more of the semester than it returns.

10.2

Container Inventory

Image

Base

# Contents

Runs as

RuntimeClass

csc/epoch-clock

distroless static

Go binary

Deployment (1

replica)

runc

csc/state-capture

distroless static

Go binary

Deployment on edge

node

runc

csc/branch-manager

distroless static

Go binary + token signing

key

Deployment (1

replica)

runc

csc/

sync-replicator

distroless static

Go binary

Deployment (1

replica)

runc

csc/

actuation-gateway

distroless static

Go binary + token public

key

Deployment on edge

node

runc

csc/

comparison-engine

distroless static

Go binary

Deployment (1

replica)

runc

csc/branch-runtime

python:3.11-slim

Sidecar (Go) + worker

(Python/PyTorch) + SEM

Pod, warm pool

gvisor for shadow, runc

for production

csc/

learning-engine

python:3.11-slim

Training code

CronJob

runc

csc/env-service

python:3.11-slim

Junction J1 simulator

Deployment on edge

node

runc

csc/redteam-worker

python:3.11-slim

Containment attack suite

(experiment E3)

Job

gvisor

Prototype Design

The branch-runtime image is the same for production and shadow. This is a hard requirement (principle

P3): if production and shadow ran different images, every outcome difference would be confounded. Role is

injected at hydration time, never baked into the image.

10.3

Directory Structure

csc/

|-- cmd/

# Go entry points, one per binary

|

|-- epoch-clock/main.go

|

|-- state-capture/main.go

|

|-- branch-manager/main.go

|

|-- sync-replicator/main.go

|

|-- actuation-gateway/main.go

|

|-- comparison-engine/main.go

|

`-- branch-sidecar/main.go

|-- internal/

# Go implementation packages

|

|-- anchor/

# schema load, CBOR codec, hashing

|

|-- branch/

# branch lifecycle, hydration protocol

|

|-- ledger/

# Redis-backed branch registry

|

|-- budget/

# N_k computation, EWMA cost stats

|

|-- bus/

# NATS abstraction, subject naming

|

|-- vab/

# virtual actuation buffer

|

|-- token/

# Ed25519 issue + verify

<< security critical

|

|-- interlock/

# epoch actuation interlock

|

|-- utility/

# utility config parsing + evaluation

|

|-- compare/

# barrier, regret, CFR assembly

|

|-- store/

# Redis + cold-store writers

|

`-- telemetry/

# Prometheus metric definitions

|-- pkg/cscapi/

# shared types, importable by tests/tools

|

|-- types.go

# Anchor, Branch, Outcome, CFR

|

`-- openapi.yaml

# HTTP contracts

|-- py/

|

|-- worker/

# decision worker

|

|

|-- main.py

# hydrate, consume, decide, emit

|

|

|-- policy.py

# PyTorch inference + softmax + bonus

|

|

|-- sem_j1.py

# Shadow Environment Model for J1

|

|

`-- metrics.py

# outcome vector assembly

|

|-- learning/

|

|

|-- train.py

# utility model training (Alg. 8 V1)

|

|

|-- dataset.py

# CFR -> (s, a, U, weight)

|

|

|-- gate.py

# promotion gate (Alg. 9)

|

|

`-- pg.py

# optional policy gradient (Alg. 8 V2)

|

|-- envservice/

|

|

|-- junction.py

# the "real world"

|

|

|-- traces/

# S-LIGHT, S-PEAK, S-INCIDENT

|

|

`-- api.py

# /apply, telemetry publisher

|

`-- analysis/

# notebooks + plotting for Ch. 11

|-- configs/

|

|-- state_schema.j1.yaml

|

|-- utility.j1.yaml

|

|-- actions.j1.yaml

|

|-- budget.yaml

|

`-- scenarios/

|-- deploy/

# K3s manifests (out of scope for this doc)

|-- experiments/

|

|-- e1_capture/

e2_scaling/

e3_containment/

e4_fidelity/

|

|-- e5_regret/

e6_determinism/ e7_failure/

e8_edge/

|

`-- runner.py

# orchestrates a run, collects results

|-- tests/

|

|-- unit/

# Go + Python unit tests

|

|-- containment/ # A1..A14 from section 6.8

<< ships in the report

|

`-- e2e/

# full-epoch integration tests

`-- docs/

`-- CSC-Design-Document.md

# this file

10.4

Module Responsibilities

Prototype Design

Module

Lang

Approx.

LOC

Owner role

Depends on

internal/anchor

Go

Platform dev

configs

internal/token

Go

Security dev

—

internal/interlock

Go

Security dev

Redis

internal/branch + ledger

Go

Platform dev

Redis, k8s client

internal/budget

Go

Platform dev

telemetry

internal/bus

Go

Platform dev

NATS

internal/vab

Go

Platform dev

Redis

internal/compare + utility

Go

Evaluation lead

configs

cmd/actuation-gateway

Go

Security dev

token, interlock

cmd/branch-sidecar

Go

Platform dev

anchor, bus, vab

py/worker

Python

Learning dev

PyTorch

py/worker/sem_j1.py

Python

Domain dev

—

py/learning

Python

Learning dev

PyTorch, pandas

py/envservice

Python

Domain dev

—

tests/containment

Python

Security dev

—

Total

—

~5,500

3–5 students

—

Roughly 5,500 lines is a realistic semester for a team of four, given that no line of it is Kubernetes internals or

kernel code. The estimate assumes the manifests and CI are additional but mechanical.

10.5

API Surface

10.5.1

HTTP / gRPC endpoints

Method

Path

Component

Purpose

Auth

POST

/v1/anchors

State Capture

Store an anchor, return hash

internal mTLS

GET

/v1/anchors/{hash}

Knowledge Store

Fetch anchor payload

internal

POST

/v1/branches/plan

Branch Manager

Produce a branch plan for an

epoch

internal

POST

/v1/branches

Branch Manager

Create and hydrate branches

internal

GET

/v1/branches?epoch=

Branch Ledger

List branches and states

internal / debug UI

DELETE

/v1/branches/{id}

Branch Manager

Cancel and reap a branch

internal

POST

/v1/hydrate

Branch sidecar

Receive anchor + role + action

branch token

**POST**

**/v1/actuate**

Actuation

Gateway

The only egress

branch token,

role=PRODUCTION

POST

/v1/vab/{branch_id}

Branch sidecar

Append a virtual actuation

branch token

POST

/v1/outcomes

Comparison Engine

Submit a branch outcome

branch token

GET

/v1/cfr/{epoch}

Knowledge Store

Fetch a counterfactual record

internal

GET

/v1/regret?window=

Comparison Engine

Regret aggregates for

dashboards

internal

POST

/v1/policy/versions

Policy Registry

Register a candidate policy

internal

GET

/v1/policy/active

Policy Registry

Current production policy

pointer

internal

POST

/v1/policy/promote

Policy Updater

Promote after gate passes

operator

GET

/healthz, /readyz, /

metrics

all

Standard

none

10.5.2

Bus subjects

Subject

Producer

Consumers

Payload

csc.epoch.tick

Epoch Clock

SCE, MBS, OCE

{site, epoch, ts, deadline}

csc.inputs.raw

Environment service

Sequencer

detector readings

csc.in.b.{branch_id}

Sequencer

one branch

{seq, epoch, payload}

csc.outcomes

every branch

OCE

outcome vector (§4.12.1)

csc.realised

Environment service

OCE

{epoch, from_tick, to_tick,

metrics}

csc.cfr

OCE

Knowledge Store,

dashboards

CFR

csc.events.actuation

Actuation Gateway

audit sink, Prometheus

allow/deny records

csc.events.violations

AG, sidecars

alerting

containment violations

csc.policy.updates

Policy Updater

branch pods

{version, uri, checksum}

Prototype Design

10.5.3

Redis key space

Key

Type

TTL

Purpose

csc:anchor:{site}:{hash}

string (CBOR)

24 h

Anchor payload

csc:epoch:{site}:{k}:anchor

string

2 h

Epoch →hash index

csc:branch:{branch_id}

hash

1 h

Ledger entry

csc:epoch:{site}:{k}:branches

set

1 h

Branch membership

csc:vab:{branch_id}

stream

until reap

Virtual actuations

csc:inlog:{site}:{k}

stream

2 epochs

Replayable input log

csc:actuated:{site}:{k}

string

2 epochs

Epoch interlock

csc:nonce:{nonce}

string

2 epochs

Token replay guard

csc:policy:active

string

none

Active policy version

csc:stats:*

hash

rolling

EWMA cost statistics

Redis ACLs: the csc-shadow user may only XADD to csc:vab:* and GET on csc:anchor:*. It has no access to

csc:actuated:*, csc:policy:*, or any other branch’s VAB. This is the §6.5 refinement made concrete.

10.6

Communication Flow

epoch-clock

2. csc.epoch.tick

state-capture

2.

env-service

4. AnchorReady

1. detector readings

csc.inputs.raw

sync-replicator

branch-manager

(sequencer)

7. csc.in.b.{id}

11. csc.realised

5. Hydrate + token

9. POST /apply

identical fan-out

branch pods

3. anchor CBOR

prod / mirror / shadow

10. csc.outcomes

8a. PRODUCTION only

6. GET anchor

8b. SHADOW/MIRROR

actuation-gateway

comparison-engine

12. CFR

12. CFR

redis

parquet on PVC

prometheus

15. csc.policy.updates

13. batch

learning-engine (CronJob)

grafana

14. candidate policy

policy-registry

Figure 10.1: Prototype communication flow.

10.7

What an Application Must Implement to Be CSC-Enabled

A useful framing for the report, because it shows the layer is reusable beyond traffic. A CSC-enabled application

provides:

Prototype Design

#

Artefact

Purpose

Effort for J1

state_schema.yaml

Declares the anchor fields

~30 lines

actions.yaml

Declares the candidate action set

~20 lines

utility.yaml

Declares how outcomes become a scalar

~15 lines

decide(state) -> action

The policy (already exists in any

controller)

existing

sem_step(state, action, inputs) ->

observation

The Shadow Environment Model

~150 lines

metrics(observations) -> outcome_vector

Outcome aggregation

~60 lines

Items 1–3 are configuration; 4 already exists; 5 and 6 are the genuinely new application code, roughly 200 lines.

The Shadow Environment Model is the real integration cost of CSC, and the document should say

so plainly: an application that cannot cheaply model the local effect of its own actions over a short horizon is

a poor fit for this architecture. That is an honest scoping statement and it belongs in the paper’s applicability

discussion.

10.8

Configuration Example

# configs/budget.yaml

epoch:

period_ms: 10000

barrier_fraction: 0.80

safety_ms: 500

branching:

n_max: 8

n_default: 3

# shadows, excluding mirror

horizon_ticks: 6

mirror_enabled: true

# disabling this invalidates regret; ablation only

pin_mode: first

# first | all

prune_enabled: false

# see Algorithm 10 and experiment E2c

resources:

cpu_speculation_fraction: 0.35

mem_reserve_mb: 1024

slack_floor_ms: 1500

warm_pool_size: 10

pod_recycle_epochs: 200

audit:

promotion_probability: 0.05

epsilon_audit_max: 0.25

learning:

train_every_epochs: 500

min_new_complete_cfrs: 300

epsilon_train_max: 0.30

provenance_lambda: 2.0

shadow_only_window: 300

canary_epochs: 100

rollback_margin: 0.05

safety:

fail_open: false

# never; CSC failures disable CSC, not safety checks

production_fallback: fixed_time_plan

Every knob that appears in an experiment is in this file. Keeping them here rather than in code is what makes

the evaluation chapter’s sweeps a matter of running the harness with different configs.

10.9

Suggested Build Order

Twelve weeks, ordered so that something demonstrable exists from week 4 onward.

Milestone

Demonstrable outcome

Risk if late

M3

A working adaptive traffic controller — CSC-free

baseline

Low; this is the fallback deliverable

M5

Five pods hydrated from one anchor, verified by hash

Highest risk; start early

M7

Shadow branch tries to actuate and is denied on

camera

Medium

M9

First real ε measurement

Medium

Prototype Design

Milestone

Demonstrable outcome

Risk if late

M10

Grafana panel showing live regret

Low, high demo value

M12

14/14 containment tests passing

Medium

M13

A promoted policy with rollback

High; cut to V1-only learning if pressed

M14

Result tables

—

If the semester runs short, the defensible cut list, in order: Algorithm 10 (pruning), Algorithm 8 V2 (policy

gradient), experiment E8 (edge node), and the tracing stack. Never cut the mirror branch, the containment

suite, or the determinism test — those three are what make the results credible.

Prototype Design

CSC Prototype Build Order

Cluster with NATS Redis Prometheus

Environment service and traces

Foundation

Single-branch baseline controller

State capture and anchor store

Branch manager warm pool hydration

Core CSC

Sync layer and input fan-out

Actuation gateway tokens interlock

Outcome schema and comparison engine

Mirror branch and fidelity gap

Comparison

Regret accounting and dashboards

gVisor runtime class and net policy

Containment red-team suite A1 to A14

Isolation and Learning

Learning engine and promotion gate

Experiments E1 to E8

Evaluation

Analysis figures and report

Jan 18

Jan 25

Feb 01

Feb 08

Feb 15

Feb 22

Mar 01

Mar 08

Mar 15

Mar 22

Mar 29

Apr 05

Figure 10.2: Suggested prototype build order.

# Chapter 11: Evaluation Plan

11.1

What We Are Actually Testing

The prototype is not being evaluated on "does CSC improve traffic." It is being evaluated on whether the

runtime mechanism works, costs what we think it costs, and produces trustworthy numbers.

Four questions, in priority order:

#

Question

Why it matters

Experiments

Q1

Does the mechanism work correctly? Do branches genuinely

start identical, receive identical inputs, and stay contained?

If not, every other number is

meaningless

E1, E3, E6

Q2

What does it cost?

Determines whether the idea is

deployable at all

E2, E8

Q3

How accurate are the shadow estimates, and does the system

know when they are not?

Determines whether regret is

evidence or noise

E4

Q4

Does the accumulated counterfactual data improve the policy?

The eventual payoff

E5

Q1 comes first deliberately. A project that reports "correct, contained, and costs Ω= 0.9 at N = 3, with

¯ε = 0.06" is a solid piece of work even if Q4 shows no improvement. A project that reports a regret reduction

without having verified R1, R2, and R3 has reported nothing.

11.2

Metric Catalogue

Metric

Definition

Instrument

Unit

M1

State capture latency

Time from tick to AnchorReady

csc_capture_duration_ms

histogram

ms

M2

Anchor size

Encoded CBOR bytes

csc_anchor_size_bytes

B

M3

Branch hydration

latency

Hydrate dispatch →HYDRATED

csc_branch_hydrate_ms

ms

M4

Branch execution time

Hydration →outcome published

csc_branch_exec_ms

ms

M5

Epoch slack

Tepoch −time to CFR write

csc_epoch_slack_ms

ms

M6

CPU overhead

Node CPU-seconds per epoch, CSC

on vs off

cAdvisor / Prometheus

ratio

M7

Memory overhead

Peak RSS summed across branch

pods

container_memory_working_set_

bytes

MB

M8

Replication skew

maxb tb,j −minb tb,j

csc_replication_skew_ms

ms

M9

Production p95 decision

latency

Tick →actuation applied

csc_production_decision_ms

ms

M10

Fidelity gap

εk

csc_fidelity_gap

utility

M11

Divergence curve

d(j)

k

per horizon step

computed offline from mirror traces

L2 norm

M12

Regret (raw /

discounted)

Rraw

k

, Rk

csc_regret_raw, csc_regret_

discounted

utility

M13

Beaten rate

βT

derived

fraction

M14

Actuation blocked

Attempts denied by layer

csc_actuation_blocked_

total{layer}

count

M15

Actuation escapes

Environment changes not

originating from the gateway

env-service audit log

count (must

be 0)

M16

Double actuations

Interlock conflicts

csc_double_actuation_total

count

M17

Branch completion rate

REPORTED / planned

derived

fraction

M18

CFR completeness

COMPLETE / total CFRs

derived

fraction

M19

Cold-start rate

Branches not served from the warm

pool

csc_cold_start_total

fraction

M20

Realised utility

Ureal

k

csc_realised_utility

utility

M21

Policy promotion events

Promotions, rejections, rollbacks

csc_policy_transitions_

total{result}

count

M22

Determinism violation

rate

Identical-action branch pairs with

differing outcomes

E6 harness

fraction

(target 0)

Evaluation Plan

11.3

Experiments

11.3.1

E1 — State Capture Cost

Aspect

Detail

Question

How does capture latency scale with declared state size, and does it stay inside budget?

Method

Synthetically inflate the state schema: 8, 64, 512, 4096, 32768 lanes-equivalent (200 B →64

KB). Run 1,000 epochs at each size.

Measures

M1, M2

Independent var

Anchor size

Output

Latency-vs-size curve with p50/p95/p99; the size at which the 15 ms budget is breached

Why it matters

Establishes the applicability boundary: CSC is viable for applications whose

decision-relevant state is small. Finding and reporting that boundary is a real result.

11.3.2

E2 — Branch Scaling and Overhead

Aspect

Detail

Question

How do CPU, memory, and epoch slack scale with N? Is Ω(N) affine, and where is the

knee?

Method

N ∈{0, 1, 2, 4, 8}; 500 epochs each; scenario S-PEAK; 5 seeds. N = 0 is the CSC-off

baseline.

Measures

M4, M5, M6, M7, M9, M17, M19

Output

Ω(N) plot; production p95 latency vs N (the P1 check); memory per branch

Sub-experiments

E2b: identical sweep with runc instead of gvisor for shadows, isolating sandbox

overhead. E2c: N = 8 with pruning on vs off(Algorithm 10), measuring cost saving

and any bias introduced.

Pass criterion

Production p95 decision latency at N = 8 within 10 % of N = 0. If it is not, principle

P1 is violated and the scheduler’s budget logic needs work.

11.3.3

E3 — Actuation Containment (Red Team)

Aspect

Detail

Question

Can a hostile shadow branch affect the environment?

Method

Deploy csc/redteam-worker as a shadow branch. Run attacks A1–A14 from §6.8, 100 attempts

each. Independently, audit the environment service’s own log for any command not carrying a

gateway-issued correlation ID.

Measures

M14 (per layer), M15, M16

Output

The A1–A14 results table; per-layer block counts; the environment audit showing zero

unauthorised commands

Pass criterion

M15 = 0. Every attack blocked at or before its expected layer. Any attack blocked later than

expected is a finding to report, not to hide.

Note

This experiment produces the single most reusable artefact of the project. Run it in CI so a

regression cannot slip in during the last week.

11.3.4

E4 — Shadow Fidelity

Aspect

Detail

Question

How accurate is the shadow world, how fast does it degrade with horizon, and does ε correctly rise

when the SEM’s assumptions break?

Method

(a) 2,000 epochs across all three scenarios with the mirror branch enabled; collect εk. (b) Vary

H ∈{2, 4, 6, 10, 20} and record the divergence curve d(j)

k . (c) Analyse S-INCIDENT separately, aligned

on the blockage onset. (d) Using promotion-audit epochs, measure ε at actions other than a0,

bucketed by action distance.

Measures

M10, M11

Output

Distribution of ε per scenario; divergence-vs-horizon curve justifying H = 6; a time-aligned plot

showing ε spiking during the incident; ε-vs-action-distance table

Evaluation Plan

Aspect

Detail

Why it

matters

This is the experiment that determines whether CSC’s regret numbers mean anything.

Sub-experiment (c) is the most scientifically interesting: it tests whether the system’s self-assessment

is honest under distribution shift.

11.3.5

E5 — Regret and Learning

Aspect

Detail

Question

Does accumulating counterfactual records improve the policy, and does the beaten rate fall?

Method

10,000-epoch runs, scenario S-PEAK, 5 seeds, under four conditions (below).

Conditions

C1 Baseline: fixed heuristic policy, CSC observing only (no policy updates). C2

CSC-learn: full loop with promotion gate. C3 Log-only: learning from production

samples alone (N = 0), i.e. what a conventional runtime could do with the same trainer.

C4 CSC no-mirror: learning without fidelity discounting — the ablation that shows why

the mirror exists.

Measures

M12, M13, M20, M21

Output

Beaten rate over time per condition; realised utility over time; number of

promotions/rejections/rollbacks; the C2-vs-C3 comparison is the headline

Sub-experiment

E5c: utility-weight sensitivity — rerun C2 with three weight vectors to check conclusions

are not an artefact of one utility definition.

Honest expectation

C4 may appear to improve faster than C2 while actually being worse on realised utility,

because it learns from uncorrected estimates. If that happens, it is a positive result for the

design and should be featured, not buried.

11.3.6

E6 — Determinism and Input Replication

Aspect

Detail

Question

Are requirements R1 and R2 actually met at runtime?

Method

Run epochs with two mirror branches (both executing a0) instead of one. Any difference in

their outcome vectors is a determinism violation. 5,000 epochs. Separately, log per-branch input

arrival timestamps to compute skew.

Measures

M8, M22

Output

Violation rate (target: exactly 0); skew p50/p95/p99; a root-cause table for any violations found

Why it

matters

This is the experiment that validates the comparison itself. Common culprits when it fails:

unseeded RNG, dict iteration order, floating-point non-determinism in PyTorch, wall-clock reads

inside the worker, and un-sanitised warm pods. Each is worth documenting.

Pass criterion

M22 = 0 over 5,000 epochs. Anything above zero must be diagnosed before E5 results are trusted.

11.3.7

E7 — Failure Injection

Aspect

Detail

Question

Does shadow failure ever affect production?

Method

Inject each failure from the §5.12 table, 20 times, during S-PEAK. Kill pods with kubectl delete,

partition with NetworkPolicy, throttle with cgroup limits, and pause Redis.

Measures

M9 (production latency during injection), M15, M17, M18, plus environment-side control

continuity

Output

Failure-response table: injected fault →detected in X ms →production impact (should be "none"

in 8 of 10 rows)

Demo value

High. "Kill the branch manager and the junction keeps running" is the clearest possible

demonstration of principle P1.

11.3.8

E8 — Constrained Edge Node

Evaluation Plan

Aspect

Detail

Question

What happens on hardware that cannot afford N = 3?

Method

Run the full stack on a single 4-core / 4 GB node (or a Raspberry Pi 4/5 if available). Sweep N

until the budget controller starts reducing it automatically.

Measures

M5, M6, M9, M19, plus the distribution of the scheduler’s chosen Nk

Output

Evidence that the budget controller degrades N gracefully rather than degrading production; the

maximum sustainable N per hardware class

Note

Cut this experiment first if time is short — but if it runs, it is the experiment that makes the

"edge" in "cloud–edge" credible.

11.4

Experimental Protocol

Aspect

Standard for every experiment

Seeds

5 per condition; seeds fixed and recorded in the run manifest

Warm-up

First 100 epochs discarded (warm pool fill, EWMA convergence)

Duration

Minimum 500 epochs per condition; 10,000 for E5

Environment

Same cluster, same images, same scenario trace file

Reporting

Median and IQR, not mean ± SD (latency distributions are skewed)

Comparison

Paired across seeds where the design allows; report effect sizes and distributions, not

p-values

Reproducibility

experiments/runner.py writes a manifest: git SHA, image digests, config hashes,

scenario file hash, seeds, node specs

Raw data

Every run’s CFR stream archived; figures regenerable from raw data by a single script

Two protocol rules that matter more than they look:

1. The scenario trace file is fixed and hashed. Two conditions must see the identical arrival sequence,

or the comparison is between traffic patterns rather than between conditions.

2. CSC-offruns use the same images with branching disabled by config, never a different build.

Otherwise the overhead measurement includes incidental build differences.

11.5

Prototype Success Criteria

What "the project succeeded" means, agreed in advance so it cannot be redefined at the end.

#

Criterion

Threshold

Experiment

Priority

SC1

Branches provably start from

identical state

Anchor-hash mismatch rate = 0 over 5,000

epochs

E6

Must

SC2

Determinism holds

M22 = 0

E6

Must

SC3

Containment holds

M15 = 0; all A1–A14 blocked

E3

Must

SC4

Production is not degraded

p95 decision latency at N = 3 within 5 % of

N = 0

E2

Must

SC5

Shadow failure never reaches

production

0 production impacts across E7 shadow-side

injections

E7

Must

SC6

Fidelity is measured, not assumed

ε reported for ≥95 % of epochs

E4

Must

SC7

The loop runs continuously

≥10,000 consecutive epochs with CFR

completeness ≥90 %

E5

Should

SC8

Overhead is characterised

Ω(N) curve published with the knee

identified

E2

Should

SC9

Counterfactual data helps

C2 beats C3 on realised utility, or a clear

explanation of why not

E5

Should

SC10

Fidelity discounting matters

Measured difference between Rraw and R,

and between C2 and C4

E4, E5

Should

SC11

Graceful degradation on

constrained hardware

Scheduler reduces N without production

impact

E8

Nice

SC12

Early pruning saves cost without

material bias

E2c reports both

E2c

Nice

Note the shape: every Must criterion is about correctness, containment, and non-interference — things fully

within the team’s control. Only the Should criteria depend on whether the idea turns out to be useful. This

Evaluation Plan

is how a project design document protects a student team from a result that is scientifically interesting but

not what they hoped for.

11.6

Threats to Validity

To be written into the report, not discovered by a reviewer.

Threat

Description

Mitigation

State it prominently; frame all claims as being

about the runtime mechanism

Simulated

environment

The "real world" is our own software.

Results say nothing about physical

traffic.

Deliberately give the environment effects the SEM

lacks (§9.7 table); report the list

SEM/environment

kinship

Both were written by the same team, so

the SEM may be unrealistically

accurate

Single domain

One example (J1) may not generalise

Scope claims to "applications with small declared

state and a cheap local effect model"; §10.7 states

the integration cost honestly

Small action set

A = 6 makes exploration easy

Report as a limitation; note that N ≪A is the

realistic regime and the scheduler is designed for it

Short horizon

H = 6 may hide errors that only appear

later

E4’s divergence curve directly addresses this by

measuring longer H

Utility definition

Conclusions may depend on chosen

weights

E5c sensitivity study

Hardware

variance

Laptop/VM measurements are noisy

5 seeds, median/IQR, same hardware across

conditions, manifest recording

Selection of

scenarios

Three hand-made traces

Publish the traces; make them regenerable; report

per-scenario results separately rather than pooled

11.7

Dashboards

Three Grafana dashboards, which double as the live demo.

Dashboard

Panels

Runtime health

Epoch slack, capture latency, hydration latency, branch completion rate, cold-start rate,

warm-pool depth, per-node CPU/memory

Counterfactual view

Live branch table for the current epoch (role, action, utility, provenance); U real vs

shadow utilities over time; ε with its EWMA; raw vs discounted regret; beaten rate;

winning-alternative histogram

Safety

actuation_allowed_total, actuation_blocked_total by layer, double_actuation_

total, violation event stream, containment-test status

The counterfactual view is the demo. A live panel showing five actions being evaluated simultaneously, with

only one of them coloured as REALISED, communicates the entire idea in about four seconds — considerably

faster than this document does.

# Chapter 12: Comparison With Existing Techniques

The purpose of this chapter is to be precise about what CSC adds and what it borrows. Overclaiming here

is the fastest way to lose credibility, so each comparison ends with a plain statement of what the existing

technique does better.

12.1

Comparison Dimensions

Dimension

Meaning

State anchoring

Do alternatives start from the exact live runtime state?

Input source

Do alternatives see the real, live inputs?

Code identity

Do alternatives run the same code as production?

Actuation

Can alternatives affect the world?

Timing

Online (in the decision loop) or offline?

Unit of comparison

Implementations, policies, or individual decisions?

Output

What does it produce?

Cost model

What does it consume?

12.2

Master Comparison Table

State anchoring

Input source

Code identity

Actuation

Timing

Unit compared

Primary

output

Online

Implementations

Correctness /

perf diff

Digital Twin

Model-maintained,

continuous

Real telemetry,

streamed

Separate model

None

Online,

long-horizon

System / asset

behaviour

Health,

prediction,

what-if studies

Shadow Traffic /

Mirroring

None (stateless

replay)

Real requests,

duplicated

Different build

under test

Usually

suppressed,

often

imperfectly

None

Real, partitioned

Both variants real

Yes — both

act

Online

Variants over

populations

Statistical lift

A/B Test,

Canary,

Interleaving

Live cluster state

Live

The scheduler itself

Yes

Online

— (no

comparison)

Placement

decisions

Offline RL / OPE

(IPS, DR)

Logged states

Logged inputs

Policy evaluated

numerically

None

Offline

Policies

Estimated

policy value

Simulation /

What-if

Reconstructed or

synthetic

Synthetic or

replayed

Often a

re-implementation

None

Offline

Scenarios

Scenario

outcomes

Kubernetes

scheduling /

descheduling

Record-and-

replay debugging

Recorded execution

Recorded

Same code

None

Offline

Executions

Root cause

Live micro-state

Live

Same code

Committed or

squashed

Online,

microseconds

Paths

Latency hiding

Chaos

engineering

Live

Live

Same code

Yes —

deliberately

Online

System under

fault

Resilience

evidence

Speculative

execution (CPU,

query)

CSC (proposed)

Live,

per-decision,

hash-verified

Live,

duplicated,

order-identical

Same image

Production

only; others

structurally

blocked

Online, per

epoch

Individual

decisions

Multi-armed

counterfactual

records +

calibrated

regret

12.3

Pairwise Discussion

12.3.1

vs Digital Twin

Digital Twin

CSC

Lifetime

Long-lived, continuously

maintained

Branches live for H ticks, then are destroyed

Fidelity strategy

Improve the model until it tracks

the asset

Keep the model small and re-anchor every epoch;

measure residual error explicitly

Question answered

"What is the system doing /

going to do?"

"Which of these specific alternatives was better,

and how much should I trust that?"

Relationship to production

code

Separate artefact

Same container image

Comparison With Existing Techniques

Digital Twin

CSC

Cost

One persistent model

N short-lived executions per decision

Where a twin is better: long-horizon prediction, physical-asset modelling, engineering analysis, and any

situation where the model is genuinely high-fidelity. CSC’s short horizon is a limitation, not a virtue in itself

— it is a mitigation for having a deliberately cheap model.

Integration, not competition: a mature digital twin is an excellent implementation of CSC’s Shadow

Environment Model.

An organisation that already has one has largely solved CSC’s hardest integration

problem (§10.7).

12.3.2

vs Shadow Traffic / Traffic Mirroring

Traffic mirroring

CSC

What varies

The service implementation

The decision

State

Typically stateless replay; no fork

Explicit anchored fork, hash-verified

Isolation

Usually convention and configuration

Five enforced layers with an audit trail

Scoring

Diffs, error rates, latency

Utility, regret, fidelity gap

Feedback loop

Human reviews the diff

Automated policy update with a promotion

gate

Where mirroring is better: it is vastly simpler, needs no state schema, no environment model, and is

production-proven for its actual purpose — validating a new build against real traffic. If your question is "does

v2 behave like v1," mirroring is the right tool and CSC is overkill.

The naming overlap is unfortunate and the team should address it head-on in the paper’s related-work

section rather than letting a reviewer raise it.

12.3.3

vs A/B Testing and Canaries

The cleanest distinction in the whole chapter:

A/B testing

CSC

How information is bought

With real-world consequences — each arm

acts on real users/assets

With compute — alternatives never

act

Per unit

One unit sees one arm

One decision yields evidence about

N + 1 arms

State comparability

Arms differ in which units they see, and rely

on randomisation

Arms see the identical state and

inputs

Ground truth

Real for every arm

Real for one arm, estimated for the

rest

Suitable when

Consequences are cheap and reversible

Consequences are expensive or

irreversible

Where A/B is better, decisively: its outcomes are real. Every arm’s result is an observation, not an

estimate. A/B testing has no ε because it does not need one. CSC trades ground truth for safety and sample

multiplicity — and that trade is only worthwhile when acting is expensive.

Note that the promotion audit (§3.7) is CSC deliberately performing a tiny, rate-limited A/B test to calibrate

itself. The two techniques compose naturally.

12.3.4

vs Off-Policy Evaluation and Offline RL

This is the most technically substantive comparison and the one a reviewer will press hardest on.

OPE / Offline RL

CSC

Data source

Logs from the deployed policy

Live multi-branch execution

Core limitation

Support: no reweighting recovers U(s, a)

where the logging policy never took a

Model error: ˆU(s, a) exists everywhere

but is only as good as the SEM

Comparison With Existing Techniques

OPE / Offline RL

CSC

Error characterisation

Variance blows up as propensities shrink;

confidence intervals from estimators

Measured directly via the mirror branch

Cost

Cheap — offline computation over existing

logs

Expensive — N× execution online

When it works

Logging policy has broad support and

known propensities

Local effect model is cheap and

reasonably accurate

Where OPE is better: it is nearly free, mathematically well-founded, and comes with established confidence-

interval machinery. If your logging policy explores adequately, OPE answers the same question at a fraction

of the cost.

The honest framing: OPE and CSC fail in different places. OPE fails where the data has no support; CSC

fails where the model is wrong. They are complementary, and the strongest version of this project’s argument

is that CSC generates data with better support, which OPE can then analyse. That framing — CSC as

a data-generation layer feeding standard off-policy machinery — is more defensible than positioning CSC as a

replacement, and it is what the paper should say.

12.3.5

vs Kubernetes Scheduling

There is no real rivalry, and the document should not manufacture one.

kube-scheduler

CSC

Layer

Cluster control plane

Application decision layer

Decides

Where a pod runs

Domain actions (green times, in J1)

Relationship

CSC uses it to place branch pods

—

The genuinely interesting connection is a future direction: a scheduler could become a CSC-enabled application,

declaring its state schema (node allocatable, pending pods, recent utilisation), its action set (candidate place-

ments), and a cheap SEM (predicted node pressure). It would then accumulate evidence about the placements

it did not make. Chapter 14 lists this; it is out of scope for the prototype and should be presented as an idea,

not a claim.

12.3.6

vs Speculative Execution

The closest architectural cousin, and worth acknowledging because it strengthens rather than weakens the

design’s credibility.

CPU / query speculative

execution

CSC

Motivation

Hide latency

Accumulate evidence

Fate of the losers

Squashed, unrecorded

Scored and recorded — this is the entire

point

Scale

Nanoseconds to microseconds, within a

process

Seconds, across pods and nodes

Correctness

Losing paths must leave no trace

Losing paths must leave no external trace but

must leave an internal record

Isolation mechanism

Hardware / engine internals

Sandbox, network policy, gateway

CSC can be described accurately as "speculative execution at the distributed runtime layer, where the specu-

lation is not discarded but measured." That sentence is defensible, credits the prior idea, and communicates

the design quickly. It is a better opening line for a paper than any novelty claim.

12.4

What CSC Proposes, Precisely

To close the chapter without overreach:

CSC does not propose: state snapshotting, container sandboxing, stream fan-out, environment modelling,

regret computation, or policy learning. All are established.

CSC proposes:

Comparison With Existing Techniques

1. Per-decision state anchoring as a runtime primitive, hash-verified across branches, rather than as

an offline reconstruction.

2. Non-actuating multi-branch execution of the production code image, with containment enforced

structurally at five layers rather than by convention.

3. A mirror branch as a continuous, per-epoch calibration mechanism, making shadow-model error

a measured runtime quantity instead of an assumption.

4. Fidelity-discounted regret as the reported decision-quality signal, so that claimed improvements must

exceed the system’s own demonstrated error.

5. The composition of the above into a continuously running cloud–edge runtime layer with a

defined integration contract (§10.7) for making an application CSC-enabled.

Items 3 and 4 are, in our judgement, the most defensible contributions, because they address the exact objection

every reviewer will raise first: "your counterfactuals are just model outputs." The answer — "yes, and here is

the per-epoch measurement of how wrong they are, and here is the regret figure with that error subtracted"

— is the strongest thing this architecture has to say.

# Chapter 13: Limitations

This chapter is written to be read by someone looking for reasons the idea will not work. Every limitation is

stated with its severity, whether the prototype can mitigate it, and how it would be detected.

13.1

Limitation Register

Limitation

Severity

Mitigated in prototype?

Detected by

L1

Shadow outcomes are estimates, never

observations

Fundamental

Partially — mirror branch

measures the error

E4

L2

Memory cost scales linearly with N

High

Budget controller, warm pool,

pruning

E2

L3

CPU cost scales linearly with N; gVisor

adds more

High

Budget controller, node separation

E2, E2b

L4

State divergence grows with horizon

High

Short H, per-epoch re-anchoring

E4

L5

Explicit state capture is only as

complete as the schema

High

Determinism test as a gate

E6

L6

Synchronisation skew and

non-determinism

Medium

Seq-driven execution, seeded

RNG, sanitised pods

E6

L7

Learning from estimates can amplify

model bias

High

Provenance weighting, promotion

gate, audits

E5 (C2 vs C4)

L8

Sandbox escape remains possible

Medium

Five layers; residual risk accepted

and documented

E3

L9

Scalability beyond a single site is

unaddressed

Medium

Out of scope; noted as future work

—

L10

Fidelity is measured only at a0

High

Promotion audits sample other

actions

E4(d)

L11

Input duplication multiplies copies of

possibly sensitive data

Medium

Same trust zone, no external

egress, retention limits

Design review

L12

Storage growth from CFRs

Low

Retention policy, compression

E5

L13

Applicability is narrow

Medium

Stated explicitly as an integration

contract

§10.7

L14

Environment is simulated

Fundamental for

this project

Cannot be mitigated; stated in

every claim

—

13.2

The Ones That Matter Most

13.2.1

L1 — Estimates, not observations

Everything in CSC downstream of a shadow branch rests on a model. If the SEM is bad, the regret figures

are decoration.

The design’s response is not to claim the model is good but to measure how bad it is, every epoch,

and subtract it. That is genuinely useful, but it has a hard limit: the mirror branch measures error at the

action production took. It cannot measure error at actions nobody took, which is exactly where the interesting

counterfactuals live. This is L10, and it is the deepest unsolved problem in the design.

The promotion audit partially addresses it by occasionally taking a shadow action, producing a real observation

at an off-policy point. But audits are rare by construction (5 % of epochs), so the error estimate at unexplored

actions will always be coarser than at a0. The report should present ε broken down by action distance and be

explicit about the sample size at each distance.

13.2.2

L2 / L3 — Resource cost

CSC multiplies decision-path compute by roughly (1 + N). At N = 3 that is a 4× decision-path cost, and

gVisor adds more on top. For a traffic junction with a 10-second epoch and a tiny state, this is affordable. For

a high-frequency, large-state control loop, it may not be.

The budget controller (§4.6.2) is the structural response: CSC reduces its own ambition rather than

degrading production. That means the honest description of CSC’s cost profile is "it consumes whatever

Limitations

slack exists, and produces proportionally less evidence when there is less slack." Experiment E8 is designed to

show exactly that behaviour on constrained hardware.

An important secondary cost that is easy to overlook: the SEM is application code that must be written,

tested, and maintained. §10.7 puts it at ~150 lines for J1, but a more complex domain could make it the

dominant integration cost — potentially larger than the entire CSC runtime.

13.2.3

L4 — Divergence

Shadow state and real state separate as the horizon grows. Since ˆs(0) = s(0) exactly and the exogenous inputs

are identical, the divergence comes purely from ˆF vs F — but it still compounds, because an error in queue

length at tick 2 changes departures at tick 3.

CSC’s response is a short, empirically-chosen H. The cost of that choice is real and should be stated: CSC

can only evaluate short-horizon consequences. An action whose benefit appears after 60 seconds — a

signal plan that pays offtwo cycles later — is invisible to a 6-tick horizon and may even be scored as harmful.

This is a genuine blind spot, not a tuning issue, and the E4 divergence curve is what makes the trade-offvisible

rather than hidden.

13.2.4

L5 / L6 — Capture completeness and determinism

Explicit schema capture buys implementation simplicity at the price of a correctness obligation: if the worker

reads anything not in the anchor and not in the input stream, branches diverge for reasons that have nothing

to do with the action, and the comparison is silently invalid.

The dangerous word is silently. A branch reading the wall clock, an unseeded RNG, an environment variable,

a cached tensor from a previous epoch, or a dictionary in non-deterministic iteration order will produce

plausible-looking, wrong results. This is why experiment E6 (two mirror branches, expect identical outcomes)

is classified as a Must success criterion rather than a nice-to-have. It is the only mechanism that turns this

from an assumption into a checked property.

Known sources the team should expect to hunt down: PyTorch non-determinism on some operations, Python

set/dict ordering across processes, time.time() calls inside metric code, unreset EWMA state in recycled pods,

and floating-point differences if branches land on heterogeneous CPUs.

13.2.5

L7 — Bias amplification

The most serious systemic risk. The loop is: shadow model produces estimates →estimates train the utility

model →the utility model chooses actions →those actions determine which states are anchored →those

states are where the shadow model is evaluated. A model error can be reinforced by its own consequences.

Three defences, none of them complete:

1. Provenance weighting (wk(a) = 1/(1 + λεk)) reduces the influence of estimates when they are demon-

strably poor.

2. The promotion gate requires improvement to exceed ¯ε before a policy reaches production.

3. Promotion audits inject genuine off-policy observations at a controlled rate.

Experiment E5’s C4 condition (no fidelity discounting) exists specifically to quantify how much these defences

are worth. If C4 diverges or degrades while C2 is stable, that is a strong result and directly justifies the mirror

branch’s cost.

13.2.6

L8 — Sandbox escape

gVisor materially reduces escape risk but does not eliminate it. If the Sentry has an exploitable bug, layer

L5 fails. The other four layers still stand — a branch that escapes the sandbox still has no credentials (L4),

no network route to the environment (L3), and no valid production token (L2) — but defence in depth is a

probability argument, not a proof.

Practical stance for the project: keep runsc current, run only first-party code as shadow policies, treat the

shadow node as a lower-trust zone, and never route the shadow node’s network to anything that matters.

Do not claim the system is "safe"; claim it is "contained by five independent mechanisms, each individually

tested."

13.2.7

L9 — Scalability

Everything in this document is single-site. Real deployments would have hundreds of junctions, and several

questions are simply unanswered:

Limitations

- Do neighbouring junctions’ branches need coordinating? (Almost certainly, since traffic is coupled — and

a shadow branch at J1 changes nothing at J2, so cross-junction counterfactuals are not composable in the

current design.)

- How are branch budgets allocated across sites competing for shared cluster capacity?

- Does the control plane (single Epoch Clock, single sequencer, single OCE instance) become a bottleneck?

The honest statement is that CSC as designed is a per-site runtime layer, and multi-site coordination is

unsolved. Chapter 14 lists it; the report should not imply otherwise.

13.2.8

L11 — Privacy and data multiplication

Duplicating the live input stream to N + 2 consumers multiplies copies of whatever is in that stream. For

vehicle counts this is uninteresting. For a domain where inputs contain personal data, CSC increases exposure

surface by design.

Mitigations that should be stated even though J1 does not need them: keep all branches inside one trust zone

(which the network policy already enforces), apply the same retention limits to the input log as to the source,

and prefer aggregated features over raw records in the anchor. If CSC were applied to a domain with personal

data, a data-protection review would be a prerequisite, not an afterthought.

13.2.9

L14 — Simulated environment

The prototype’s junction is software the team wrote. No result in this project says anything about physical

traffic control, and every claim must be scoped to the runtime mechanism. Stating this clearly is not a weakness

in the write-up — it is what separates a careful project from an overreaching one.

13.3

When CSC Is the Wrong Choice

A short, blunt list, which is more useful than a long list of strengths:

Do not use CSC when. . .

Because

The decision-relevant state is large or hard to declare

Capture cost and completeness risk dominate (E1 finds the

boundary)

No cheap local model of the action’s effect exists

There is no SEM, so shadow branches produce nothing

Consequences only appear over long horizons

Divergence makes short-horizon evaluation misleading (L4)

Acting is cheap and reversible

A/B testing gives real outcomes for less effort and less code

Resources are tight and fully committed

The budget controller will simply set N = 0

The action space is continuous and high-dimensional

N branches sample a vanishing fraction of it

The logging policy already explores broadly

Standard off-policy evaluation answers the question offline

for far less

# Chapter 14: Future Work

Kept deliberately brief. These are directions, not commitments, and none of them is required for the prototype.

Direction

Idea

Why it is interesting

Difficulty

High

Addresses L9 partially and

reduces the data each site

must gather alone

Federated CSC

Sites share counterfactual records (or model

updates) without sharing raw inputs, so a

junction benefits from evidence gathered

elsewhere

The correct fix for the

composability gap in L9

High

Multi-site coordinated

branching

Branch neighbouring junctions jointly so a

shadow action at J1 propagates into J2’s

shadow world

Medium

Energy-aware branching

Make Nk a function of available energy or

carbon intensity, not just CPU — natural for

solar/battery-powered edge nodes

Turns speculation into an

explicitly elastic, schedulable

resource

Directly attacks L2/L3;

measurable in E2c

Medium

Adaptive shadow

pruning

Extend Algorithm 10 into a proper

successive-halving or bandit allocation across

candidates within an epoch

Medium

Learned SEM

Replace the hand-written model with one

trained from realised transitions, with ε as its

own training signal

Could shrink ε; risks

worsening L7 if not carefully

gated

Uncertainty-aware

branch selection

Choose candidates by expected information

gain rather than by policy rank

Better use of a scarce branch

budget

Medium

Medium

Hardware-backed

isolation

Run shadow branches in

confidential-computing enclaves (SEV-SNP,

TDX) or microVMs

Strengthens L8; enables

shadowing across trust

boundaries

High

True process-level

forking

CRIU checkpoint/restore or copy-on-write

memory cloning instead of schema capture

Removes L5 entirely; would

let CSC apply to applications

that cannot declare their state

Medium

WebAssembly

microbranches

Compile the decision worker to Wasm for

millisecond-scale branch startup

Would make much larger N

affordable and shrink cold

starts

Medium

CSC for cluster

scheduling

Make kube-scheduler a CSC-enabled

application per §10.7

Would test whether the layer

generalises beyond the traffic

domain

Medium

Formal verification of

the actuation boundary

Model-check the gateway’s token and interlock

logic

Converts §6.4’s test-based

argument into a proof for the

smallest, most critical

component

Medium

Multi-cloud /

cross-provider

branching

Place shadow branches on spot or preemptible

capacity in a different provider from

production

Speculation is interruptible by

definition, so it is an

unusually good fit for

preemptible resources

The two with the best effort-to-insight ratio for a follow-on project are adaptive shadow pruning (measur-

able, self-contained, directly addresses the biggest cost) and CSC for cluster scheduling (tests generalisation,

which is the main open question about the whole architecture).

# Chapter 15: Conclusion

15.1

The Problem

Runtime systems commit to one action per decision and observe only its consequence.

Every alternative

is discarded without evidence. This makes decision quality indistinguishable from outcome quality, biases

any learning built on operational telemetry toward the policy that produced it, and forces teams to buy

information about alternatives by executing them on real users or real assets.

Existing tools give either

realism without alternatives (observability, A/B testing) or alternatives without realism (offline simulation,

off-policy estimation).

15.2

The Architecture

CSC proposes a runtime layer that, at every decision epoch, captures the decision-relevant state into a hash-

verified anchor, forks that anchor into a production branch and several shadow branches running the same

container image, replicates the live input stream identically to all of them, and permits only the produc-

tion branch to reach the environment. Containment is enforced structurally at five independent layers — a

role-aware egress shim, a signed-token gateway with a per-epoch actuation interlock, network egress policy, cre-

dential absence, and a gVisor sandbox — rather than by convention. Shadow branches close their loop through

a small, short-horizon Shadow Environment Model that receives the real exogenous inputs and models only

the effect of its own action.

The design’s distinguishing feature is that it treats the accuracy of its own estimates as a measured runtime

quantity. A mirror branch executes the production action inside the shadow world every epoch, so the

difference between its estimate and the observed reality gives a direct, continuous measurement of shadow-

model error. Regret is then reported after subtracting that error, so an alternative is only credited with

an improvement when it beats production by more than the system’s own demonstrated inaccuracy. The

resulting counterfactual records — several labelled action–utility pairs per decision, each with a provenance

tag and an error bar — feed a policy-improvement loop protected by shadow-first promotion, a fidelity-aware

gate, and automatic rollback.

15.3

The Prototype

The prototype is scoped to one semester and one junction. It runs on a three-node K3s cluster with NATS

JetStream, Redis, Prometheus and Grafana; a Go control plane; a Python decision worker and learning engine;

and gVisor for shadow isolation. Approximately 5,500 lines of first-party code, no kernel work, no enterprise

tooling. The build order in §10.9 produces a demonstrable artefact from week four and defers every optional

component to the end.

Success is defined in advance and weighted toward correctness rather than toward favourable results. The

mandatory criteria are that branches provably start from identical state, that two branches given the same

action produce identical outcomes, that a deliberately hostile shadow branch cannot affect the environment,

that production latency is unaffected, and that shadow failures never propagate. Only the secondary criteria

depend on whether the counterfactual data turns out to improve the policy.

15.4

What This Document Does Not Claim

No performance figure in this document is a measurement. The overhead model, the timing budget, and the

worked example in Chapter 9 are design targets and illustrative arithmetic. Whether Ω(N) is affine, whether

¯ε is small enough for regret to be meaningful, whether the beaten rate falls under learning, and whether CSC’s

data beats production-only logs for the same trainer are all open questions that Chapter 11 exists to

answer. The architecture may also turn out to be inapplicable outside a narrow class of applications — those

with small declared state and a cheap local effect model — and §10.7 and §13.3 state that boundary honestly

rather than obscuring it.

Nor is any mechanism here new in isolation. State capture, sandboxing, stream fan-out, environment mod-

elling, regret accounting and policy learning are all established. What CSC proposes is their composition and

Conclusion

placement: making per-decision counterfactual execution a continuous property of a live cloud–edge runtime,

with the error of its own estimates measured rather than assumed.

15.5

Toward Implementation

The immediate next steps for the team are, in order: stand up the cluster and the environment service;

build the single-branch baseline controller; implement state capture and verify anchor hashing; then build the

branch manager and prove that five pods can hydrate from one anchor and report matching hashes. That

fourth milestone is the project’s highest-risk moment and the point at which the idea becomes either real or

not.

Everything after it — the gateway, the mirror branch, the comparison engine, the containment suite, the

learning loop — is incremental work on a foundation that either holds or does not. If it holds, the team will

have a running system that produces, every ten seconds, a small piece of evidence that no conventional runtime

can produce: a record of what the alternatives looked like, and an honest statement of how much to trust it.

Appendix A

Prometheus Metric Catalogue

Metric

Type

Labels

Component

csc_epoch_total

counter

site, result

Epoch Clock

csc_capture_duration_ms

histogram

site

State Capture

csc_anchor_size_bytes

histogram

site, schema_

version

State Capture

csc_capture_budget_exceeded_total

counter

site

State Capture

csc_capture_missing_field_total

counter

site, field

State Capture

csc_branch_budget

gauge

site

Branch Manager

csc_branches_planned_total

counter

site, role, reason

Branch Manager

csc_branch_hydrate_ms

histogram

role

Branch sidecar

csc_branch_exec_ms

histogram

role, status

Branch sidecar

csc_anchor_mismatch_total

counter

role

Branch Manager

csc_cold_start_total

counter

—

Branch Manager

csc_branch_pruned_total

counter

reason

Branch Manager

csc_warm_pool_depth

gauge

—

Branch Manager

csc_replication_skew_ms

histogram

site

Sync

csc_input_dropped_total

counter

branch_role,

reason

Sync

csc_actuation_allowed_total

counter

site

Gateway

csc_actuation_blocked_total

counter

layer, role, reason

Gateway, sidecar

csc_double_actuation_total

counter

site

Gateway

csc_virtual_actuation_total

counter

role

Sidecar

csc_production_decision_ms

histogram

site

Production branch

csc_barrier_wait_ms

histogram

site

Comparison Engine

csc_compare_duration_ms

histogram

site

Comparison Engine

csc_cfr_written_total

counter

status

Comparison Engine

csc_cfr_skipped_no_ground_truth_total

counter

site

Comparison Engine

csc_realised_utility

gauge

site

Comparison Engine

csc_fidelity_gap

gauge

site, source

Comparison Engine

csc_regret_raw

gauge

site

Comparison Engine

csc_regret_discounted

gauge

site

Comparison Engine

csc_beaten_rate

gauge

site, window

Comparison Engine

csc_epoch_slack_ms

histogram

site

Comparison Engine

csc_policy_transitions_total

counter

result

Policy Updater

csc_promotion_audit_total

counter

site

Branch Manager

csc_training_runs_total

counter

result

Learning Engine

Alerting rules worth defining from day one:

Alert

Condition

Severity

ActuationEscape

csc_actuation_blocked_total{layer!="L1"} > 0

outside experiment E3

critical

DoubleActuation

csc_double_actuation_total > 0

critical

AnchorMismatch

csc_anchor_mismatch_total > 0

critical

EpochSlackExhausted

csc_epoch_slack_ms p50 < 500 for 5 min

warning

FidelityDegraded

csc_fidelity_gap EWMA > EPSILON_ALERT

warning

ProductionLatencyRegression

csc_production_decision_ms p95 up > 10 % vs 1

h ago

warning

CFRCompletenessLow

COMPLETE fraction < 0.8 over 30 min

info

Appendix B

Counterfactual Record Schema

{

"$schema": "https://json-schema.org/draft/2020-12/schema",

"title": "CounterfactualRecord",

"type": "object",

"required": ["cfr_id","epoch","site_id","anchor_hash","u_real",

"epsilon","regret_discounted","branches","record_status"],

"properties": {

"cfr_id":

{"type":"string"},

"epoch":

{"type":"integer"},

"site_id":

{"type":"string"},

"anchor_hash":

{"type":"string"},

"schema_version":

{"type":"integer"},

"policy_version":

{"type":"string"},

"utility_config_hash": {"type":"string"},

"horizon_ticks":

{"type":"integer"},

"u_real":

{"type":"number"},

"u_mirror":

{"type":["number","null"]},

"epsilon":

{"type":"number","minimum":0},

"epsilon_source":

{"enum":["MEASURED","ESTIMATED"]},

"regret_raw":

{"type":"number","minimum":0},

"regret_discounted":{"type":"number","minimum":0},

"best_alt_action":

{"type":["string","null"]},

"audited":

{"type":"boolean"},

"record_status":

{"enum":["COMPLETE","PARTIAL","PRODUCTION_ONLY"]},

"missing":

{"type":"array","items":{"type":"string"}},

"branches": {

"type":"array",

"items": {

"type":"object",

"required":["branch_id","role","action","provenance","utility","status"],

"properties": {

"branch_id":

{"type":"string"},

"role":

{"enum":["PRODUCTION","MIRROR","SHADOW"]},

"action":

{"type":"object"},

"reason":

{"enum":["policy","top_k","explore","probe","mirror"]},

"provenance": {"enum":["REALISED","ESTIMATED"]},

"utility":

{"type":"number"},

"metrics":

{"type":"object"},

"runtime":

{"type":"object"},

"status":

{"enum":["REPORTED","TIMEOUT","FAULTED","DEGRADED"]}

}

}

}

}

}

utility_config_hash is easy to forget and important: without it, records produced under different utility

weights are silently incomparable, and an E5c sensitivity study would be impossible to reconstruct after the

fact.

Appendix C

Experiment Run Manifest

Written by experiments/runner.py at the start of every run. Any result without one is not reportable.

run_id: e5-c2-seed3-20260420T1412Z

experiment: E5

condition: C2_csc_learn

seed: 3

git_sha: 4f2a9c1e

images:

branch-runtime: sha256:9ab3...

actuation-gateway: sha256:71cd...

env-service: sha256:0e4f...

configs:

budget.yaml: sha256:cc12...

utility.j1.yaml: sha256:8a90...

state_schema.j1.yaml: sha256:5f77...

scenario:

name: S-PEAK

trace_file: traces/peak_60min.csv

trace_sha256: sha256:b3e1...

cluster:

nodes:

- {name: csc-control, cpu: 4, mem_gb: 8, kernel: "6.8.0"}

- {name: csc-edge-1,

cpu: 4, mem_gb: 4, kernel: "6.8.0"}

- {name: csc-shadow-1,cpu: 8, mem_gb: 8, kernel: "6.8.0", runsc: "20260115.0"}

parameters:

n_shadows: 3

horizon_ticks: 6

mirror_enabled: true

epoch_period_ms: 10000

learning_enabled: true

duration_epochs: 10000

warmup_epochs: 100

outputs:

cfr_stream: results/e5-c2-seed3/cfr.parquet

metrics_snapshot: results/e5-c2-seed3/prom.tar.gz

logs: results/e5-c2-seed3/logs/

Appendix D

Risk Register and Team Roles

D.1

D.1 Project Risks

Risk

Likelihood

Impact

Response

PR1

gVisor cannot be installed on

available hardware

Medium

Medium

Documented fallback to runc + hardened

securityContext; report reduced depth explicitly

PR2

Determinism (E6) fails and

cannot be fixed in time

Medium

High

Start E6 at milestone M5, not at the end; it gates every

other result

PR3

Branch hydration proves

slower than the epoch budget

Medium

High

Warm pool designed in from the start; fall back to a

longer Tepoch (20 s) rather than abandoning branching

PR4

ε turns out large, so regret is

always zero

Medium

Medium

This is a result, not a failure. Report it, analyse why,

and use E4(c) to show the system correctly distrusts

itself

PR5

Learning shows no

improvement

Medium

Low

SC9 is a Should, not a Must. Report the C2/C3/C4

comparison honestly

PR6

Team member unavailable

Medium

Medium

Module ownership in §10.4 is deliberately decoupled;

pair on the security-critical modules

PR7

Scope creep into multi-site or

real hardware

Medium

High

§"Scope and Non-Goals" is the contract; revisit it at

every milestone review

PR8

Cluster instability consumes

the semester

Medium

High

Single-node K3s fallback for development; treat the

3-node cluster as an experiment target, not a dev

environment

D.2

D.2 Suggested Role Split (team of four)

Role

Owns

Primary chapters

Platform / control plane

internal/*, branch manager, sync, ledger, warm pool

4, 5, 10

Security / isolation

Gateway, tokens, interlock, network policy, gVisor,

containment suite

6, 11 (E3)

Learning / evaluation

Worker policy, learning engine, promotion gate, analysis

notebooks

7, 8, 11

Domain / environment

Environment service, SEM, traces, utility config, dashboards

9, 11

The security role should be a named individual, not a shared responsibility. The gateway and token modules

are the only components where a bug is a safety issue rather than a data-quality issue, and they benefit from

a single owner plus mandatory two-person review.

Appendix E

Design Decisions Record

A condensed record of the choices made in this document and the reasoning, so that a future team can revisit

them deliberately rather than by accident.

#

Decision

Alternatives

considered

Rationale

Revisit if. . .

D1

Explicit schema state capture

CRIU, memory

cloning, process fork

Implementable in a semester;

portable; debuggable

Applications appear

that cannot declare

their state (L5)

D2

Mirror branch as a permanent

fixture

Periodic calibration;

assume fidelity

Turns L1 from an assumption into

a measurement; cost is one branch

slot

A better uncertainty

model emerges

Branch budget

becomes the binding

constraint

D3

Fidelity-discounted regret as the

reported figure

Raw regret;

confidence intervals

Conservative and defensible;

directly answers the obvious

reviewer objection

D4

gVisor for shadow isolation

Kata, plain runc,

Wasm

Strong isolation at acceptable cost,

no code to write

E2b shows

unacceptable

overhead (→PR1

fallback)

D5

Egress blocked at the

app-protocol layer, not by syscall

rewriting

Transparent syscall

interception into

virtual buffers

Gateway becomes a

throughput bottleneck

Precision and feasibility; syscalls

do not know what an "actuation" is

A domain appears

where effects are raw

syscalls

D6

Single Actuation Gateway with

an epoch interlock

Per-branch capability

enforcement only

One small auditable chokepoint;

bounds worst-case damage to one

actuation

D7

Epoch number, not timestamps,

as the correlation key

Wall-clock alignment

Immune to clock skew across cloud

and edge nodes

—

—

D8

Branch execution driven by

input seq, not wall clock

Time-driven ticks

Decouples correctness from

network timing

Real-time deadlines

become part of the

semantics

D9

NATS JetStream over Kafka

Kafka, Redis Streams

alone

Far lighter to operate on student

hardware

Team already has

Kafka expertise

D10

Utility model (V1) before policy

gradient (V2)

Policy gradient first

Simpler, debuggable, sufficient to

test the mechanism

V1 plateaus and time

remains

D11

Shadow-first promotion with

canary and rollback

Direct promotion

Prevents a model-error-driven

policy from reaching production

(L7)

E4(d) shows the rate

is too low to calibrate

D12

Promotion audits at 5 %

No audits; higher rate

Buys off-policy ground truth at a

small, bounded, auditable

real-world cost

Never — this one is

load-bearing

D13

Environment service and SEM

written as deliberately different

models

Share code

Prevents ε = 0 by construction,

which would make the whole

fidelity argument circular

—

D14

Success criteria weighted toward

correctness

Weighted toward

learning results

Protects the project from

depending on an uncertain

outcome

End of document.
