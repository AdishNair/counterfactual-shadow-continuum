# CSC experiment protocol

**Status:** The first section records the executed local smoke protocol. The
former proposed confirmatory reference-fidelity work was executed under the
frozen pre-execution amendment in `research/evidence/cycle2/confirmatory_factorial_amendment.md`;
its negative decision result is in `research/evidence/cycle1/reference_fidelity_analysis.md`.

## Executed local matrix

`experiments/matrix.json` set seeds 1--5, K={0,1,2}, 100 epochs/run, 10 warm-up epochs, and `peak` workload. K=0 used no mirror; K=1/K=2 each used one same-action mirror plus K alternatives. The runner pairs conditions by seed and asserts equal workload and production semantic hashes. Production policy is fixed, so matched production trajectories across K are an invariance check, not an effectiveness comparison.

The execution unit is one local Python run. Branches are formed from saved anchors and event windows; raw JSONL, resource samples, summary, and manifest are retained. `results/matrix/replay-verification.json` records 15 verified runs, 4,000 replayed branch trajectories, and zero mismatches. This audit separately recomputed manifest hashes for all 15 indexed runs and found no failure.

Short validation uses `experiments/validation.py`: eight epochs, no warm-up, and generally one run per scenario. It is diagnostic regression evidence, not replicated treatment evidence.

## Analysis protocol for current evidence

Use only paths named by the matrix or validation index. Do not select a duplicate directory based on a favorable outcome. Reduce each run to the runner's post-warm-up distribution and use the run median as one seed-level observation. Report all five K=1-K=0, K=2-K=0, and K=2-K=1 differences, their median, condition medians, exclusions, and digest checks. Describe faults and ablations as scenario outcomes with their run count.

## Proposed confirmatory local protocol

Before collection, freeze workload generator, coordinator, shadow backend, metric definitions, primary endpoint, seed list, horizon, warm-up, timeout, and exclusions. Use a fresh result directory. Use at least 20 independent workload seeds as a planning minimum, counterbalance K order within seed, and retain the same production policy and event window across paired conditions. Record host, interpreter, worker-reuse mode, CPU/RSS/transport metrics, startup state, and load context. Separate warmed-worker timing from spawned-worker timing.

Predeclare action-distance, model-mismatch, and horizon factors; summarize per-run mirror error and ranking agreement against an independent reference or observed simulator outcome where available. Do not call shadow output ground truth. For fault tests, use multiple randomized failure epochs and workload seeds, distinguish intended exclusion from failure to preserve production behavior, and replay every successful branch.

## Deployment validation

Only after a real cluster and policy-enforcing runtime are available, test deployed image identity/secrets, ingress/egress policy, filesystem, capabilities, resource limits, faults, partitions, and asynchronous production timing. Preserve command and monitoring evidence. Local gateway tests cannot substitute for this phase.
