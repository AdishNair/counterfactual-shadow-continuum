"""Verify every matrix run and persist reproducibility evidence separately."""
import argparse
import json
from pathlib import Path
from experiments.replay import replay


def verify(root, source_root=None):
    root = Path(root)
    matrix = json.loads((root / "matrix-summary.json").read_text())
    checks = [replay(row["path"], source_root) for row in matrix]
    result = {"runs_verified": len(checks), "branches_replayed": sum(c["branches_replayed"] for c in checks),
              "trajectory_mismatches": sum(c["trajectory_mismatches"] for c in checks), "checks": checks}
    (root / "replay-verification.json").write_text(json.dumps(result, indent=2))
    return {k: v for k, v in result.items() if k != "checks"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", default="results/matrix", nargs="?")
    parser.add_argument("--source-root", help="repository/source bundle root recorded for the run")
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.source_root), indent=2))
