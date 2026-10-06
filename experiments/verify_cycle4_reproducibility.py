"""Deterministically aggregate Cycle 4 raw-series reproducibility checks."""
import argparse
import json
import hashlib
from pathlib import Path
import subprocess
import sys

from experiments.verify_cycle4_trust import verify as verify_trust


ROOT = Path(__file__).resolve().parent.parent
DEVELOPMENT = ROOT / "results/cycle4-trust/development-20261005-v1"
CALIBRATION = ROOT / "results/cycle4-trust/calibration-20261005-v1"
ASYNC = ROOT / "results/cycle4-async/local-20261005-v1"
CALIBRATION_ANALYSIS = ROOT / "research/tables/cycle4-trust-calibration-v1"
LEDGER = ROOT / "research/archive/cycle4/protocol_support/cycle4_trust_stage_ledger.json"


def run(output):
    """Verify split series, archived async source, and auditable final-stage gate."""
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    async_verification = output.with_name("cycle4-reproducibility-async-verification.json")
    subprocess.run(
        [sys.executable, "-m", "experiments.cycle4_async", "verify", str(ASYNC),
         "--output", str(async_verification)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    trust_reports = []
    for series in (DEVELOPMENT, CALIBRATION):
        archive = series / "source"
        report_path = output.with_name(series.name + "-archived-verification.json")
        command = [sys.executable, "-m", "experiments.verify_cycle4_trust",
                   str(series), "--output", str(report_path)]
        if series == CALIBRATION:
            command.extend(["--analysis", str(CALIBRATION_ANALYSIS)])
        subprocess.run(command, cwd=archive, check=True, capture_output=True, text=True)
        trust_reports.append(json.loads(report_path.read_text(encoding="utf-8")))
    development, calibration = trust_reports
    regenerated = output.parent / "cycle4-trust-archived-reanalysis-v1"
    if not regenerated.exists():
        subprocess.run([sys.executable, "-m", "experiments.analyze_cycle4_trust",
                        str(CALIBRATION), "--output", str(regenerated)],
                       cwd=CALIBRATION / "source", check=True, capture_output=True, text=True)
    analysis_matches = {}
    for name in ("calibration-selection.json", "candidate-cell-summary.csv",
                 "candidate-run-summary.csv", "negative-controls.json"):
        analysis_matches[name] = (hashlib.sha256((regenerated/name).read_bytes()).hexdigest()
                                  == hashlib.sha256((CALIBRATION_ANALYSIS/name).read_bytes()).hexdigest())
    async_result = json.loads(async_verification.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    final_series = sorted(str(path.relative_to(ROOT)).replace("\\", "/")
                          for path in (ROOT / "results/cycle4-trust").glob("final-heldout-*"))
    outcomes = {
        "development": development,
        "calibration": calibration,
        "async": async_result,
        "trust_final_heldout_directories": final_series,
        "stage_ledger": ledger,
    }
    failures = []
    if not all(analysis_matches.values()):
        failures.append("trust_full_analysis_regeneration")
    if not development["passed"]:
        failures.append("development_verification")
    if not calibration["passed"]:
        failures.append("calibration_verification")
    if async_result["status"] != "VERIFIED":
        failures.append("async_verification")
    if final_series:
        failures.append("unexpected_final_heldout_series")
    if ledger["stages"][-1]["state"] != "NOT GENERATED; forbidden because calibration selected no rule":
        failures.append("stage_ledger_final_state")
    result = {
        "status": "VERIFIED" if not failures else "FAILED",
        "scope": "Cycle 4 immutable series only; historical series are not rewritten or rehashed here",
        "trust_development": {key: development[key] for key in ("passed", "phase", "counts", "expected_runs", "expected_cells", "seed_range", "split_overlap", "bundle_digest")},
        "trust_calibration": {key: calibration[key] for key in ("passed", "phase", "counts", "expected_runs", "expected_cells", "seed_range", "split_overlap", "bundle_digest", "analysis_candidate_checks")},
        "async": {key: async_result[key] for key in ("status", "runs_verified", "branches_replayed", "source_archive_hashes_verified", "raw_summary_regeneration", "replay_execution_source")},
        "trust_final_heldout_directories": final_series,
        "trust_verification_source": "ARCHIVED_SOURCE_BUNDLE",
        "trust_full_analysis_regeneration": analysis_matches,
        "heldout_access_audit": "runner gating, immutable stage ledger and absence of a final series; arbitrary filesystem reads are not observable",
        "failures": failures,
        "machine_details": str(async_verification.relative_to(ROOT)).replace("\\", "/"),
    }
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.output), sort_keys=True))
