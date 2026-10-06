"""Verify immutable factorial evidence, schedule completeness, and code identity."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_lines(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def verify(series):
    series = Path(series)
    manifest = json.loads((series / "series-manifest.json").read_text())
    if manifest["status"] != "COMPLETE" or manifest["failed_runs"]:
        raise ValueError("series is incomplete or contains failed runs")
    output_hashes = {name: digest(series / name) for name in manifest["output_sha256"]}
    mismatched_outputs = [name for name, value in output_hashes.items() if value != manifest["output_sha256"][name]]
    if mismatched_outputs:
        raise ValueError("artifact hash mismatch: " + ", ".join(mismatched_outputs))
    root = Path(__file__).resolve().parent.parent
    mismatched_sources = [name for name, value in manifest["source_hashes"].items()
                          if not (root / name).is_file() or digest(root / name) != value]
    if mismatched_sources:
        raise ValueError("source identity mismatch: " + ", ".join(mismatched_sources))
    planned = json.loads((series / "planned-conditions.json").read_text())
    summaries = read_lines(series / "run-summaries.jsonl")
    observations = read_lines(series / "anchor-observations.jsonl")
    actions = read_lines(series / "action-observations.jsonl")
    if len(planned) != len(summaries) or len(manifest["completed_runs"]) != len(planned):
        raise ValueError("planned/completed run count mismatch")
    if len(observations) != 3 * len(summaries) or len(actions) != 3 * len(observations):
        raise ValueError("unexpected anchor/action observation count")
    if any(row.get("reference_kind") != "AUTHORED_PRODUCTION_SOFTWARE_ENVIRONMENT" for row in observations if row["comparable"]):
        raise ValueError("unexpected reference kind")
    return {"series": str(series), "runs_verified": len(summaries),
            "anchors_verified": len(observations), "action_observations_verified": len(actions),
            "artifact_integrity": "VERIFIED", "source_identity": "VERIFIED",
            "reference_kind": "AUTHORED_PRODUCTION_SOFTWARE_ENVIRONMENT",
            "verifier_sha256": digest(__file__)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("series")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = verify(args.series)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
