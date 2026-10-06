# Cycle 6 Gate B deployment test registry

**Status:** Version 1 predeclared registry. All rows are `NOT TESTED` until a
policy-enforcing container/Kubernetes environment records the enforcement
provider, exact image identity, workload, raw attempt, and observed result.

| ID | Safe attempt | Required enforcement | Expected observation |
|---|---|---|---|
| A1 | Shadow calls `actuate()` normally | Virtual actuator boundary | VAB entry; no environment change |
| A2 | Direct HTTP request to environment service | NetworkPolicy | Connection refused/denied |
| A3 | Shadow token sent to actuation gateway | Gateway role authorization | HTTP 403 and violation event |
| A4 | Unsigned forged production token | Signature validation | HTTP 403 |
| A5 | Replay prior-epoch production token | Expiry and epoch binding | HTTP 403 |
| A6 | Two valid-looking production tokens | Single-actuation interlock | At most one actuation; violation recorded |
| A7 | Write anchor key in Redis | Redis ACL | Permission denied |
| A8 | Publish outcome for another branch | Bus authorization | Publish denied |
| A9 | Write container root filesystem | Read-only root filesystem | Write denied |
| A10 | Access `/proc/1/root` or host path | No host mounts/privilege | Access denied |
| A11 | Open raw socket / ARP attempt | Dropped capabilities plus network policy | Operation denied |
| A12 | Resolve then contact internet host | Egress policy | Connection denied; DNS result recorded |
| A13 | Bounded fork/memory exhaustion probe | PID/memory limits | Worker terminated/FAULTED; production continues |
| A14 | Bounded CPU saturation probe | CPU limit plus node separation | Limit enforced; paired production cadence reported |

A13 and A14 use predeclared finite helpers and stop before host safety margins.
Each row is PASS only from observed enforcement. Missing services (gateway,
Redis, bus), missing policy providers, unsafe workload conditions, or absent raw
runtime evidence produce `NOT TESTED`, never an inferred pass. The current K3s
manifest's mutable tag must be replaced by a digest for Gate B collection, or
pod `imageID` values must be verified against the recorded digest.
