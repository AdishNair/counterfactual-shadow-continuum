"""Immutable pre/post-source correctness validation, never a main performance rerun."""
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
import json,sys,threading,subprocess,queue,time
from dataclasses import replace,asdict
sys.path.insert(0, sys.argv[1])
from csc.branches import BranchManager
from csc.contracts import Config,State,StateCaptureEngine
from csc.branches import MultiBranchScheduler
config=Config(duration_epochs=2,warmup_epochs=0,max_shadow_slots=1,shadow_timeout_s=.1)
mode=sys.argv[2]
if mode=='physical':
    manager=BranchManager(config)
    entered,release=threading.Event(),threading.Event()
    def blocked():
        entered.set(); release.wait(5)
    manager.pool.submit(blocked); entered.wait(1)
    for _ in range(1000):
        manager.pool.submit(lambda:None).cancel()
    result={'submitted_cancelled':1000,'configured_cap':config.max_pending_shadow_tasks,
            'physical_queue_depth':manager.pool._work_queue.qsize()}
    release.set();manager.close();print(json.dumps(result),flush=True)
elif mode=='invalid':
    manager=BranchManager(config);manager.config=replace(config,worker_mode='warm')
    anchor=StateCaptureEngine().capture(State(),'negative',0)
    branch=MultiBranchScheduler().plan(anchor,config,'negative',0,'NS_GREEN')[1]
    class Fake:
        def expired(self):return False
        def evaluate(self,request):return {**asdict(branch),'epoch':99,'provenance':'ESTIMATED','runtime':{},'status':'REPORTED'}
        def close(self):self.closed=True
    worker=Fake();worker.closed=False;manager.available_workers.put(worker)
    result=manager._execute({'branch':asdict(branch),'anchor':anchor.envelope()},0)
    returned=manager.available_workers.get_nowait()
    print(json.dumps({'outcome_status':result['status'],'invalid_worker_returned_to_pool':returned is worker,
                      'worker_destroyed':worker.closed}),flush=True)
    manager.close()
elif mode=='blockedpipe':
    from unittest.mock import patch
    from csc.warm import WarmProcess
    original=subprocess.Popen
    childcode="import json,time;print(json.dumps({'status':'READY'}),flush=True);time.sleep(30)"
    def spawn(args,**kwargs):return original([sys.executable,'-c',childcode],**kwargs)
    with patch('csc.warm.subprocess.Popen',side_effect=spawn):worker=WarmProcess(config)
    print(json.dumps({'phase':'before_write','worker_pid':worker.process.pid,'service_timeout_s':config.shadow_timeout_s}),flush=True)
    worker.evaluate({'padding':'x'*(1024*1024)})
    worker.close();print(json.dumps({'phase':'unexpected_write_return'}),flush=True)
'''

REREVIEW_PROBE = r'''
import json,sys,queue,math
from dataclasses import replace,asdict
sys.path.insert(0,sys.argv[1])
from csc.branches import BranchManager,MultiBranchScheduler,execute_shadow
from csc.contracts import Config,State,StateCaptureEngine,canonical
from csc.world import workload
config=Config(duration_epochs=2,warmup_epochs=0,max_shadow_slots=1,shadow_timeout_s=.1)
anchor=StateCaptureEngine().capture(State(),'negative',0)
branch=MultiBranchScheduler().plan(anchor,config,'negative',0,'NS_GREEN')[1]
request={'branch':asdict(branch),'anchor':anchor.envelope(),'config':asdict(config),
         'events':[asdict(e) for e in list(workload(config,'negative'))[:config.horizon_ticks]],'fault':'none'}
result=execute_shadow(request)
mode=sys.argv[2]
manager=BranchManager(config);manager.config=replace(config,worker_mode='warm')
if mode=='runtime':result['runtime']['execution_ms']='bad'
if mode=='mirror':result['trace'][0].update(queue_ns=1.7e308,queue_ew=1.7e308)
if mode=='cleanup':result['epoch']=99
if mode=='enrichment':manager.config=replace(manager.config,max_result_bytes=len(canonical(result))+5)
class Fake:
    def expired(self):return False
    def evaluate(self,request):return result
    def close(self):
        if mode=='cleanup':raise PermissionError('synthetic cleanup denied')
