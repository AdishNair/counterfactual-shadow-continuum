"""Versioned application contracts and canonical, immutable state anchors."""
from dataclasses import asdict, dataclass, field
import hashlib
import json
import math


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


ACTIONS = ("NS_GREEN", "EW_GREEN", "BALANCED")
ROLES = ("PRODUCTION", "MIRROR", "SHADOW")


@dataclass
class State:
    schema_version: int = 1
    state_version: int = 0
    junction_id: str = "J1"
    queue_ns: float = 14
    queue_ew: float = 3
    signal_phase: str = "NS_GREEN"
    phase_elapsed: int = 0
    recent_arrivals: list = field(default_factory=lambda: [0, 0])
    policy_context: dict = field(default_factory=lambda: {"version": "heuristic-v1"})
    input_sequence_watermark: int = -1
    rng_seed: int = 1

    def validate(self):
        if self.schema_version != 1 or self.junction_id != "J1":
            raise ValueError("unsupported state schema/site")
        if self.signal_phase not in ACTIONS[:2]:
            raise ValueError("invalid phase")
        for q in (self.queue_ns, self.queue_ew):
            if not math.isfinite(q) or q < 0:
                raise ValueError("queues must be finite and nonnegative")
        if self.phase_elapsed < 0 or self.state_version < 0:
            raise ValueError("negative state counter")
        return self


@dataclass(frozen=True)
class Anchor:
    snapshot_id: str
    payload: bytes

    def hydrate(self):
        if hashlib.sha256(self.payload).hexdigest() != self.snapshot_id:
            raise ValueError("anchor hash mismatch")
        obj = json.loads(self.payload)
        state = State(**obj["state"]).validate()
        if obj["schema_version"] != 1:
            raise ValueError("unsupported anchor schema")
        return state

    def envelope(self):
        return {"snapshot_id": self.snapshot_id, "payload": self.payload.decode()}

    @classmethod
    def from_envelope(cls, obj):
        anchor = cls(obj["snapshot_id"], obj["payload"].encode())
        anchor.hydrate()
        return anchor


class StateCaptureEngine:
    def capture(self, state, experiment_id, epoch):
        state.validate()
        payload = canonical({"schema_version": 1, "experiment_id": experiment_id,
                             "epoch": epoch, "decision_time": state.input_sequence_watermark + 1,
                             "state": asdict(state)})
        return Anchor(hashlib.sha256(payload).hexdigest(), payload)


@dataclass(frozen=True)
class Event:
    event_id: str
    experiment_id: str
    sequence_number: int
    event_time: int
    epoch: int
    arrivals_ns: int
    arrivals_ew: int
    blocked_ew: bool = False
    source: str = "seeded-test-environment"
    junction_id: str = "J1"
    event_type: str = "external_arrivals"

    def validate(self):
        if self.sequence_number < 0 or self.event_time != self.sequence_number:
            raise ValueError("invalid event clock")
        if self.arrivals_ns < 0 or self.arrivals_ew < 0 or self.junction_id != "J1":
            raise ValueError("invalid arrival/site")
        return self


@dataclass(frozen=True)
class Branch:
    branch_id: str
    experiment_id: str
    epoch: int
    role: str
    action: str
    parent_snapshot_id: str
    start_sequence: int
    end_sequence: int

    def __post_init__(self):
        if self.role not in ROLES or self.action not in ACTIONS:
            raise ValueError("invalid branch role/action")


