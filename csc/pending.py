"""Coordinator-only bounded evidence ledger. Owns no production authority."""
from dataclasses import asdict
from collections import deque, OrderedDict
import math
import time
from .compare import utility
from .contracts import canonical

TERMINAL = {"COMPLETED", "FAILED", "TIMED_OUT", "EXPIRED", "DROPPED", "REJECTED"}
LEGAL = {"QUEUED": {"RUNNING", "COMPLETED", "FAILED", "TIMED_OUT", "EXPIRED", "REJECTED"},
         "RUNNING": {"COMPLETED", "FAILED", "TIMED_OUT", "EXPIRED", "REJECTED"}}


def transition(previous, target):
    if previous == "COMPLETED" and target == "COMPLETED":
        return "DUPLICATE"
    if target not in LEGAL.get(previous, set()):
        raise ValueError(f"illegal transition {previous}->{target}")
    return target


class PendingShadowLedger:
    def __init__(self, config, manager, comparator, store, clock=time.perf_counter):
        self.config, self.manager, self.comparator, self.store, self.clock = config, manager, comparator, store, clock
        self.pending, self.active, self.finalized = {}, {}, OrderedDict()
        self.committed_high_watermark = -1
        self.last_admission = {}
        self.counts = {k: 0 for k in ("DROPPED", "EXPIRED", "REJECTED", "DUPLICATE", "LATE", "COMPLETED", "FAILED", "TIMED_OUT", "saturation_events")}
        self.max_active = 0
        self.finished = deque(maxlen=config.retention_completed_epochs)
        self.closed = False

    def audit(self, epoch, branch_id, status, **details):
        self.store.append("lifecycle.jsonl", {"epoch": epoch, "branch_id": branch_id, "status": status,
                                             "monotonic_s": self.clock(), **details})

    def append_evidence(self, name, value, record_id, origin_monotonic_s=None):
        method = getattr(self.store, "append_evidence", None)
        return method(name, value, record_id, origin_monotonic_s) if method else self.store.append(name, value)

    def placeholder(self, package, branch, state, reason):
        return {**asdict(branch), "anchor_hash": package["anchor"].snapshot_id,
                "provenance": "ESTIMATED", "status": state, "failure_flags": [reason], "utility": None,
                "runtime": {}, "observation_window": [branch.start_sequence, branch.end_sequence]}

    def commit(self, anchor, branches, events, production):
        if self.closed:
            raise RuntimeError("ledger closed")
        epoch, now = branches[0].epoch, self.clock()
        if epoch <= self.committed_high_watermark:
            raise ValueError("duplicate epoch commit")
        self.committed_high_watermark = epoch
        self.poll()
        # Bound retained packages too: retire oldest evidence if capacity is exhausted.
        if len(self.pending) >= self.config.max_pending_epochs:
            oldest = self.pending[min(self.pending)]
            self.expire(oldest, "epoch_capacity")
            self.finalize()
        package = {"anchor": anchor, "branches": branches, "production": production, "outcomes": {},
                   "states": {}, "committed": now, "deadline": now + self.config.shadow_result_deadline_s,
                   "requested_k": self.config.shadow_count, "admitted_k": 0,
                   "drop_reasons": [], "resource_state": {"active_tasks": len(self.active),
                   "capacity": self.config.max_pending_shadow_tasks, "worker_slots": self.config.max_shadow_slots}}
        self.store.append("epoch_journal.jsonl", {"status": "PRODUCTION_COMMITTED", "site_id": "J1",
                          "experiment_id": branches[0].experiment_id, "epoch": epoch, "anchor_hash": anchor.snapshot_id,
                          "input_hash": production["synchronization"]["input_hash"], "branches": [asdict(b) for b in branches],
                          "production": production, "committed_monotonic_s": now, "deadline_monotonic_s": package["deadline"]})
        self.pending[epoch] = package
        nonproduction = branches[1:]
        admitted = []
        physical_capacity = self.manager.admission_capacity() if hasattr(self.manager, "admission_capacity") else self.config.max_pending_shadow_tasks
        for branch in sorted(nonproduction, key=lambda b: b.role != "MIRROR"):
            if len(self.active) + len(admitted) >= self.config.max_pending_shadow_tasks or not self.config.max_shadow_slots or len(admitted) >= physical_capacity:
                reason = "worker_capacity" if not self.config.max_shadow_slots else "scheduler_capacity" if len(admitted) >= physical_capacity else "queue_full"
                package["states"][branch.branch_id] = "DROPPED"
                package["outcomes"][branch.branch_id] = self.placeholder(package, branch, "DROPPED", reason)
                package["drop_reasons"].append(reason)
                self.counts["DROPPED"] += 1
                self.audit(epoch, branch.branch_id, "DROPPED", reason=reason)
            else:
                admitted.append(branch)
        if package["drop_reasons"]:
            self.counts["saturation_events"] += 1
        package["admitted_k"] = sum(b.role == "SHADOW" for b in admitted)
        self.last_admission = {"requested_k": package["requested_k"], "admitted_k": package["admitted_k"]}
        if admitted:
            for branch, future in self.manager.launch(admitted, anchor, events):
                if getattr(future, "_csc_admitted", True) is False:
                    reason = getattr(future, "_csc_drop_reason", "scheduler_capacity")
                    package["states"][branch.branch_id] = "DROPPED"
                    package["outcomes"][branch.branch_id] = self.placeholder(package, branch, "DROPPED", reason)
                    package["drop_reasons"].append(reason)
                    self.counts["DROPPED"] += 1
                    self.counts["saturation_events"] += 1
                    self.audit(epoch, branch.branch_id, "DROPPED", reason=reason)
                    continue
                package["states"][branch.branch_id] = "QUEUED"
                self.active[branch.branch_id] = (package, branch, future)
                self.audit(epoch, branch.branch_id, "QUEUED")
            package["admitted_k"] = sum(
                branch.role == "SHADOW" and package["states"].get(branch.branch_id) != "DROPPED"
                for branch in admitted)
            self.last_admission = {"requested_k": package["requested_k"], "admitted_k": package["admitted_k"]}
        self.max_active = max(self.max_active, len(self.active))
        self.finalize()

    def valid_identity(self, package, branch, result):
        if not isinstance(result, dict) or any(result.get(k) != v for k, v in asdict(branch).items()):
            return False
        try:
            if len(canonical(result)) > self.config.max_result_bytes:
                return False
        except (TypeError, ValueError, OverflowError):
            return False
        if result.get("provenance") != "ESTIMATED":
            return False
        if result.get("status") in ("FAULTED", "TIMEOUT"):
            return True  # Coordinator-created terminal error envelope, no estimate accepted.
        metrics, trace = result.get("metrics"), result.get("trace")
        if not isinstance(metrics, dict) or not isinstance(trace, list):
            return False
        if len(trace) > self.config.horizon_ticks:
            return False
        if result.get("status") == "REPORTED" and len(trace) != self.config.horizon_ticks:
            return False
        try:
            if any(type(metrics.get(k)) not in (int, float) or not math.isfinite(metrics[k])
                   for k in ("mean_queue", "waiting_vehicle_ticks", "phase_switches", "throughput")):
                return False
            # JSON integers can overflow float conversion, and finite components
            # can overflow their weighted sum. Neither may abort finalization.
            utility(metrics, self.config)
            if any(not isinstance(t, dict) or any(type(t.get(k)) not in (int, float) or not math.isfinite(t[k])
                        for k in ("queue_ns", "queue_ew")) for t in trace):
                return False
            if branch.role == "MIRROR" and any(
                not math.isfinite(math.hypot(p["queue_ns"] - m["queue_ns"],
                                            p["queue_ew"] - m["queue_ew"]))
                for p, m in zip(package["production"]["trace"], trace)
            ):
                return False
        except (ValueError, OverflowError, TypeError):
            return False
        synchronization = result.get("synchronization")
        if not isinstance(synchronization, dict):
            return False
        return (result.get("anchor_hash") == package["anchor"].snapshot_id and
                result.get("initial_state_hash") == package["anchor"].snapshot_id and
                result.get("observation_window") == [branch.start_sequence, branch.end_sequence] and
                synchronization.get("input_hash") == package["production"]["synchronization"]["input_hash"])

    def accept(self, package, branch, result):
        bid, epoch = branch.branch_id, branch.epoch
        if not self.valid_identity(package, branch, result):
            self.counts["REJECTED"] += 1
            self.audit(epoch, bid, "REJECTED", reason="identity_or_input_mismatch")
            if package["states"].get(bid) not in TERMINAL:
                package["states"][bid] = "REJECTED"
                package["outcomes"][bid] = self.placeholder(package, branch, "REJECTED", "identity_or_input_mismatch")
            return
        previous = package["states"].get(bid)
        if epoch in self.finalized or previous in TERMINAL:
            status = "DUPLICATE" if previous == "COMPLETED" else "LATE"
            self.counts[status] += 1
            self.audit(epoch, bid, status, branch_completion_ms=(self.clock() - package["committed"]) * 1000,
                       worker_runtime=result.get("runtime", {}))
            return
        if self.closed or self.clock() >= package["deadline"]:
            package["states"][bid] = transition(previous, "EXPIRED")
            package["outcomes"][bid] = self.placeholder(package, branch, "EXPIRED", "deadline")
            self.counts["EXPIRED"] += 1
            self.counts["LATE"] += 1
            self.audit(epoch, bid, "LATE")
            return
        status = {"REPORTED": "COMPLETED", "TIMEOUT": "TIMED_OUT"}.get(result.get("status"), "FAILED")
        package["states"][bid] = transition(previous, status)
        package["outcomes"][bid] = result
        self.counts[status] += 1
        self.audit(epoch, bid, status, branch_completion_ms=(self.clock() - package["committed"]) * 1000,
                   worker_runtime=result.get("runtime", {}))

    def expire(self, package, reason="deadline"):
        for branch in package["branches"][1:]:
            bid = branch.branch_id
            if package["states"][bid] not in TERMINAL:
                package["states"][bid] = transition(package["states"][bid], "EXPIRED")
                package["outcomes"][bid] = self.placeholder(package, branch, "EXPIRED", reason)
                self.counts["EXPIRED"] += 1
                future = self.active.get(bid, (None, None, None))[2]
                self.audit(branch.epoch, bid, "EXPIRED", reason=reason,
                           execution_state="running" if future and future.running() else "queued",
                           age_ms=(self.clock() - package["committed"]) * 1000)
                if bid in self.active:
                    self.active[bid][2].cancel()

    def poll(self):
        for bid, (package, branch, future) in list(self.active.items()):
            if future.done():
                if not future.cancelled():
                    try:
                        result = future.result()  # Only after done(): never a production wait.
                    except Exception as exc:
                        result = self.placeholder(package, branch, "FAULTED", type(exc).__name__)
                    self.accept(package, branch, result)
                del self.active[bid]  # Permits retained until actual completion/cancellation.
                self.manager.ledger.pop(bid, None)
            elif future.running() and package["states"][bid] == "QUEUED":
                package["states"][bid] = transition("QUEUED", "RUNNING")
                self.audit(branch.epoch, bid, "RUNNING")
        for package in list(self.pending.values()):
            if self.clock() >= package["deadline"]:
                self.expire(package)
        self.finalize()

    def finalize(self):
        while self.pending:
            epoch = min(self.pending)
            package = self.pending[epoch]
            if any(s not in TERMINAL for s in package["states"].values()):
                break
            outcomes = [package["outcomes"][b.branch_id] for b in package["branches"][1:]]
            record = self.comparator.compare(package["anchor"], package["branches"], package["production"], outcomes)
            if record is None:
                raise ValueError("invalid committed production")
            # Do not derive regret from an incomplete alternative set or unavailable mirror.
            if record["missing"]:
                record.update(regret_signed=None, regret_raw=None, regret_discounted=None, best_alt_action=None)
            accepted = [r for r in outcomes if r.get("utility") is not None]
            has_mirror = any(r["role"] == "MIRROR" for r in accepted)
            alternatives = sum(r["role"] == "SHADOW" for r in accepted)
            record["evidence_completeness"] = ("COMPLETE_COMPARISON" if not record["missing"] and outcomes else
                 "PARTIAL_ALTERNATIVES" if alternatives else "MIRROR_COMPLETE" if has_mirror else
                 "EXPIRED_OR_MISSING" if outcomes else "PRODUCTION_ONLY")
            record["comparison_completion_ms"] = (self.clock() - package["committed"]) * 1000
            record["committed_monotonic_s"] = package["committed"]
            record["deadline_monotonic_s"] = package["deadline"]
            record["comparison_monotonic_s"] = self.clock()
            record.update(requested_k=package["requested_k"], admitted_k=package["admitted_k"],
                          completed_k=alternatives, drop_reasons=package["drop_reasons"],
                          resource_state=package["resource_state"],
                          branch_terminal_states=package["states"],
                          evidence_age_ms=record["comparison_completion_ms"])
            t = time.perf_counter()
            record["evidence_record_id"] = f"epoch:{epoch}:comparison"
            record["persistence_admission"] = self.append_evidence(
                "cfr.jsonl", record, record["evidence_record_id"], package["committed"])
            self.audit(epoch, package["branches"][0].branch_id, "EVIDENCE_ADMITTED",
                       record_id=record["evidence_record_id"], stream="cfr.jsonl",
                       disposition=record["persistence_admission"])
            for result in record["branches"]:
                result["evidence_record_id"] = f"epoch:{epoch}:branch:{result['branch_id']}"
                result["persistence_admission"] = self.append_evidence(
                    "branch_metrics.jsonl", result, result["evidence_record_id"], package["committed"])
                self.audit(epoch, result["branch_id"], "EVIDENCE_ADMITTED",
                           record_id=result["evidence_record_id"], stream="branch_metrics.jsonl",
                           disposition=result["persistence_admission"])
            self.audit(epoch, package["branches"][0].branch_id, "FINALIZED", evidence_completeness=record["evidence_completeness"],
                       result_store_ms=(time.perf_counter() - t) * 1000,
                       requested_k=package["requested_k"], admitted_k=package["admitted_k"],
                       completed_k=alternatives, mirror_accepted=has_mirror,
                       accepted_nonproduction=len(accepted), missing_count=len(record["missing"]),
                       record_status=record["record_status"],
                       comparison_completion_ms=record["comparison_completion_ms"],
                       comparison_record_id=record["evidence_record_id"])
            summary_record = {key: record[key] for key in ("u_real", "epsilon", "regret_raw", "regret_discounted", "record_status", "missing")}
            summary_record["branches"] = [{"metrics": package["production"]["metrics"]}]
            self.finished.append(summary_record)
            self.finalized[epoch] = self.clock()
            while len(self.finalized) > self.config.retention_completed_epochs:
                self.finalized.popitem(last=False)
            del self.pending[epoch]

    def shutdown(self):
        # Bounded evidence drain; worker transport remains bounded by its own timeout.
        deadline = self.clock() + self.config.shadow_result_deadline_s
        while self.pending and self.clock() < deadline:
            self.poll()
            time.sleep(.001)
        for package in list(self.pending.values()):
            self.expire(package, "shutdown")
        self.finalize()
        self.closed = True
        self.manager.close()  # Post-production only; cancels queued work, finite transport timeout.
        self.poll()
