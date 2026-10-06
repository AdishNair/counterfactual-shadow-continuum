"""Authored-production reference evaluator, independent of ShadowWorldModel.

This module intentionally imports only the production transition model and shared
contracts/metric. It is a software-environment reference, not physical ground
truth.
"""
from csc.compare import utility
from csc.world import ProductionWorld, domain_metrics


REFERENCE_KIND = "AUTHORED_PRODUCTION_SOFTWARE_ENVIRONMENT"


def trace(anchor, action, events, config):
    capability = object()
    world = ProductionWorld(anchor.hydrate(), capability, config)
    world.apply_plan(action, capability, "reference-only")
    return [world.step(event, tick) for tick, event in enumerate(events)]


def outcome(anchor, action, events, config):
    action_trace = trace(anchor, action, events, config)
    return {
        "action": action,
        "trace": action_trace,
        "metrics": domain_metrics(action_trace),
        "utility": utility(domain_metrics(action_trace), config),
        "reference_kind": REFERENCE_KIND,
    }
