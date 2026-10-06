"""Verify artifact integrity and independently replay every successful branch."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from csc.branches import execute_shadow
from csc.contracts import Anchor, Config, Event
from csc.world import ProductionWorld


def read_lines(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_source_identity(manifest, source_root=None):
    """Fail closed when replay code differs from the run's recorded CSC sources."""
    expected = manifest.get("source_hashes")
    if not expected:
        raise ValueError("run manifest has no source identity")
    root = Path(source_root) if source_root else Path(__file__).resolve().parent.parent
    mismatches = []
    for relative_path, expected_hash in expected.items():
        candidate = root / relative_path
        if not candidate.is_file() or sha256_file(candidate) != expected_hash:
            mismatches.append(relative_path)
    if mismatches:
        raise ValueError("source identity mismatch: " + ", ".join(sorted(mismatches)))
    return {"source_root": str(root), "files_verified": len(expected)}


def replay(path, source_root=None):
    path = Path(path)
    manifest = json.loads((path / "manifest.json").read_text())
    for filename, expected in manifest["artifact_hashes"].items():
        if sha256_file(path / filename) != expected:
            raise ValueError(f"artifact changed: {filename}")
    source_identity = verify_source_identity(manifest, source_root)
    config = Config(**manifest["config"])
    anchors = {a["snapshot_id"]: Anchor.from_envelope(a) for a in read_lines(path / "anchors.jsonl")}
    events = defaultdict(list)
    for event in read_lines(path / "events.jsonl"):
        events[event["epoch"]].append(event)
    journal = {}
    if config.execution_mode == "asynchronous":
        for entry in read_lines(path / "epoch_journal.jsonl"):
            if entry["epoch"] in journal or entry["status"] != "PRODUCTION_COMMITTED":
                raise ValueError("duplicate/invalid production commit")
            journal[entry["epoch"]] = entry
    checked, skipped = 0, 0
    for record in read_lines(path / "cfr.jsonl"):
        if config.execution_mode == "asynchronous":
            commit = journal.pop(record["epoch"], None)
            if commit is None or commit["anchor_hash"] != record["anchor_hash"] or commit["experiment_id"] != record["experiment_id"]:
                raise ValueError("comparison/production journal mismatch")
            actual = record["branches"][0]
            if commit["production"]["trace"] != actual["trace"] or commit["input_hash"] != actual["synchronization"]["input_hash"]:
                raise ValueError("production commit mutated")
        anchor = anchors[record["anchor_hash"]]
        for branch in record["branches"]:
            if branch["status"] != "REPORTED" or not branch.get("synchronization", {}).get("comparable"):
                skipped += 1
                continue
            if branch["role"] == "PRODUCTION":
                capability = object()
                world = ProductionWorld(anchor.hydrate(), capability, config)
                world.apply_plan(branch["action"], capability, "replay-only")
                trace = [world.step(Event(**e), tick) for tick, e in enumerate(events[record["epoch"]])]
            else:
                request = {"anchor": anchor.envelope(), "config": manifest["config"],
                           "branch": {k: branch[k] for k in ("branch_id", "experiment_id", "epoch", "role", "action", "parent_snapshot_id", "start_sequence", "end_sequence")},
                           "events": events[record["epoch"]]}
                trace = execute_shadow(request)["trace"]
            if trace != branch["trace"]:
                raise AssertionError(f"replay divergence: {branch['branch_id']}")
            checked += 1
    if journal and manifest["status"] == "COMPLETE":
        raise ValueError("complete run has unfinalized commits")
    return {"experiment_id": manifest["experiment_id"], "branches_replayed": checked,
            "incomplete_branches_skipped": skipped, "trajectory_mismatches": 0,
            "artifact_integrity": "VERIFIED", "source_identity": "VERIFIED",
            "source_identity_details": source_identity}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory")
    parser.add_argument("--source-root", help="repository/source bundle root recorded for the run")
    args = parser.parse_args()
    print(json.dumps(replay(args.run_directory, args.source_root), indent=2))
