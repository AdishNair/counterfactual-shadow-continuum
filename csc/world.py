"""Independent authoritative queue simulator and approximate shadow world.

No physical traffic is controlled. Randomness is keyed by seed/sequence so it
does not depend on scheduling, branch identity, or the number of alternatives.
"""
from dataclasses import asdict
import random

from .contracts import ACTIONS, Event, State


def workload(config, experiment_id):
    rng = random.Random(config.random_seed)
    for seq in range(config.duration_epochs * config.horizon_ticks):
        if config.workload_profile == "light":
            ns, ew = int(rng.random() < .2), int(rng.random() < .2)
        else:
            # Demand direction changes halfway through each 120-tick cycle.
            heavy, light = rng.randrange(4), int(rng.random() < .5)
            ns, ew = (heavy, light) if seq % 120 < 60 else (light, heavy)
        total = config.duration_epochs * config.horizon_ticks
        incident = config.workload_profile == "incident" and total // 3 <= seq < 2 * total // 3
        yield Event(f"arrival-{seq}", experiment_id, seq, seq, seq // config.horizon_ticks,
                    ns, ew, incident)


def phase_for(action, tick, horizon):
    if action not in ACTIONS:
        raise ValueError("unknown action")
    if action == "BALANCED":
        return "NS_GREEN" if tick < (horizon + 1) // 2 else "EW_GREEN"
    return action


class ProductionWorld:
    """Authoritative test-world state; mutation requires the gateway capability.

    Capability privacy is an application boundary, not a Python security sandbox.
    Shadow workers never receive this instance or its capability.
    """

    def __init__(self, state, capability, config):
        self.__state = State(**asdict(state)).validate()
        self.__capability = capability
        self.config = config
        self.action = None
        self.audit = []
        self.denied_mutations = 0

    def snapshot_state(self):
        return State(**asdict(self.__state))

    def apply_plan(self, action, capability, correlation_id):
        if capability is not self.__capability:
            self.denied_mutations += 1
            raise PermissionError("authoritative mutation requires gateway capability")
        if action not in ACTIONS:
            raise ValueError("invalid signal plan")
        self.action = action
        self.audit.append({"correlation_id": correlation_id, "action": action})

    def step(self, event, tick):
        if self.action is None:
            raise RuntimeError("no authorized plan")
        state = self.__state
        event.validate()
        if event.sequence_number != state.input_sequence_watermark + 1:
            raise ValueError("production input gap")
        phase = phase_for(self.action, tick, self.config.horizon_ticks)
        switched = phase != state.signal_phase
        elapsed = 0 if switched else state.phase_elapsed
        capacity = self.config.production_service_rate * (.5 if elapsed < 2 else 1)
        # Independent per-tick heterogeneous discharge; deliberately absent in SEM.
        if self.config.production_heterogeneity:
            rng = random.Random(f"discharge:{state.rng_seed}:{event.sequence_number}")
            capacity *= rng.choice((.5, 1, 1, 1.5))
        state.queue_ns += event.arrivals_ns
        state.queue_ew += event.arrivals_ew
        departed = 0
        if phase == "NS_GREEN":
            departed = min(state.queue_ns, capacity)
            state.queue_ns -= departed
        elif not event.blocked_ew:
            departed = min(state.queue_ew, capacity)
            state.queue_ew -= departed
        state.signal_phase = phase
        state.phase_elapsed = elapsed + 1
        state.recent_arrivals = [event.arrivals_ns, event.arrivals_ew]
        state.input_sequence_watermark = event.sequence_number
        state.state_version += 1
        return observation(state, departed, switched)


class ShadowWorldModel:
    """Deterministic fluid model; no production object, credentials, or device API."""

    def __init__(self, state, config):
        self.state = State(**asdict(state)).validate()
        self.config = config

    def step(self, event, action, tick):
        # Separate transition implementation makes model fidelity falsifiable.
        s = self.state
        p = phase_for(action, tick, self.config.horizon_ticks)
        switched = p != s.signal_phase
        age = 0 if switched else s.phase_elapsed
        service = self.config.shadow_service_rate * (0.5 if age < 2 else 1.0)
        queues = [s.queue_ns + event.arrivals_ns, s.queue_ew + event.arrivals_ew]
        active = 0 if p == "NS_GREEN" else 1
        blocked = active == 1 and event.blocked_ew and self.config.model_incidents
        served = 0 if blocked else min(service, queues[active])
        queues[active] -= served
        s.queue_ns, s.queue_ew = queues
        s.signal_phase, s.phase_elapsed = p, age + 1
        s.recent_arrivals = [event.arrivals_ns, event.arrivals_ew]
        s.state_version += 1
        s.input_sequence_watermark = event.sequence_number
        return observation(s, served, switched)


def observation(state, departed, switched):
    return {"sequence_number": state.input_sequence_watermark, "queue_ns": state.queue_ns,
            "queue_ew": state.queue_ew, "departed": departed,
            "switched": int(switched), "phase": state.signal_phase}


def domain_metrics(trace):
    if not trace:
        return {"mean_queue": 0, "waiting_vehicle_ticks": 0, "throughput": 0, "phase_switches": 0,
                "final_queue": 0}
    waiting = sum(t["queue_ns"] + t["queue_ew"] for t in trace)
    return {"mean_queue": waiting / len(trace), "waiting_vehicle_ticks": waiting,
            "throughput": sum(t["departed"] for t in trace),
            "phase_switches": sum(t["switched"] for t in trace),
            "final_queue": trace[-1]["queue_ns"] + trace[-1]["queue_ew"]}