worker=Fake();manager.available_workers.put(worker)
outcome=manager._execute(request,0)
returned=manager.available_workers.get_nowait()
print(json.dumps({'mode':mode,'status':outcome['status'],'worker_returned':returned is worker,
                 'mirror_hypot_finite':math.isfinite(math.hypot(result['trace'][0]['queue_ns'],result['trace'][0]['queue_ew']))}),flush=True)
manager.close()
'''


def negative_probes(directory, variant):
    probe = directory / "negative_probe.py"
    with probe.open("x", encoding="utf-8") as stream:
        stream.write(REREVIEW_PROBE if variant == "v2" else NEGATIVE_PROBE)
    rows = []
    for mode in (("cleanup", "runtime", "mirror", "enrichment") if variant == "v2" else ("physical", "invalid", "blockedpipe")):
        process = subprocess.Popen([sys.executable, str(probe), str(directory / "before"), mode],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        started = time.monotonic()
        timeout = False
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            timeout = True
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
            else:
                process.kill()
            stdout, stderr = process.communicate(timeout=5)
        rows.append({"mode": mode, "watchdog_s": 2, "watchdog_expired": timeout,
                     "elapsed_s": time.monotonic() - started, "returncode": process.returncode,
                     "stdout": stdout, "stderr": stderr})
    (directory / "negative_validation.json").write_bytes(canonical(rows))
    return rows


def main():
    root = Path(__file__).resolve().parents[1]
    variant = "v2" if "--v2" in sys.argv else "v1"
    directory = root / "results/cycle5-validation" / f"post-review-hardening-20261006-{variant}"
    manifest_path = directory / "manifest.json"
    if manifest_path.exists() or (directory / "negative_validation.json").exists():
        raise FileExistsError("validation run already executed")
    before_hashes = {str(p.relative_to(directory / "before")).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted((directory / "before").rglob("*.py"))}
    negatives = negative_probes(directory, variant)
    closure = [p for folder in ("csc", "tests", "experiments") for p in sorted((root / folder).glob("*.py"))]
    after_hashes = {}
    for path in closure:
        relative = path.relative_to(root)
        destination = directory / "after" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        after_hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]
    started = time.monotonic()
    gate = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=300)
    (directory / "unittest.log").write_text(gate.stdout + gate.stderr, encoding="utf-8")
    changed = [name for name, expected in after_hashes.items() if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected]
    config = asdict(Config(duration_epochs=2, warmup_epochs=0, max_shadow_slots=1, shadow_timeout_s=.1))
    artifacts = {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(directory.rglob("*")) if p.is_file() and p != manifest_path}
    manifest = {"status": "COMPLETE" if gate.returncode == 0 and not changed else "FAILED",
                "source_variant": "post-measurement hardening; no main performance rerun",
                "before_source_hashes": before_hashes, "after_source_hashes": after_hashes,
                "source_identity_sha256": digest(after_hashes), "config": config, "config_hash": digest(config),
                "seed": config["random_seed"], "factor_values": {"physical_cancel_attempts": 1000,
                "blocked_request_bytes": 1048576, "capacity": 12, "service_timeout_s": .1},
                "command": command, "exit_code": gate.returncode, "gate_elapsed_s": time.monotonic() - started,
                "source_changed_during_gate": changed, "negative_probes": negatives,
                "artifact_hashes": artifacts,
                "analysis_script_identity_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "environment": {"python": platform.python_version(), "platform": platform.platform(), "cpu_count": os.cpu_count()},
                "limitations": ["Synthetic correctness validation, not production cadence or memory confirmation",
                                "Negative physical probe submits tiny functions without real workload bodies",
                                "Blocked-pipe old-source helper terminated with an external two-second process-tree watchdog",
                                "All previous main/fault/gate artifacts remain immutable"]}
    manifest_path.write_bytes(canonical(manifest))
    print(json.dumps({"path": str(directory), "status": manifest["status"], "gate_exit": gate.returncode,
                      "source_identity_sha256": manifest["source_identity_sha256"], "negative_probes": negatives}))
    if manifest["status"] != "COMPLETE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
