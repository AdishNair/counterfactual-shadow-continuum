"""Paired baseline/K sweep. Small defaults are smoke evidence, not paper protocol."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import uuid
from csc.contracts import Config
from csc.runner import run


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(path)


def create_series_dir(parent, series_id=None):
    parent = Path(parent)
    parent.mkdir(parents=True, exist_ok=True)
    series_id = series_id or f"matrix-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"
    if not series_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for char in series_id):
        raise ValueError("series_id must be a safe directory name")
    destination = parent / series_id
    destination.mkdir(exist_ok=False)
    return destination


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", default="experiments/matrix.json")
    parser.add_argument("--output", default="results/matrix", help="parent directory for a new immutable series")
    parser.add_argument("--series-id", help="unique immutable series name; generated when omitted")
    args = parser.parse_args()
    matrix_path = Path(args.matrix)
    matrix = json.loads(matrix_path.read_text())
    if matrix["schema_version"] != 1:
        raise ValueError("unsupported matrix schema")
    series = create_series_dir(args.output, args.series_id)
    manifest = {"schema_version": 1, "kind": "matrix_series", "status": "RUNNING",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "matrix_path": str(matrix_path),
                "matrix_sha256": hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
                "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "members": []}
    write_json(series / "series-manifest.json", manifest)
    results = []
    for seed in matrix["seeds"]:
        baseline = None
        for k in matrix["shadow_counts"]:
            config = Config(random_seed=seed, shadow_count=k, mirror_count=int(k > 0),
                            experiment_name=f"k{k}-seed{seed}", duration_epochs=matrix["duration_epochs"],
                            warmup_epochs=matrix["warmup_epochs"], workload_profile=matrix["workload_profile"])
            path, summary = run(config, series)
            if k == 0:
                baseline = summary
            if baseline:
                assert summary["workload_sha256"] == baseline["workload_sha256"]
                assert summary["production_semantic_sha256"] == baseline["production_semantic_sha256"]
            results.append({"seed": seed, "k": k, "mirror_count": config.mirror_count,
                            "path": str(path), "summary": summary})
            manifest["members"].append({"seed": seed, "k": k, "path": str(path),
                                        "manifest_sha256": hashlib.sha256((path / "manifest.json").read_bytes()).hexdigest()})
            print(json.dumps({"completed": str(path), "seed": seed, "k": k}), flush=True)
    write_json(series / "matrix-summary.json", results)
    manifest.update(status="COMPLETE", completed_utc=datetime.now(timezone.utc).isoformat(),
                    matrix_summary_sha256=hashlib.sha256((series / "matrix-summary.json").read_bytes()).hexdigest())
    write_json(series / "series-manifest.json", manifest)
    print(json.dumps({"series": str(series), "status": "COMPLETE"}))


if __name__ == "__main__":
    main()
