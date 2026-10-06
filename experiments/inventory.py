"""Read-only inventory of result directories for provenance review."""
import argparse
import csv
import json
from pathlib import Path


def indexed_paths(root, index_name):
    index = root / index_name
    if not index.is_file():
        return set()
    value = json.loads(index.read_text())
    rows = value if isinstance(value, list) else value.get("runs", [])
    return {str(Path(row["path"]).resolve()) for row in rows if "path" in row}


def inventory(results_root, output):
    results_root, output = Path(results_root), Path(output)
    records = []
    for collection, index_name in (("matrix", "matrix-summary.json"), ("validation", "validation-summary.json")):
        root = results_root / collection
        indexed = indexed_paths(root, index_name)
        if not root.is_dir():
            continue
        for child in sorted(path for path in root.iterdir() if path.is_dir()):
            manifest_path = child / "manifest.json"
            if not manifest_path.is_file():
                continue
            manifest = json.loads(manifest_path.read_text())
            records.append({"collection": collection, "run_directory": str(child),
                            "indexed_by_current_aggregate": str(child.resolve()) in indexed,
                            "experiment_id": manifest.get("experiment_id"),
                            "timestamp_utc": manifest.get("timestamp_utc"),
                            "config_hash": manifest.get("config_hash"),
                            "runner_source_hash": manifest.get("source_hashes", {}).get("csc/runner.py"),
                            "manifest_status": manifest.get("status")})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]) if records else ["collection"])
        writer.writeheader()
        writer.writerows(records)
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--output", default="research/tables/result_series_inventory.csv")
    args = parser.parse_args()
    print(f"inventoried {len(inventory(args.results_root, args.output))} runs")
