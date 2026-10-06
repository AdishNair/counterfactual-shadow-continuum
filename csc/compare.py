"""Only comparable, full-window observations enter utility/regret accounting."""
import math
import sys
from .contracts import digest


# Leaves headroom for subtraction, absolute differences, and discounted regret.
# This is an arithmetic safety bound, not a scientific acceptance threshold.
MAX_SAFE_UTILITY_MAGNITUDE = sys.float_info.max / 4


def utility(metrics, config):
    value = -(config.queue_weight * metrics["mean_queue"] +
              config.wait_weight * metrics["waiting_vehicle_ticks"] +
              config.switch_weight * metrics["phase_switches"])
    if not math.isfinite(value) or abs(value) > MAX_SAFE_UTILITY_MAGNITUDE:
        raise ValueError("utility exceeds finite derived-arithmetic envelope")
    return value


def finite_difference(left, right, name):
    value = left - right
    if not math.isfinite(value):
        raise ValueError(f"nonfinite {name}")
    return value


class RegretCalculator:
    @staticmethod
    def calculate(real, alternatives, epsilon):
        if not alternatives:
            return {"regret_signed": None, "regret_raw": None, "regret_discounted": None}
        signed = finite_difference(max(alternatives), real, "regret")
        discounted = None if epsilon is None else max(0, finite_difference(signed, epsilon, "discounted regret"))
        return {"regret_signed": signed, "regret_raw": max(0, signed),
                "regret_discounted": discounted}


class OutcomeComparisonEngine:
    def __init__(self, config):
        self.config, self.epsilon_ewma = config, None
        self.utility_config = {"queue_weight": config.queue_weight, "wait_weight": config.wait_weight,
                               "switch_weight": config.switch_weight, "form": "negative_weighted_cost"}

    def compare(self, anchor, expected, production, shadows):
        if not production or production.get("status") != "REPORTED" or production.get("provenance") != "REALISED":
            return None
        all_results, accepted, excluded = [production] + shadows, [], []
        expected_map = {b.branch_id: b for b in expected}
        seen = set()
        for result in all_results:
            bid = result["branch_id"]
            if bid in seen or bid not in expected_map:
                raise ValueError("duplicate/unplanned outcome")
            seen.add(bid)
            b = expected_map[bid]
            valid = (result.get("status") == "REPORTED" and
                     result.get("anchor_hash") == anchor.snapshot_id and
                     result.get("observation_window") == [b.start_sequence, b.end_sequence] and
                     result.get("synchronization", {}).get("comparable") and
                     result.get("synchronization", {}).get("input_hash") == production["synchronization"]["input_hash"] and
                     len(result.get("trace", [])) == b.end_sequence - b.start_sequence + 1 and
                     result.get("role") == b.role and result.get("action") == b.action and
                     result.get("experiment_id") == b.experiment_id and result.get("epoch") == b.epoch and
                     result.get("provenance") == ("REALISED" if b.role == "PRODUCTION" else "ESTIMATED"))
            if not valid:
                excluded.append(bid)
                result["utility"] = None
                continue
            try:
                result["utility"] = utility(result["metrics"], self.config)
            except (KeyError, TypeError, ValueError, OverflowError):
                excluded.append(bid)
                result["utility"] = None
                continue
            accepted.append(result)
        if production not in accepted:
            return None
        mirrors = [r for r in accepted if r["role"] == "MIRROR"]
        alternatives = [r for r in accepted if r["role"] == "SHADOW"]
        real = production["utility"]
        if mirrors:
            epsilon = abs(finite_difference(mirrors[0]["utility"], real, "mirror epsilon"))
            self.epsilon_ewma = epsilon if self.epsilon_ewma is None else .05 * epsilon + .95 * self.epsilon_ewma
            epsilon_source = "MEASURED"
        else:
            epsilon, epsilon_source = self.epsilon_ewma, "ESTIMATED" if self.epsilon_ewma is not None else "UNAVAILABLE"
        missing = sorted(set(expected_map) - {r["branch_id"] for r in accepted})
        status = "PRODUCTION_ONLY" if not mirrors and not alternatives else "PARTIAL" if missing else "COMPLETE"
        divergence = []
        if mirrors:
            for p, m in zip(production["trace"], mirrors[0]["trace"]):
                divergence.append(math.hypot(p["queue_ns"] - m["queue_ns"], p["queue_ew"] - m["queue_ew"]))
        return {"schema_version": 1, "cfr_id": f"{production['experiment_id']}:{production['epoch']}",
                "experiment_id": production["experiment_id"], "epoch": production["epoch"], "site_id": "J1",
                "anchor_hash": anchor.snapshot_id, "policy_version": "heuristic-v1", "audited": False,
                "utility_config_hash": digest(self.utility_config), "horizon_ticks": self.config.horizon_ticks,
                "u_real": real, "u_mirror": mirrors[0]["utility"] if mirrors else None,
                "epsilon": epsilon, "epsilon_ewma": self.epsilon_ewma, "epsilon_source": epsilon_source,
                **RegretCalculator.calculate(real, [r["utility"] for r in alternatives], epsilon),
                "best_alt_action": max(alternatives, key=lambda r: r["utility"])["action"] if alternatives else None,
                "record_status": status, "missing": missing, "excluded": excluded,
                "mirror_divergence_l2": divergence, "branches": all_results}
