"""Frozen online selector interface. This module cannot access oracle records."""
import math

VERSION = "cycle4-frozen-v1"
FIELDS = {"horizon", "epsilon", "estimated_improvement", "divergence", "capabilities", "window_metadata"}


def validate_features(features):
    if set(features) != FIELDS:
        raise ValueError("selector feature allowlist violation")
    if set(features["capabilities"]) != {"incident_semantics"}:
        raise ValueError("capability allowlist violation")
    metadata = features["window_metadata"]
    if set(metadata) != {"incident_semantics", "declared_at_decision", "requires_incident"}:
        raise ValueError("metadata allowlist violation")
    for key in ("epsilon", "estimated_improvement", "divergence"):
        if not isinstance(features[key], (float, int)) or not math.isfinite(features[key]):
            return "UNAVAILABLE"
    if features["epsilon"] < 0 or features["divergence"] < 0 or features["horizon"] not in (2, 6, 20):
        return "UNAVAILABLE"
    if not metadata["declared_at_decision"] or metadata["incident_semantics"] != "blocked-ew-v1":
        return "UNKNOWN_OR_LATE_SEMANTICS"
    if metadata["requires_incident"] and features["capabilities"]["incident_semantics"] != "blocked-ew-v1":
        return "UNSUPPORTED_SEMANTICS"
    return "AVAILABLE"


def select(features, rule):
    status = validate_features(features)
    if status != "AVAILABLE":
        return False, status
    accepted = features["estimated_improvement"] > features["epsilon"]
    if rule["family"] != "BASELINE":
        accepted = accepted and features["divergence"] <= rule["d"]
    if rule["family"] == "DIVERGENCE_HORIZON":
        accepted = accepted and features["horizon"] <= rule["h"]
    return accepted, status
