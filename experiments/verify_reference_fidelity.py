"""Verify every CSC run cited by a reference-fidelity series."""
import argparse
import json
from pathlib import Path

from experiments.replay import replay


def verify(series):
    series = Path(series)
    rows = json.loads((series / "reference-summary.json").read_text())
    verified = []
    for row in rows:
        result = replay(row["run_path"])
        verified.append({"run_path": row["run_path"], **result})
    return {
        "series": str(series),
        "runs_verified": len(verified),
        "branches_replayed": sum(row["branches_replayed"] for row in verified),
        "trajectory_mismatches": sum(row["trajectory_mismatches"] for row in verified),
        "results": verified,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("series")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = verify(args.series)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("runs_verified", "branches_replayed", "trajectory_mismatches")}))
