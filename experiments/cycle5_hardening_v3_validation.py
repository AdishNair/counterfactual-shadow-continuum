"""Freeze and validate the third post-review correction without rerunning performance."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

from csc.contracts import Config, canonical, digest


NEGATIVE_PROBE = r'''
import json,math,subprocess,sys,time
from dataclasses import replace
from unittest.mock import patch
sys.path.insert(0,sys.argv[1])
from csc.branches import BranchManager,execute_shadow
from csc.compare import utility
from csc.contracts import Config
from tests.test_cycle5_runtime import request

mode=sys.argv[2]
base=Config(duration_epochs=12,warmup_epochs=0,horizon_ticks=4,execution_mode='asynchronous',
            worker_mode='warm',max_shadow_slots=1,shadow_timeout_s=.15)

def warm_result(config):
    result=execute_shadow(request(config))
    result['runtime'].update(process_launch_to_entry_ms=0,worker_startup_ms=0,
                             worker_metadata_version=1,worker_completed_tasks=1,reset_verified=True)
    return result

if mode in ('runtime_cpu','utility_difference'):
    config=replace(base,queue_weight=1e306) if mode=='utility_difference' else base
    manager=BranchManager(config)
    worker=next(iter(manager.workers))
    result=warm_result(config)
    if mode=='runtime_cpu':result['runtime']['cpu_ms']='bad'
    else:result['metrics']['mean_queue']=-100
    with patch.object(worker,'evaluate',return_value=result):outcome=manager._execute(request(config),0)
    returned=manager.available_workers.get_nowait()
    payload={'mode':mode,'status':outcome['status'],'worker_returned':returned is worker}
    if mode=='utility_difference':
        left=utility({'mean_queue':-100,'waiting_vehicle_ticks':0,'phase_switches':0},config)
        right=utility({'mean_queue':100,'waiting_vehicle_ticks':0,'phase_switches':0},config)
        payload.update(left=left,right=right,difference_finite=math.isfinite(left-right))
    print(json.dumps(payload),flush=True)
    manager.available_workers.put(returned);manager.close()
elif mode=='warm_lease_shutdown':
    manager=BranchManager(base)
    manager.available_workers.get_nowait()
    future=manager.pool.submit(manager._execute,request(base),0)
    while not future.running():time.sleep(.001)
    manager.close()
    print(json.dumps({'mode':mode,'settled':future.done()}),flush=True)
elif mode=='cold_capacity':
    config=replace(base,worker_mode='cold')
    manager=BranchManager(config)
    processes=[]
    class Process:
        pid=0;returncode=None
        def __init__(self):self.terminated=False
        def poll(self):return 0 if self.terminated else None
        def kill(self):raise PermissionError('denied')
        def communicate(self,body=None,timeout=None):
            if self.terminated:return b'',b''
            raise subprocess.TimeoutExpired('fake',timeout)
    def spawn(*args,**kwargs):
        process=Process();processes.append(process);return process
    with patch('csc.branches.subprocess.Popen',side_effect=spawn):
        first=manager._execute(request(config),0)
        second=manager._execute(request(config,1),0)
    print(json.dumps({'mode':mode,'first':first['status'],'second':second['status'],
                      'spawn_count':len(processes),'owned_count':len(manager.cold_processes)}),flush=True)
    for process in processes:process.terminated=True
    manager.close()
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_probe(directory, mode):
    process = subprocess.Popen([sys.executable, str(directory / "negative_probe.py"),
                                str(directory / "before"), mode],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    started = time.monotonic()
    expired = False
    try:
        stdout, stderr = process.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        expired = True
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, timeout=10)
        else:
            process.kill()
        stdout, stderr = process.communicate(timeout=5)
    return {"mode": mode, "watchdog_s": 3, "watchdog_expired": expired,
            "elapsed_s": time.monotonic() - started, "returncode": process.returncode,
            "stdout": stdout, "stderr": stderr}


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "results/cycle5-validation/post-review-hardening-20261006-v3"
    if directory.exists():
        raise FileExistsError("v3 validation directory already exists")
    directory.mkdir(parents=True)
    shutil.copytree(root / "results/cycle5-validation/post-review-hardening-20261006-v2/after",
                    directory / "before")
    (directory / "negative_probe.py").write_text(NEGATIVE_PROBE, encoding="utf-8")
    negatives = [run_probe(directory, mode) for mode in
                 ("runtime_cpu", "utility_difference", "warm_lease_shutdown", "cold_capacity")]

    closure = [path for folder in ("csc", "tests", "experiments")
               for path in sorted((root / folder).glob("*.py"))]
    source_hashes = {}
    for path in closure:
        relative = path.relative_to(root)
        target = directory / "after" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        source_hashes[relative.as_posix()] = sha(path)

    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]
    started = time.monotonic()
    gate = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=300)
    elapsed = time.monotonic() - started
    (directory / "unittest.log").write_text(gate.stdout + gate.stderr, encoding="utf-8")
    changed = [name for name, expected in source_hashes.items() if sha(root / name) != expected]
    config = asdict(Config(duration_epochs=2, warmup_epochs=0, max_shadow_slots=1, shadow_timeout_s=.15))
    manifest_path = directory / "manifest.json"
    artifacts = {path.relative_to(directory).as_posix(): sha(path)
                 for path in sorted(directory.rglob("*")) if path.is_file() and path != manifest_path}
    csc_hashes = {name: value for name, value in source_hashes.items() if name.startswith("csc/")}
    manifest = {
        "status": "COMPLETE" if gate.returncode == 0 and not changed else "FAILED",
        "scope": "post-measurement v3 correctness only; no main performance rerun",
        "before_variant": "post-review-hardening-20261006-v2",
        "source_hashes": source_hashes,
        "source_identity_sha256": digest(source_hashes),
        "csc_source_identity_sha256": digest(csc_hashes),
        "config": config, "config_hash": digest(config), "seed": config["random_seed"],
        "command": command, "exit_code": gate.returncode, "gate_elapsed_s": elapsed,
        "source_changed_during_gate": changed, "negative_probes": negatives,
        "artifact_hashes": artifacts,
        "analysis_script_identity_sha256": sha(Path(__file__)),
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "cpu_count": os.cpu_count()},
        "limitations": ["Correctness/fault validation only", "No cadence, yield, memory, or storage claim upgraded",
                        "Watchdog termination is bounded local evidence, not hostile-process containment",
                        "All earlier gates, reviews, and experiment archives remain immutable"]}
    manifest_path.write_bytes(canonical(manifest))
    print(json.dumps({key: manifest[key] for key in
                      ("status", "source_identity_sha256", "csc_source_identity_sha256", "exit_code", "gate_elapsed_s")}))
    if manifest["status"] != "COMPLETE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
