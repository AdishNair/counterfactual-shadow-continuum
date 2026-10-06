"""Source-isolated authored J1 reference. No CSC imports or selector dependencies."""
from copy import deepcopy
import random

REFERENCE_KIND = "SOURCE_ISOLATED_AUTHORED_SOFTWARE_REFERENCE"


def discharge(seed, sequence):
    return random.Random(f"discharge:{seed}:{sequence}").choice((.5, 1, 1, 1.5))


def simulate(state, action, events, horizon, rate=2, heterogeneous=False):
    """Accept plain immutable-input records; return fresh state and observations."""
    if action not in ("NS_GREEN", "EW_GREEN", "BALANCED"):
        raise ValueError("unknown action")
    current, trace = deepcopy(state), []
    for tick, event in enumerate(events):
        if event["sequence_number"] != current["input_sequence_watermark"] + 1:
            raise ValueError("reference input gap")
        phase = action
        if action == "BALANCED":
            phase = "NS_GREEN" if 2 * tick < horizon + (horizon % 2) else "EW_GREEN"
        changed = phase != current["signal_phase"]
        age = 0 if changed else current["phase_elapsed"]
        available = rate / 2 if age < 2 else rate
        if heterogeneous:
            available *= discharge(current["rng_seed"], event["sequence_number"])
        current["queue_ns"] += event["arrivals_ns"]
        current["queue_ew"] += event["arrivals_ew"]
        queue = "queue_ns" if phase == "NS_GREEN" else "queue_ew"
        exits = 0 if phase == "EW_GREEN" and event["blocked_ew"] else min(available, current[queue])
        current[queue] -= exits
        current.update(signal_phase=phase, phase_elapsed=age + 1,
                       recent_arrivals=[event["arrivals_ns"], event["arrivals_ew"]],
                       input_sequence_watermark=event["sequence_number"],
                       state_version=current["state_version"] + 1)
        trace.append(dict(sequence_number=event["sequence_number"], queue_ns=current["queue_ns"],
                          queue_ew=current["queue_ew"], departed=exits, switched=int(changed), phase=phase))
    return current, trace


def metrics(trace):
    total = sum(row["queue_ns"] + row["queue_ew"] for row in trace)
    return dict(mean_queue=total / len(trace) if trace else 0, waiting_vehicle_ticks=total,
                throughput=sum(row["departed"] for row in trace),
                phase_switches=sum(row["switched"] for row in trace),
                final_queue=trace[-1]["queue_ns"] + trace[-1]["queue_ew"] if trace else 0)


def value(trace):
    return -metrics(trace)["mean_queue"]
