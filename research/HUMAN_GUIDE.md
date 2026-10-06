# CSC human guide

**Status:** Current explanation after Cycle 5 closure (2026-10-06).

## What CSC is

Counterfactual Shadow Continuum (CSC) is a research prototype for asking a practical question after a controller makes a decision: "What would the model estimate for other available actions from the same starting conditions?" It runs one real production path and separate non-actuating shadow paths. In this repository the "real" path is still only an authored software traffic simulation for Junction J1. It is not a road junction, a deployed traffic controller, or a cloud service.

The production path is the only authoritative path. A **mirror** repeats the same action in a shadow model so the system can measure model disagreement. An **alternative** takes a different action in that shadow model. `K` means the number of distinct alternative actions and does not count the mirror. The traffic example has three meaningful actions, so K can be 0, 1, or 2.

## How a decision is evaluated

At an epoch, CSC captures a state anchor and a bounded sequence of external arrivals. Production commits one action. Mirror and alternative branches receive the same declared anchor, action, and event window, but cannot actuate production. Once outcomes are available, CSC records comparable estimates and any model discrepancy. These shadow outcomes are useful research evidence only when their assumptions and timing are clear; they are never observed physical futures.

The current mirror error signal, called epsilon, is known only after the window it evaluates. That makes it useful for post-window analysis but not a demonstrated signal for trusting a decision before it is made.

## What Cycle 5 found

Cycle 5 compared two ways to execute shadow work in a local asynchronous coordinator:

- **Cold workers:** start a fresh process for each shadow branch.
- **Warm workers:** reuse a worker after it resets and rehydrates from the new anchor.

In the immutable 86-run local archive, warm workers greatly improved complete evidence in normal conditions. Cold K=1 and K=2 produced no complete evidence in the main measured cells. Warm K=1 completed every requested comparison, and warm K=2 had a median complete fraction of 0.994. This is encouraging for normal local conditions, not proof that CSC works under all load.

The limits matter as much as the improvement. When shadow delay was introduced, median complete evidence fell to zero. The production trajectory hashes matched for paired seed units, but some individual runs had large cadence delays. Named in-memory ledger/ring counts were capped, yet measured RSS and Python allocations still had positive late-run slopes, so process memory was not shown to be bounded. A deliberately injected storage append failure stopped production after one of twelve planned epochs. The system has an explicit bounded-admission policy, but losing mirrors and all useful evidence under pressure means general graceful degradation is not established.

## What was corrected after measurement

The measured archive was frozen. Afterwards, reviewers found several implementation paths involving worker lifecycle, transport, validation, timing arithmetic, cleanup, analysis, and copied-source checks. Those were fixed through separate v1-v5 correctness gates. The final v5 gate passed 108 tests, and its independent review found no critical, major, or moderate remaining issue within that narrow scope. One minor integration-coverage limit remains.

Those later tests make the current v5 tree a reasonable, correctness-gated starting point for a new preregistered study. They do not improve, replace, or reinterpret the measured Cycle 5 performance results. Historical review findings must be read as findings about the pre-correction archive source, not as seven current-v5 implementation blockers.

## What CSC does not claim

CSC has not established physical traffic validity, real-time safety, resource non-interference, hostile-container isolation, cloud deployment behavior, domain independence, durable storage recovery, bounded process memory, robust cadence, or useful delayed evidence yield. The code's local process boundaries are not safe for hostile third-party code.

Trust in alternative counterfactual outcomes remains **Decision D**: the required validity gate did not pass. Learning remains **BLOCKED**: no policy learner is implemented or authorized by the evidence.

## What comes next

The next research gate is a fresh, preregistered controlled-host systems study. It should measure fault containment, physical queues and bytes, storage recovery, long-run memory, cadence tails, and evidence admission under normal and stressed conditions. It must use fresh seeds and a new immutable result directory. Cycle 5 is closed; this guide does not start Cycle 6.

For the current technical state read [RESEARCH_CONTEXT.md](RESEARCH_CONTEXT.md), [RESEARCH_STATUS.md](RESEARCH_STATUS.md), and [CLAIM_EVIDENCE_MATRIX.md](CLAIM_EVIDENCE_MATRIX.md). For exact measured numbers read [RESULTS.md](../RESULTS.md) and the immutable result archive.
