"""Frozen Gate A machinery. Collection is explicit; smoke is disposable evidence only."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shutil
import signal
import subprocess
import sys
import threading
import time

from csc.contracts import Config, canonical, digest
from csc.runner import run
from experiments.cycle6_faults import CASES, optional_fault

ROOT = Path(__file__).resolve().parent.parent
GIB = 1024 ** 3


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def atomic(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(canonical(value))
    temporary.replace(path)


def registry():
    rows = []
    for seed in (26001, 26002, 26003):
        block = []
        for mode in ("k0", "warm1", "warm2"):
            conditions = ("normal", "cpu", "memory", "storage") if mode == "k0" else (
                "normal", "delay120", "delay400", "capacity1", "cpu", "memory", "storage")
            for condition in conditions:
                block.append(dict(kind="factorial", seed=seed, mode=mode, condition=condition,
                                  load=condition if condition in ("cpu", "memory", "storage") else "normal",
                                  delay_s=.12 if condition == "delay120" else .4 if condition == "delay400" else 0.,
                                  fault="control"))
        random.Random(626001 + seed).shuffle(block)
        rows.extend(block)
    for seed in (26101, 26102, 26103):
        rows.extend(dict(kind="storage_fault", seed=seed, mode="warm2", condition=case,
                         load="normal", delay_s=0., fault=case) for case in CASES)
    rows.append(dict(kind="continuous", seed=26201, mode="warm2", condition="normal",
                     load="normal", delay_s=0., fault="control"))
    for index, row in enumerate(rows):
        row.update(order=index, run_id=f"{row['kind']}-{row['seed']}-{row['mode']}-{row['condition']}")
    return rows


def configuration(row, smoke=False):
    k = 0 if row["mode"] == "k0" else int(row["mode"][-1])
    duration, warmup = ((10000, 500) if row["kind"] == "continuous" else
                        (200, 20) if row["kind"] == "storage_fault" else (500, 50))
    if smoke:
        duration, warmup = 8, 1
    return Config(experiment_name="cycle6-disposable-smoke" if smoke else "cycle6-gate-a",
                  random_seed=row["seed"], duration_epochs=duration, warmup_epochs=warmup,
                  horizon_ticks=6, shadow_count=k, mirror_count=int(k > 0),
                  execution_mode="asynchronous", production_period_s=.04,
                  shadow_timeout_s=2., shadow_result_deadline_s=.3,
                  max_shadow_slots=1 if row["condition"] == "capacity1" else 3,
                  max_pending_shadow_tasks=1 if row["condition"] == "capacity1" else 12,
                  max_pending_epochs=16, max_pending_shadow_bytes=16 * 1024 * 1024,
                  shadow_injected_delay_s=row["delay_s"], worker_mode="warm" if k else "cold",
                  worker_max_tasks=100, worker_max_lifetime_s=60., retention_completed_epochs=64,
                  evidence_spool_max_items=256, evidence_spool_max_bytes=16 * 1024 * 1024,
                  evidence_spool_max_attempts=3, evidence_spool_drain_s=1.).validate()


def closure():
    files = list((ROOT / "csc").glob("*.py")) + list((ROOT / "tests").glob("*.py"))
    files += list((ROOT / "experiments").glob("cycle6*.py"))
    files += [ROOT / "experiments/__init__.py", ROOT / "experiments/replay.py",
              ROOT / "research/cycle6/PROTOCOL.md", ROOT / "research/cycle6/PREFLIGHT_REVIEW.md",
              ROOT / "research/cycle6/README.md", ROOT / "research/cycle6/GATE_B_REGISTRY.md",
              ROOT / "Dockerfile"]
    files += [p for p in (ROOT / "deployments").rglob("*") if p.is_file()]
    required = ("cycle6_campaign.py", "cycle6_pressure.py", "cycle6_faults.py",
                "cycle6_analyze.py", "cycle6_verify.py")
    if any(not (ROOT / "experiments" / name).is_file() for name in required):
        raise RuntimeError("execution closure is incomplete")
    if any(not p.is_file() for p in files):
        raise RuntimeError("required closure artifact is absent")
    return sorted(set(files))


def validate_gate(gate_path):
    gate_path = Path(gate_path).resolve()
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if (not isinstance(gate, dict) or gate.get("gate_passed") is not True or
            gate.get("exit_code") != 0 or gate.get("source_changed_during_gate")):
        raise RuntimeError("explicit readiness gate did not pass")
    if digest(gate.get("source_hashes", {})) != gate.get("source_identity_sha256"):
        raise RuntimeError("gate source identity is invalid")
    for path in (ROOT / "csc").glob("*.py"):
        name = path.relative_to(ROOT).as_posix()
        if gate.get("source_hashes", {}).get(name) != sha(path):
            raise RuntimeError("gate/current runtime identity mismatch: " + name)
    name = "research/cycle6/PROTOCOL.md"
    if gate.get("source_hashes", {}).get(name) != sha(ROOT / name):
        raise RuntimeError("gate/current protocol identity mismatch")
    for name, expected in gate.get("artifact_hashes", {}).items():
        if sha(gate_path.parent / name) != expected:
            raise RuntimeError("gate artifact hash mismatch: " + name)
    return gate


def prepare(series, gate_path, smoke=False):
    if gate_path is None:
        raise RuntimeError("explicit --gate manifest is required")
    gate = validate_gate(gate_path)
    files = closure()
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in files}
    for name, value in before.items():
        if gate.get("source_hashes", {}).get(name) != value:
            raise RuntimeError("campaign closure was not validated by the explicit gate: " + name)
    series = Path(series).resolve()
    series.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for path in files:
        name = path.relative_to(ROOT).as_posix()
        target = series / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        hashes[name] = sha(target)
    if hashes != before or any(sha(ROOT / name) != value for name, value in before.items()):
        raise RuntimeError("source changed during freeze")
    gate_dir = series / "source/gates/readiness"
    gate_dir.mkdir(parents=True)
    for name in ("manifest.json", *gate.get("artifact_hashes", {})):
        original = Path(gate_path) if name == "manifest.json" else Path(gate_path).parent / name
        target = gate_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
        hashes[target.relative_to(series / "source").as_posix()] = sha(target)
    rows = registry()
    if smoke:
        # Disposable cases cover runtime, helper lifecycle and optional recovery; never main IDs.
        rows = [dict(rows[0], run_id="smoke-normal", mode="warm2", condition="normal", load="normal", delay_s=0.),
                dict(rows[0], run_id="smoke-storage", mode="warm1", condition="storage", load="storage", delay_s=0.),
                dict(rows[0], run_id="smoke-torn", mode="warm2", condition="torn", load="normal", delay_s=0., fault="torn")]
    configs = {row["run_id"]: asdict(configuration(row, smoke)) for row in rows}
    meta = dict(schema_version=1, status="PREREGISTERED_NOT_STARTED", smoke=smoke,
                timestamp_utc=datetime.now(timezone.utc).isoformat(), registry=rows,
                registry_sha256=digest(rows), configs=configs,
                config_hashes={key: digest(value) for key, value in configs.items()},
                order_seeds=[626001 + seed for seed in (26001, 26002, 26003)],
                source_hashes=hashes, source_identity_sha256=digest(hashes),
                protocol_sha256=hashes["research/cycle6/PROTOCOL.md"],
                correctness_gate_manifest_sha256=sha(gate_path),
                correctness_gate_source_identity_sha256=gate.get("source_identity_sha256"),
                environment=dict(python=sys.version, platform=platform.platform(), logical_cpu_count=os.cpu_count()),
                limitations=["disposable smoke has no performance interpretation"] if smoke else [])
    atomic(series / "preregistration.json", meta)
    atomic(series / "execution_status.json", [dict(run_id=r["run_id"], status="NOT_ATTEMPTED") for r in rows])
    return meta


def verify_archive(series):
    series = Path(series).resolve()
    meta = json.loads((series / "preregistration.json").read_text())
    if digest(meta["registry"]) != meta["registry_sha256"] or digest(meta["source_hashes"]) != meta["source_identity_sha256"]:
        raise RuntimeError("preregistration identity mismatch")
    for name, expected in meta["source_hashes"].items():
        if sha(series / "source" / name) != expected:
            raise RuntimeError("archived source mismatch: " + name)
    for run_id, value in meta["configs"].items():
        if digest(value) != meta["config_hashes"][run_id]:
            raise RuntimeError("frozen config mismatch")
    return meta


def available_memory():
    if os.name == "nt":
        import ctypes
        class Memory(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in ("total_phys", "avail_phys", "total_page",
                                                       "avail_page", "total_virtual", "avail_virtual", "avail_extended")]
        value = Memory()
        value.length = ctypes.sizeof(value)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value)):
            raise OSError("available memory measurement unavailable")
        return value.avail_phys
    fields = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
    return int(fields["MemAvailable"].strip().split()[0]) * 1024


def capacity(path):
    return dict(free_disk_bytes=shutil.disk_usage(path).free, available_memory_bytes=available_memory())


def stop_helper(proc, scratch):
    errors = []
    try:
        (scratch / "stop").write_text("stop")
    except OSError as exc:
        errors.append(repr(exc))
    for action, timeout in ((None, 10), (proc.terminate, 2), (proc.kill, 2)):
        if action:
            try:
                action()
            except OSError as exc:
                errors.append(repr(exc))
        try:
            proc.wait(timeout=timeout)
            return dict(reaped=True, return_code=proc.returncode, errors=errors)
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(repr(exc))
    raise RuntimeError("owned pressure helper cleanup is uncertain: " + repr(errors))


def run_one(series, run_id):
    series = Path(series).resolve()
    meta = verify_archive(series)
    if ROOT != series / "source":
        raise RuntimeError("run-one must execute the archived source closure")
    row = next((r for r in meta["registry"] if r["run_id"] == run_id), None)
    if row is None:
        raise ValueError("unknown frozen run identity")
    control = series / "run_control" / run_id
    control.mkdir(parents=True, exist_ok=False)
    scratch = control / "pressure"
    pressure = None
    succeeded = False
    cleanup = dict(cleanup_confirmed=False)
    try:
        if row["load"] != "normal":
            scratch.mkdir()
            pressure = subprocess.Popen([sys.executable, "-m", "experiments.cycle6_pressure", row["load"], str(scratch)],
                                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            deadline = time.monotonic() + 10
            while not (scratch / "ready.json").is_file():
                if pressure.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("pressure helper readiness failed")
                time.sleep(.01)
        with optional_fault(row["fault"]) as faults:
            try:
                run(Config(**meta["configs"][run_id]), series / "runs", run_id)
                succeeded = True
            finally:
                atomic(control / "faults.json", faults)
    finally:
        try:
            if pressure is not None:
                cleanup["pressure"] = stop_helper(pressure, scratch)
                if cleanup["pressure"]["return_code"] != 0 or not (scratch / "final.json").is_file():
                    raise RuntimeError("pressure duty ended abnormally or has no final telemetry")
            cleanup["cleanup_confirmed"] = succeeded
        finally:
            cleanup["runtime_returned_normally"] = succeeded
            atomic(control / "cleanup.json", cleanup)


def terminate_tree(proc):
    errors = []
    if os.name == "nt":
        try:
            result = subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                                    capture_output=True, timeout=10,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode != 0:
                errors.append("owned tree termination unconfirmed")
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(repr(exc))
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError as exc:
            errors.append(repr(exc))
    try:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(repr(exc))
    return errors


def execute_child(command, cwd, env, timeout, safety_path=None, monitor_path=None):
    kwargs = dict(cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    kwargs.update(creationflags=subprocess.CREATE_NO_WINDOW) if os.name == "nt" else kwargs.update(start_new_session=True)
    proc = subprocess.Popen(command, **kwargs)
    stop = threading.Event()
    danger = []
    samples = []
    def monitor():
        while not stop.wait(.25):
            try:
                sample = dict(monotonic_s=time.monotonic(), **capacity(safety_path))
                samples.append(sample)
                if min(sample["free_disk_bytes"], sample["available_memory_bytes"]) < GIB:
                    danger.append("safety capacity below 1 GiB")
                    danger.extend(terminate_tree(proc))
                    return
            except Exception as exc:
                danger.append("safety measurement failed: " + repr(exc))
                danger.extend(terminate_tree(proc))
                return
    monitor_thread = threading.Thread(target=monitor, daemon=True) if safety_path is not None else None
    if monitor_thread:
        monitor_thread.start()
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        if danger:
            raise RuntimeError("; ".join(danger))
        return subprocess.CompletedProcess(command, proc.returncode, stdout, stderr)
    except BaseException as initiating:
        errors = terminate_tree(proc)
        raise RuntimeError("launcher failure: " + repr(initiating) + "; owned cleanup errors=" + repr(errors)) from initiating
    finally:
        stop.set()
        if monitor_thread:
            monitor_thread.join(timeout=16)
            if monitor_thread.is_alive():
                raise RuntimeError("safety monitor cleanup uncertain")
        if monitor_path:
            atomic(monitor_path, samples)


def inspect_integrity(series, row, meta):
    path = Path(series) / "runs" / row["run_id"]
    manifest = json.loads((path / "manifest.json").read_text())
    if manifest.get("config_hash") != meta["config_hashes"][row["run_id"]]:
        raise RuntimeError("measured configuration mismatch")
    for name, value in manifest["source_hashes"].items():
        if meta["source_hashes"].get(name) != value:
            raise RuntimeError("measured runtime identity mismatch")
    summary = json.loads((path / "summary.json").read_text())
    if summary.get("unauthorized_production_mutations_from_shadow", 0):
        raise RuntimeError("authority corruption")
    journal = path / "epoch_journal.jsonl"
    epochs = set()
    with journal.open() as stream:
        for line in stream:
            epochs.add(json.loads(line)["epoch"])
    if epochs != set(range(meta["configs"][row["run_id"]]["duration_epochs"])):
        raise RuntimeError("production journal is incomplete")
    return summary


def execute(series, gate_path, smoke=False):
    series = Path(series).resolve()
    if not smoke:
        series.parent.mkdir(parents=True, exist_ok=True)
    meta = prepare(series, gate_path, smoke)
    statuses = [dict(run_id=r["run_id"], status="NOT_ATTEMPTED") for r in meta["registry"]]
    paired = {}
    env = dict(os.environ, PYTHONPATH=str(series / "source"), PYTHONDONTWRITEBYTECODE="1")
    for index, row in enumerate(meta["registry"]):
        started = time.monotonic()
        status = statuses[index]
        status.update(status="RUNNING", started_utc=datetime.now(timezone.utc).isoformat())
        atomic(series / "execution_status.json", statuses)
        try:
            if row["kind"] == "continuous":
                measured = capacity(series)
                status["long_run_preflight"] = measured
                if min(measured.values()) < 2 * GIB:
                    raise RuntimeError("continuous-run preflight requires 2 GiB free disk and available memory")
            verify_archive(series)
            timeout = 300 + 2 * meta["configs"][row["run_id"]]["duration_epochs"]
            result = execute_child([sys.executable, "-m", "experiments.cycle6_campaign", "run-one",
                                    str(series), "--run-id", row["run_id"]], series / "source", env, timeout,
                                   series if row["kind"] == "continuous" else None,
                                   series / (row["run_id"] + "-watchdog.json") if row["kind"] == "continuous" else None)
            status.update(return_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
            cleanup = json.loads((series / "run_control" / row["run_id"] / "cleanup.json").read_text())
            if not isinstance(cleanup, dict) or cleanup.get("cleanup_confirmed") is not True:
                raise RuntimeError("owned runtime cleanup unconfirmed")
            if result.returncode:
                raise RuntimeError("run failed; artifact usability/ownership cannot authorize another run")
            summary = inspect_integrity(series, row, meta)
            pair = (summary["production_semantic_sha256"], summary["workload_sha256"])
            if row["seed"] in paired and paired[row["seed"]] != pair:
                raise RuntimeError("paired production/workload trajectory mismatch")
            paired[row["seed"]] = pair
            status["status"] = "COMPLETE"
        except Exception as exc:
            status.update(status="FAILED", error=repr(exc), campaign_stop="integrity, artifact usability or ownership uncertainty")
            break
        finally:
            status["elapsed_s"] = time.monotonic() - started
            atomic(series / "execution_status.json", statuses)
        print(f"{index + 1}/{len(statuses)} {row['run_id']}", flush=True)
    meta.update(status="COMPLETE" if all(s["status"] == "COMPLETE" for s in statuses) else "HAS_FAILED_OR_UNATTEMPTED_RUNS",
                ended_utc=datetime.now(timezone.utc).isoformat())
    meta["artifact_hashes"] = {p.relative_to(series).as_posix(): sha(p) for p in sorted(series.rglob("*"))
                              if p.is_file() and p.name != "series_manifest.json" and "__pycache__" not in p.parts}
    atomic(series / "series_manifest.json", meta)
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "execute", "smoke", "run-one"))
    parser.add_argument("series")
    parser.add_argument("--gate")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    if args.action == "run-one":
        run_one(args.series, args.run_id)
    elif args.action == "prepare":
        prepare(args.series, args.gate)
    else:
        result = execute(args.series, args.gate, args.action == "smoke")
        raise SystemExit(0 if result["status"] == "COMPLETE" else 1)
