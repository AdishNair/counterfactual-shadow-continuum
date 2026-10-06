"""Immutable prospective three-stage authored-reference collection and firewall."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys

from csc.contracts import ACTIONS, Config, Event, State, StateCaptureEngine, canonical
from csc.world import ProductionWorld, ShadowWorldModel, domain_metrics
from experiments import trust_reference as reference
from experiments.trust_selector import VERSION, validate_features

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "experiments/cycle4_trust_design.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hashed(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def write(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def lines(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def source_paths():
    return sorted(list((ROOT / "csc").glob("*.py")) + list((ROOT / "experiments").glob("*trust*")) +
                  [ROOT / "experiments/__init__.py", ROOT / "research/archive/cycle4/protocol_support/trust_signal_experiment_protocol.md",
                   ROOT / "research/archive/cycle4/protocol_support/cycle4_trust_preoutcome_specification.md",
                   ROOT / "research/archive/cycle4/protocol_support/cycle4_trust_report_template.md", ROOT / "tests/__init__.py",
                   ROOT / "tests/test_cycle4_trust.py", ROOT / "research/archive/cycle4/protocol_support/cycle4_trust_source_isolation_audit.md",
                   ROOT / "research/archive/cycle4/protocol_support/cycle4_trust_preflight_verification.json"])


def freeze(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    files = {}
    for path in source_paths():
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        files[rel] = sha(target)
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        git_sha = None
    write(destination / "source-manifest.json", {"files": files, "bundle_digest": hashed(files), "selector_version": VERSION, "git_sha":git_sha})
    return destination


def window(seed, demand, incident, count, start, identity, epoch, label):
    rng = random.Random(f"cycle4-v1:{seed}:{demand}:{incident}:{epoch}:{label}")
    events = []
    for offset in range(count):
        if demand == "light":
            ns, ew = int(rng.random() < .2), int(rng.random() < .2)
        else:
            heavy, light = rng.randrange(4), int(rng.random() < .5)
            ns, ew = (heavy, light) if (start + offset) % 120 < 60 else (light, heavy)
        sequence = start + offset
        events.append(Event(f"{identity}-{label}-{sequence}", identity, sequence, sequence, epoch,
                            ns, ew, incident == "blocked_ew"))
    return events


def best(values, tolerance):
    maximum = max(values.values())
    return [action for action in ACTIONS if action in values and maximum - values[action] <= tolerance]


def sign(value, tolerance):
    return 1 if value > tolerance else -1 if value < -tolerance else 0


def collect_run(condition, design):
    seed, horizon, demand, incident, mismatch = [condition[key] for key in ("seed", "horizon", "demand", "incident", "mismatch")]
    params = design["mismatch"][mismatch]
    config = Config(random_seed=seed, horizon_ticks=horizon, duration_epochs=1, warmup_epochs=0,
                    production_heterogeneity=params["heterogeneous"], shadow_service_rate=params["sem_rate"],
                    production_service_rate=design["production_rate"], model_incidents=params["model_incidents"])
    capability = object()
    world = ProductionWorld(State(rng_seed=seed), capability, config)
    observations = []
    run_id = f"s{seed}-h{horizon}-{demand}-{incident}-{mismatch}"
    for epoch in range(design["anchors_per_run"]):
        state = world.snapshot_state()
        action = "NS_GREEN" if state.queue_ns >= state.queue_ew else "EW_GREEN"
        identity = f"cycle4-{run_id}"
        history = window(seed, demand, incident, design["history_ticks_between_anchors"],
                         state.input_sequence_watermark + 1, identity, epoch, "history")
        world.apply_plan(action, capability, f"history-{epoch}")
        history_trace = [world.step(event, tick) for tick, event in enumerate(history)]
        state = world.snapshot_state()
        anchor = StateCaptureEngine().capture(state, identity, epoch)
        action = "NS_GREEN" if state.queue_ns >= state.queue_ew else "EW_GREEN"
        events = window(seed, demand, incident, horizon, state.input_sequence_watermark + 1, identity, epoch, "future")
        records = [asdict(event) for event in events]
        ref, sem = {}, {}
        for candidate in ACTIONS:
            _, trace = reference.simulate(asdict(state), candidate, records, horizon, design["production_rate"], params["heterogeneous"])
            ref[candidate] = {"trace": trace, "metrics": reference.metrics(trace), "utility": reference.value(trace)}
            model = ShadowWorldModel(anchor.hydrate(), config)
            trace = [model.step(event, candidate, tick) for tick, event in enumerate(events)]
            sem[candidate] = {"trace": trace, "metrics": domain_metrics(trace), "utility": -domain_metrics(trace)["mean_queue"]}
        # Production is actual authored execution, not reference substituted for observations.
        production = ProductionWorld(anchor.hydrate(), capability, config)
        production.apply_plan(action, capability, f"production-{epoch}")
        trace = [production.step(event, tick) for tick, event in enumerate(events)]
        if trace != ref[action]["trace"]:
            raise ValueError("independent reference disagrees with authoritative authored execution")
        production_utility = -domain_metrics(trace)["mean_queue"]
        alternatives = {candidate: sem[candidate]["utility"] for candidate in ACTIONS if candidate != action}
        selected = best(alternatives, design["tie_tolerance"])[0]
        epsilon = abs(sem[action]["utility"] - production_utility)
        divergence = sum(((a["queue_ns"] - m["queue_ns"]) ** 2 + (a["queue_ew"] - m["queue_ew"]) ** 2) ** .5
                         for a, m in zip(sem[selected]["trace"], sem[action]["trace"]))
        features = dict(horizon=horizon, epsilon=epsilon, estimated_improvement=sem[selected]["utility"] - production_utility,
                        divergence=divergence, capabilities={"incident_semantics": "blocked-ew-v1" if params["model_incidents"] else "unsupported"},
                        window_metadata={"incident_semantics": "blocked-ew-v1", "declared_at_decision": True,
                                         "requires_incident": any(event.blocked_ew for event in events)})
        selected_gain = ref[selected]["utility"] - production_utility
        oracle_gain = max(ref[candidate]["utility"] for candidate in alternatives) - production_utility
        observations.append(dict(run_id=run_id, **condition, anchor_index=epoch, anchor=anchor.envelope(),
                                 history=[asdict(event) for event in history], history_trace=history_trace, events=records,
                                 input_hash=hashed(records), production_action=action, production_trace=trace,
                                 production_utility=production_utility, config=asdict(config), sem=sem, reference=ref,
                                 features=features, feature_status=validate_features(features), selected_action=selected,
                                 reference_positive=selected_gain > design["tie_tolerance"],
                                 any_reference_positive=oracle_gain > design["tie_tolerance"], reference_gain=selected_gain,
                                 selected_error=abs(sem[selected]["utility"] - ref[selected]["utility"]),
                                 epsilon_coverage=abs(features["estimated_improvement"] - selected_gain) <= epsilon,
                                 ranking_agreement=best({a: sem[a]["utility"] for a in ACTIONS}, design["tie_tolerance"]) == best({a: ref[a]["utility"] for a in ACTIONS}, design["tie_tolerance"]),
                                 regret_sign_agreement=sign(features["estimated_improvement"], design["tie_tolerance"]) == sign(oracle_gain, design["tie_tolerance"]),
                                 choice_value_loss=max(ref[a]["utility"] for a in ACTIONS) - ref[selected]["utility"],
                                 alternative_margin=sorted(alternatives.values(), reverse=True)[0] - sorted(alternatives.values(), reverse=True)[1]))
        # Closed-loop authoritative future becomes the next history's starting state.
        world = production
    return observations


def collect(phase, output, calibration=None):
    design = json.loads(DESIGN.read_text())
    bundle_manifest = ROOT / "source-manifest.json"
    if not bundle_manifest.exists():
        raise ValueError("collection requires archived runnable source bundle")
    source = json.loads(bundle_manifest.read_text())
    if any(sha(ROOT / name) != value for name, value in source["files"].items()):
        raise ValueError("source bundle changed")
    if phase == "calibration":
        gate = json.loads(Path(calibration).read_text()) if calibration else {}
        if gate.get("development_feature_validation") != "PASS" or gate.get("bundle_digest") != source["bundle_digest"]:
            raise ValueError("frozen development feature-validation gate missing")
    if phase == "final-held-out":
        gate = json.loads(Path(calibration).read_text()) if calibration else {}
        if gate.get("selected_rule") is None or gate.get("bundle_digest") != source["bundle_digest"] or gate.get("decision")!="QUALIFIED_FOR_FINAL_ONLY":
            raise ValueError("heldout generation blocked: no qualifying frozen calibration rule")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    low, high = design["splits"][phase]
    conditions = [dict(zip(("seed", "horizon", "demand", "incident", "mismatch"), values)) for values in
                  itertools.product(range(low, high + 1), design["horizons"], design["demand"], design["incident"], design["mismatch"])]
    random.Random(design["order_seed"]).shuffle(conditions)
    write(output / "planned-conditions.json", conditions)
    write(output / "frozen-design.json", design)
    shutil.copytree(ROOT, output / "source")
    started = datetime.now(timezone.utc).isoformat()
    for index, condition in enumerate(conditions):
        rows = collect_run(condition, design)
        with (output / f"run-{index:04d}.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
            for row in rows:
                stream.write(canonical(row).decode() + "\n")
        if (index + 1) % 200 == 0:
            print(json.dumps({"phase": phase, "runs": index + 1, "total": len(conditions)}), flush=True)
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        git_sha = None
    artifacts = {path.relative_to(output).as_posix(): sha(path) for path in sorted(output.rglob("*")) if path.is_file()}
    write(output / "manifest.json", dict(status="COMPLETE", phase=phase, runs=len(conditions), anchors=len(conditions)*8,
                                         selector_version=VERSION, bundle_digest=source["bundle_digest"], config_hash=hashed(design),
                                         workload_hash=hashed({k: design[k] for k in ("demand", "incident", "anchors_per_run", "history_ticks_between_anchors")} ),
                                         source_hashes=source["files"], git_sha=source.get("git_sha",git_sha), runtime={"python":sys.version, "platform":platform.platform(),"dependencies":"Python standard library"},
                                         timestamps={"started_utc":started,"completed_utc":datetime.now(timezone.utc).isoformat()},
                                         prerequisite_hash=sha(calibration) if calibration else None, artifacts=artifacts,
                                         reference_kind=reference.REFERENCE_KIND, decision_timing="offline common-window evidence; epsilon available after production window"))
    print(json.dumps({"series":str(output),"status":"COMPLETE"}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze")
    parser.add_argument("--phase", choices=("development", "calibration", "final-held-out"))
    parser.add_argument("--output")
    parser.add_argument("--gate")
    args = parser.parse_args()
    if args.freeze:
        print(freeze(args.freeze))
    else:
        collect(args.phase, args.output, args.gate)


if __name__ == "__main__":
    main()
