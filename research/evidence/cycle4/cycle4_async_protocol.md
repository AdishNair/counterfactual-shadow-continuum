# Cycle 4 local asynchronous experiment protocol

**Status:** Preregistered 2026-10-05 before any Cycle 4 timing series execution.

**Question:** Does injected shadow delay change production start-to-start cadence
in the local asynchronous coordinator? Trust validity is a separate experiment.

**Method:** Five paired seeds 901–905, 12 epochs/run, first two warmup epochs
excluded, H=6, peak arrivals, queue production policy. Every seed receives every
condition in a pseudorandom order fixed by `Random(4901)`. Modes are K=0 baseline
(no mirror), synchronous K=1/K=2, asynchronous K=1/K=2. K excludes one mirror in
each nonzero-K mode. There are six conditions: normal (0 added delay), moderate
(40 ms), severe (120 ms), timeout (last alternative at epoch 4 sleeps past the
transport timeout), crash (last alternative at epoch 4), saturation (120 ms
delay, capacity three tasks). All use actual local subprocess workers, three
worker threads, production target period 40 ms, transport timeout 600 ms,
result deadline 300 ms, ordinary task capacity 12, epoch capacity 16.
Factorial size is 150 runs and 1,800 production epochs.

The target period is an intentional local pacing probe, not a real-time service
contract. Synchronous pacing uses the same lower bound and retains its barrier.
No claim is made that these capacities or deadlines are optimal.

**Endpoints:** Reduce measurements within each run first, then report paired
seed-level effects versus the same mode's normal condition. Primary endpoint is
median production start-to-start interval in ms. Secondary endpoints are
production decision latency, run p95/p99 descriptive interpolated quantiles,
late intervals (>40 ms target, with no tolerance or success threshold), epoch
execution duration, comparison completion latency, branch completion latency,
complete/partial/production-only evidence fractions, dropped/expired branches,
queue/running/active depths, and saturation events. Production trajectories and
common workload hashes must match all runs sharing a seed.

**Decision:** No defensible percentage equivalence margin exists here. Report
all five paired effects, medians and ranges; do not define a pass threshold
after outcomes. Logical nonblocking is an invariant-test conclusion; wall-clock
effects remain descriptive local decoupling evidence. A changed production hash,
fabricated incomplete regret, hidden future wait, or exceeded task capacity is
a systems failure regardless of timing.

**Resources:** Coordinator `process_time`, worker reported process CPU,
tracemalloc Python peak, worker subprocess PIDs/count, and serialized request /
response bytes where available. Windows `process_time` can be quantized; zeros
are not zero cost. Worker RSS is unavailable without `resource`; Python peak is
not process RSS. No unreliable RSS is imputed. Observed worker PIDs are a lower
bound when work expires. Host measurements are not resource isolation evidence.

**Secondary microstudy, fixed in advance:** Seeds 906–908, async K=2, 12 epochs,
same pacing/deadlines/capacity; normal, fixed one-million-iteration CPU load,
16 MiB touched bytearray per worker, and high occupancy (120 ms delay/capacity
three). Fixed order randomized by `Random(4902)`. Report paired cadence effects
and evidence loss. No new trust selector or domain is implemented.

**Integrity:** Unique series directory with source bundle (explicit async
dependency closure), script/protocol/config hashes, runtime versions, run seed /
condition registry, all artifact hashes, start/end timestamps distinct from
semantic replay fields. Analyzer and verifier are frozen before execution.
Analysis runs only after every run manifest is terminal. Summaries regenerate
from raw JSONL. Archive never changes; reanalysis writes separate research files.

**Limitations/open questions:** Cooperative first-party workers; tiny local run
and five seed blocks; paired timing does not eliminate host scheduling variation.
No K3s, OS containment, resource independence, real-time safety, durable restart,
or physical validity claim. Action space allows at most two distinct alternatives.

**Next action:** Complete invariant tests, freeze implementation and exact run
registry, then execute once in a timing window without concurrent CSC experiments.
