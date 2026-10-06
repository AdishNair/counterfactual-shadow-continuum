# CSC methodology

**Status:** Description of implemented, locally tested methodology and its limits as audited on 2026-09-28.

## Question

How can this prototype measure the local cost and calibration behavior of non-actuating counterfactual shadows without treating their outcomes as authoritative facts?

## Method

At each logical epoch, the coordinator captures a canonical state anchor, selects one production action, and sends that action through the authoritative gateway. It supplies the same saved exogenous event window to a same-action mirror and, when `K > 0`, K alternative-action shadows. The production world alone receives the authoritative actuation capability. The local coordinator collects shadows before the next logical epoch, so this measures a synchronized harness rather than wall-clock non-interference.

The production model is the Junction J1 software world. Utility is negative mean total queue. Mirror gap `epsilon` is the difference between production and same-action mirror utility. Alternative outcomes are model estimates; raw regret is clipped at zero and discounted regret removes current mirror error. No mirror means no fabricated discounted regret.

## Evidence and units

Primary matrix evidence is `results/matrix/matrix-summary.json`, which names 15 runs: five workload seeds at each K in {0, 1, 2}. Each run has 100 logical epochs and excludes its first 10 epochs from summaries. The independent experimental unit is a seed-specific run. The valid paired comparison is the K contrast within workload seed because workload and production semantic digests match. Epochs estimate a run distribution; they do not raise the independent sample size from five.

Each indexed directory retains anchors, inputs, counterfactual records, branch metrics, resource samples, environment audit, summary, and manifest. The manifest hashes artifacts. `results/validation/validation-summary.json` separately indexes short fault, fidelity, and ablation checks.

## Findings and limitations

The implementation records sufficient input and branch data for deterministic replay, hashes primary artifacts, and labels safety scope as gateway/world capability checks rather than OS containment. Incomplete branches are excluded rather than assigned favorable utility. These are implemented and locally tested properties. Docker/K3s manifests, network policy, gVisor, and hostile-container claims are not deployment-validated.

The same authored queue model produces production and shadow transitions; mirror agreement is a calibration diagnostic, not empirical counterfactual validity. Local worker creation dominates timing, Windows CPU timing is quantized, worker RSS is unavailable, and fixed production policy does not learn from shadow records. The matrix therefore cannot establish policy improvement or physical-world utility.

## Next actions

Add independent workloads, randomized condition order, resource metadata, longer horizons, and asynchronous production measurement. Treat a second-domain adapter and deployment-fault study as separate research with their own ground truth and safety evidence.
