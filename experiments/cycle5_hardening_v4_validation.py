"""Freeze the final bounded post-review corrections; never rerun main performance."""
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
import json,math,subprocess,sys,tempfile,time
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,sys.argv[1])
from csc.branches import BranchManager,execute_shadow
from csc.contracts import Config,canonical
from tests.test_cycle5_runtime import request

mode=sys.argv[2]
base=Config(duration_epochs=12,warmup_epochs=0,horizon_ticks=4,execution_mode='asynchronous',
            worker_mode='warm',max_shadow_slots=1,shadow_timeout_s=.15)
def warm_result(config):
    result=execute_shadow(request(config))
    result['runtime'].update(process_launch_to_entry_ms=0,worker_startup_ms=0,
                             worker_metadata_version=1,worker_completed_tasks=1,reset_verified=True)
    return result

if mode=='cpu_aggregate':
    manager=BranchManager(base);worker=next(iter(manager.workers));result=warm_result(base)
    result['runtime']['cpu_ms']=1e308
    with patch.object(worker,'evaluate',return_value=result):outcome=manager._execute(request(base),0)
    returned=manager.available_workers.get_nowait()
    print(json.dumps({'status':outcome['status'],'worker_returned':returned is worker,
                      'two_value_sum_finite':math.isfinite(result['runtime']['cpu_ms']+result['runtime']['cpu_ms'])}),flush=True)
    manager.available_workers.put(returned);manager.close()
elif mode=='cold_validation':
    config=replace(base,worker_mode='cold',shadow_timeout_s=1);manager=BranchManager(config)
    req=request(config);req['_dispatch_monotonic_s']=time.perf_counter();result=execute_shadow(req);result['runtime']['cpu_ms']='bad'
    class Process:
        pid=12345;returncode=0
        def poll(self):return 0
        def communicate(self,body=None,timeout=None):return canonical(result),b''
    with patch('csc.branches.subprocess.Popen',return_value=Process()):outcome=manager._execute(request(config),0)
    print(json.dumps({'status':outcome['status'],'cpu_ms':outcome['runtime'].get('cpu_ms')}),flush=True);manager.close()
elif mode=='final_cleanup_status':
    from experiments import cycle5_async as campaign
    row=dict(mode='warm1',seed=1501,kind='factorial',condition='normal',load='normal',delay_s=0,run_id='last')
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);ownership=root/'ownership/last';ownership.mkdir(parents=True);(ownership/'cleanup.json').write_text('null')
        completed=subprocess.CompletedProcess([],0,'','')
        with patch.object(campaign,'prepare',return_value={'registry':[row]}),patch.object(campaign,'execute_child',return_value=(completed,False)),patch.object(campaign,'analyze',return_value={}):campaign.execute(root)
        status=json.loads((root/'execution_status.json').read_text())[0]
        manifest=json.loads((root/'series_manifest.json').read_text())
        print(json.dumps({'row_status':status['status'],'campaign_status':manifest['status'],'unsafe':status.get('unsafe_to_continue')}),flush=True)
elif mode=='gate_format':
    from experiments import cycle5_async as campaign
    with tempfile.TemporaryDirectory() as td:
        try:campaign.prepare(Path(td)/'series',Path(sys.argv[3]));accepted=True;error=None
        except Exception as exc:accepted=False;error=type(exc).__name__+':'+str(exc)
        print(json.dumps({'accepted':accepted,'error':error}),flush=True)
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "results/cycle5-validation/post-review-hardening-20261006-v4"
    if directory.exists():
        raise FileExistsError("v4 validation directory already exists")
    directory.mkdir(parents=True)
    prior = root / "results/cycle5-validation/post-review-hardening-20261006-v3"
    shutil.copytree(prior / "after", directory / "before")
    (directory / "negative_probe.py").write_text(NEGATIVE_PROBE, encoding="utf-8")
    negatives = []
    for mode in ("cpu_aggregate", "cold_validation", "final_cleanup_status", "gate_format"):
        command = [sys.executable, str(directory / "negative_probe.py"), str(directory / "before"), mode,
                   str(prior / "manifest.json")]
        process = subprocess.run(command, capture_output=True, text=True, timeout=15)
        negatives.append({"mode": mode, "returncode": process.returncode,
                          "stdout": process.stdout, "stderr": process.stderr})

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
    complete = gate.returncode == 0 and not changed
    manifest = {
        "status": "COMPLETE" if complete else "FAILED", "gate_passed": complete,
        "scope": "final post-measurement correctness gate; no performance rerun",
        "before_variant": "post-review-hardening-20261006-v3",
        "source_hashes": source_hashes, "source_identity_sha256": digest(source_hashes),
        "csc_source_identity_sha256": digest(csc_hashes),
        "config": config, "config_hash": digest(config), "seed": config["random_seed"],
        "command": command, "exit_code": gate.returncode, "gate_elapsed_s": elapsed,
        "source_changed_during_gate": changed, "negative_probes": negatives,
        "artifact_hashes": artifacts, "analysis_script_identity_sha256": sha(Path(__file__)),
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "cpu_count": os.cpu_count()},
        "limitations": ["Correctness gate only", "No main performance rerun or empirical claim upgrade",
                        "Finite first-party schedules do not prove hostile containment or universal OS cleanup",
                        "All prior evidence remains immutable"]}
    manifest_path.write_bytes(canonical(manifest))
    print(json.dumps({key: manifest[key] for key in
                      ("status", "gate_passed", "source_identity_sha256", "csc_source_identity_sha256",
                       "exit_code", "gate_elapsed_s")}))
    if not complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
