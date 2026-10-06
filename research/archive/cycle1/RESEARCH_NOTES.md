# Research notes and decisions

## Specification reconciliation

The user's pasted request explicitly authorizes implementation and treats the
supplied specification as its project reference. The spec's aspirational platform
and illustrative figures are not evidence of implemented or measured behavior.

1. **K accounting:** K means distinct alternative actions, excluding mirrors, as
   in the user request and mathematical symbol table. Some spec sections count a
   mirror inside a total shadow budget; both counts are recorded explicitly.
2. **Regret:** retain signed difference requested by the user and nonnegative raw/
   discounted regret from the long spec. Current measured epsilon is used, matching
   Algorithm 6; EWMA is retained and used only if a later mirror is unavailable.
3. **Unavailable is not zero:** null epsilon/discounted regret when there is no
   current or historical calibration. Null regret when no alternative was evaluated.
   This deliberately extends Appendix B's numeric schema to avoid false evidence.
4. **One plan per epoch:** the gateway accepts one plan and the world executes its
   tick schedule. Per-tick external calls would conflict with the spec's interlock.
5. **Fixed horizon plan:** assigned plans govern the entire window. There are no
   follow-up policy decisions within an epoch; this is the spec's pin-all abstraction.
6. **Separate models:** production includes seeded discharge heterogeneity and an
   EW blockage; SEM omits both by default. Shared input/schema/phase mapping and
   metric aggregation do not share transition code. Exact-control mode removes
   production heterogeneity to test transitions independently, not to claim fidelity.
7. **Simpler technology:** Python, JSON and process/HTTP transport make P0/P1
   executable without external services. Boundaries permit later service replacement.

## Measurement definitions

- Production utility: negative configured queue/wait/switch cost in the software world.
- Mean queue: mean post-service total queue over exactly H ticks.
- Waiting: sum of post-service queues, in vehicle-ticks. This is a queue-integral
  approximation, not tracked per-vehicle delay in seconds.
- Throughput: discharged fluid vehicle units; values can be fractional.
- Divergence: per-tick Euclidean distance of mirror and production queue vectors.
  It need not increase monotonically: queues may drain and trajectories reconverge.
- Resource timing: real monotonic host measurements. They are intentionally not
  deterministic. Full schema/serialization/logging overhead is included in epoch time.
- Communication: serialized request/response bytes, excluding transport framing.
- Safety: observed environment command correlation/action compared with the current
  authorized plan; failed authorization tests independently assert no world mutation.

The baseline is instrumented and shares capture/recording code with CSC. Reported
K-dependent overhead therefore measures incremental shadow execution, not the
cost relative to a stripped controller with all research instrumentation removed.

## Validity limits

Both environments are authored models of a single simplified junction; results
say nothing about real traffic. Seeded workloads have only three hand-designed
profiles. A small discrete action set makes complete coverage unusually cheap.
Same-action mirror error does not bound error for other actions; discounted regret
is a heuristic, not a statistical confidence interval. No promotional audit or
learner has been implemented to test that extrapolation.

Local process workers share the OS user and host resources. They have no issued
production credentials or Python object references, but can access the user's
filesystem/network if made malicious. Application containment and crash isolation
are tested; complete security containment is an open deployment requirement.

The harness joins the comparison at every epoch. Consequently it cannot support
a claim of unchanged production wall-clock cadence. Process startup dominates
these tiny models; warm-pool and cluster measurements may differ substantially.
Successful seeded replay excludes timestamps, process IDs, security nonces and
resource usage. Manifests hash runtime sources and raw artifacts; they are integrity
records, not cryptographic signatures or immutable external attestations.

The five-seed, 100-epoch sweep is smoke evidence. It is not the publication protocol
in Chapter 11. Warmup is retained in raw files and excluded only from metric
summaries. Per-seed distributions and paired workload hashes must accompany any
future headline claim; do not interpret pooled epoch samples as independent runs.

## Next empirical gates

1. Apply the manifests on a real policy-enforcing cluster, verify no shadow egress,
   rootfs/host/device access or production credentials; record each A1–A14 result.
2. Separate continuous production from comparison and test wall-clock cadence under
   failed/slow shadows before claiming production non-interference.
3. Measure true per-process/container RSS, startup CPU, network skew, restart and
   durable-state behavior; then run the full scaling and fidelity protocol.
4. Only then introduce the independently disableable learner, realised holdout,
   shadow-first promotion and rollback experiments.
