# Distributed prototype deployment

The implemented P2 slice is one coordinator plus remote shadow services using
bounded HTTP requests containing the anchor and ordered epoch input log. The
same image runs both roles. Production environment, gateway, capture and
comparator remain modules in the coordinator. Redis, NATS and a Go control plane
are not implemented. This is a distributed experiment harness, not a live cluster
controller or streaming transport implementation.

Prerequisites: a running Linux container engine; a K3s context with a network
policy enforcing CNI and dynamic PVC provisioning; the image available on every
node. Build `docker build -t csc-prototype:0.1.0 .` and load/push that exact image
using the cluster's normal image workflow. Pin its digest for reportable runs.

Apply `kubectl apply -f deployments/k3s.yaml`. Inspect
`kubectl -n csc logs job/csc-experiment` and preserve the results PVC.
The Job waits up to its configured branch deadline; unavailable services yield
partial records. Before a reportable experiment, wait for both worker replicas
to be ready and submit a new uniquely named Job. The supplied Job is a smoke run.

Shadow pods have no service-account token, production secrets, host/device mounts,
or production result volume. Their entire egress set is empty: the coordinator
pushes inputs, and established-connection responses carry outcomes. Scratch space
is ephemeral, rootfs is read-only, capabilities are dropped, and CPU/memory limits
are declared. **These manifests have not been applied or containment-tested in
this workspace.** Do not infer a passing A1–A14 suite from YAML.

The base uses the cluster's default runtime, explicitly the weaker runc fallback.
After provisioning a `gvisor` RuntimeClass/handler and labelling shadow nodes,
apply `kubectl -n csc patch deployment shadow-runtime --patch-file deployments/gvisor-patch.yaml`.
Installation of gVisor itself is an operator prerequisite. Node separation,
NetworkPolicy enforcement, cgroup limits, filesystem denial and hostile-code
containment still require actual cluster experiments.

Remote HTTP behavior is exercised locally by `tests/test_failures.py`. The service
binds to localhost by default; container configuration binds it inside the pod.
It has no public authentication/TLS layer and must remain an internal lab service
behind the supplied ingress policy. Do not expose it to the Internet.