@dataclass
class Config:
    schema_version: int = 1
    experiment_name: str = "csc-k2"
    random_seed: int = 1
    workload_profile: str = "peak"
    duration_epochs: int = 100
    warmup_epochs: int = 10
    horizon_ticks: int = 6
    shadow_count: int = 2
    mirror_count: int = 1
    production_policy: str = "queue"
    synchronization_enabled: bool = True
    learning_enabled: bool = False
    failure_scenario: str = "none"
    failure_epoch: int = 10
    shadow_timeout_s: float = 2
    shadow_delay_s: float = 0.01
    shadow_service_rate: float = 2
    production_service_rate: float = 2
    production_heterogeneity: bool = True
    model_incidents: bool = False
    queue_weight: float = 1
    wait_weight: float = 0
    switch_weight: float = 0
    max_shadow_slots: int = 3
    capture_max_bytes: int = 65536
    backend: str = "local"
    remote_shadow_urls: list = field(default_factory=list)
    execution_mode: str = "synchronous"
    max_pending_shadow_tasks: int = 12
    max_pending_epochs: int = 16
    shadow_result_deadline_s: float = 1
    production_period_s: float = 0
    shadow_injected_delay_s: float = 0
    shadow_load: str = "normal"
    worker_mode: str = "cold"
    worker_max_tasks: int = 100
    worker_max_lifetime_s: float = 60
    retention_completed_epochs: int = 64
    max_result_bytes: int = 4 * 1024 * 1024
    max_assignment_bytes: int = 4 * 1024 * 1024
    max_pending_shadow_bytes: int = 16 * 1024 * 1024
    evidence_spool_max_items: int = 256
    evidence_spool_max_bytes: int = 16 * 1024 * 1024
    evidence_spool_max_attempts: int = 3
    evidence_spool_drain_s: float = 1

    def validate(self):
        if self.schema_version != 1:
            raise ValueError("unsupported config version")
        for name in ("duration_epochs", "horizon_ticks", "shadow_count", "mirror_count",
                     "warmup_epochs", "max_shadow_slots", "failure_epoch", "capture_max_bytes", "random_seed"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if not 0 < self.duration_epochs <= 100000 or not 0 < self.horizon_ticks <= 1000:
            raise ValueError("duration/horizon outside bounded prototype limits")
        if self.warmup_epochs >= self.duration_epochs or self.shadow_count > 2 or self.mirror_count > 2:
            raise ValueError("invalid warmup or branch count (at most two distinct alternatives)")
        if self.workload_profile not in ("light", "peak", "incident"):
            raise ValueError("unknown workload")
        if self.production_policy not in ("queue", "fixed", "predictive"):
            raise ValueError("unknown policy")
        if self.failure_scenario not in ("none", "crash", "timeout", "drop", "duplicate", "reorder", "delay", "model_error", "resource_budget", "capture", "worker_contamination"):
            raise ValueError("unknown failure scenario")
        if self.backend not in ("local", "http"):
            raise ValueError("backend must be local or http")
        if self.backend == "http" and not self.remote_shadow_urls:
            raise ValueError("http backend needs remote_shadow_urls")
        for name in ("shadow_timeout_s", "shadow_delay_s", "shadow_service_rate", "production_service_rate",
                     "queue_weight", "wait_weight", "switch_weight"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) < 0:
                raise ValueError(f"invalid {name}")
        if self.shadow_timeout_s <= 0 or self.max_shadow_slots > 4:
            raise ValueError("invalid branch resource budget")
        if self.learning_enabled:
            raise ValueError("learning is deferred until distributed containment is validated")
        if self.execution_mode not in ("synchronous", "asynchronous"):
            raise ValueError("unknown execution mode")
        for name in ("max_pending_shadow_tasks", "max_pending_epochs"):
            if type(getattr(self, name)) is not int or not 0 < getattr(self, name) <= 10000:
                raise ValueError("invalid async capacity")
        for name in ("shadow_result_deadline_s", "production_period_s", "shadow_injected_delay_s"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) < 0:
                raise ValueError("invalid async timing")
        if self.shadow_result_deadline_s <= 0 or self.shadow_load not in ("normal", "cpu", "memory"):
            raise ValueError("invalid async deadline/load")
        if self.worker_mode not in ("cold", "warm") or (self.worker_mode == "warm" and self.backend != "local"):
            raise ValueError("warm workers require local backend")
        for name in ("worker_max_tasks", "retention_completed_epochs", "max_result_bytes",
                     "max_assignment_bytes", "max_pending_shadow_bytes", "evidence_spool_max_items",
                     "evidence_spool_max_bytes", "evidence_spool_max_attempts"):
            if type(getattr(self, name)) is not int or not 0 < getattr(self, name) <= 16777216:
                raise ValueError("invalid worker/retention/body bound")
        if (not math.isfinite(self.worker_max_lifetime_s) or self.worker_max_lifetime_s <= 0 or
                not math.isfinite(self.evidence_spool_drain_s) or self.evidence_spool_drain_s < 0):
            raise ValueError("invalid worker lifetime")
        return self

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8-sig") as stream:
            return cls(**json.load(stream)).validate()
