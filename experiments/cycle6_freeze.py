"""Create the immutable Cycle 6 precollection correctness/source gate."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def closure():
    from experiments.cycle6_campaign import closure as campaign_closure
    return campaign_closure()


def hashes(files):
    return {path.relative_to(ROOT).as_posix(): sha(path) for path in files}


def run_gate(target):
    target = Path(target).resolve()
    target.mkdir(parents=True, exist_ok=False)
    files = closure()
    before = hashes(files)
    started = time.perf_counter()
    process = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                             cwd=ROOT, capture_output=True)
    elapsed = time.perf_counter() - started
    log = process.stdout + process.stderr
    (target / "unittest.log").write_bytes(log)
    after = hashes(files)
    changed = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
    copied = {}
    for path in files:
        relative = path.relative_to(ROOT)
        destination = target / "source" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copied[relative.as_posix()] = sha(destination)
    decoded = log.decode(errors="replace")
    match = re.search(r"Ran (\d+) tests in ([0-9.]+)s", decoded)
    identity = hashlib.sha256(canonical(copied)).hexdigest()
    passed = process.returncode == 0 and not changed and copied == after and match is not None
    manifest = {
        "schema_version": 1,
        "status": "COMPLETE" if passed else "FAILED",
        "gate_passed": passed,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Cycle 6 precollection runtime correction and protocol freeze; no performance evidence",
        "exit_code": process.returncode,
        "tests_run": int(match.group(1)) if match else None,
        "reported_test_seconds": float(match.group(2)) if match else None,
        "gate_elapsed_seconds": elapsed,
        "source_identity_sha256": identity,
        "source_hashes": copied,
        "source_changed_during_gate": changed,
        "environment": {"python": sys.version, "platform": platform.platform()},
        "artifact_hashes": {"unittest.log": sha(target / "unittest.log")},
        "limitations": ["correctness tests only; no Cycle 6 performance measurement",
                        "deployment manifests are archived but policy enforcement is untested"],
    }
    (target / "manifest.json").write_bytes(canonical(manifest))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    args = parser.parse_args()
    result = run_gate(args.target)
    print(json.dumps({key: result[key] for key in
                      ("status", "tests_run", "reported_test_seconds", "source_identity_sha256")}, indent=2))
    raise SystemExit(0 if result["gate_passed"] else 1)
