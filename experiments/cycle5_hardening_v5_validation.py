"""Freeze the final reviewed Cycle 5 correction closure without performance runs."""
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
import json,math,statistics,sys,tempfile,time
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
    result=execute_shadow(request(config));result['runtime'].update(process_launch_to_entry_ms=0,worker_startup_ms=0,
        worker_metadata_version=1,worker_completed_tasks=1,reset_verified=True);return result
if mode=='timing':
    manager=BranchManager(base);worker=next(iter(manager.workers));result=warm_result(base);result['runtime']['hydrate_ms']=1e308
    with patch.object(worker,'evaluate',return_value=result):outcome=manager._execute(request(base),0)
    returned=manager.available_workers.get_nowait();median=statistics.median([1e308,1e308])
    print(json.dumps({'status':outcome['status'],'worker_returned':returned is worker,'median_finite':math.isfinite(median)}),flush=True)
    manager.available_workers.put(returned);manager.close()
elif mode=='cold_optional':
    config=replace(base,worker_mode='cold',shadow_timeout_s=1);manager=BranchManager(config)
    req=request(config);req['_dispatch_monotonic_s']=time.perf_counter();result=execute_shadow(req);result['runtime']['worker_startup_ms']='bad'
    class Process:
        pid=12345;returncode=0
        def poll(self):return 0
        def communicate(self,body=None,timeout=None):return canonical(result),b''
    with patch('csc.branches.subprocess.Popen',return_value=Process()):outcome=manager._execute(request(config),0)
    print(json.dumps({'status':outcome['status'],'startup':outcome['runtime'].get('worker_startup_ms')}),flush=True);manager.close()
elif mode=='analysis_disposition':
    from experiments import cycle5_async as campaign
    row=dict(mode='warm2',seed=1510,kind='long',condition='long-normal',load='normal',delay_s=0,run_id='last')
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);(root/'preregistration.json').write_text(json.dumps({'registry':[row]}));(root/'execution_status.json').write_text(json.dumps([{'run_id':'last','status':'FAILED'}]))
        reduced={**row,'status':'COMPLETE'}
        with patch.object(campaign,'reduce_run',return_value=reduced):report=campaign.analyze(root)
        print(json.dumps({'failed_count':len(report['failed_or_unattempted_runs']),
                          'run_status':report['runs'][0]['status']}),flush=True)
elif mode=='copy_race':
    from experiments import cycle5_async as campaign
    campaign.ROOT=Path(sys.argv[3])
    required=[*sorted((campaign.ROOT/'csc').glob('*.py')),*sorted((campaign.ROOT/'tests').glob('*.py'))]
    required += [campaign.ROOT/name for name in ('experiments/__init__.py','experiments/cycle5_async.py','experiments/cycle5_pressure.py','experiments/cycle5_loss.py','experiments/replay.py')]
    hashes={str(path.relative_to(campaign.ROOT)).replace('\\','/'):campaign.sha256_file(path) for path in required}
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);gate=root/'gate.json';gate.write_text(json.dumps({'gate_passed':True,'exit_code':0,'source_hashes':hashes,'source_identity_sha256':'fixture'}))
        original=campaign.shutil.copy2
        def changed(source,target,*args,**kwargs):
            value=original(source,target,*args,**kwargs)
            if str(source).replace('\\','/').endswith('experiments/cycle5_pressure.py'):Path(target).write_text('# changed\n')
            return value
        with patch.object(campaign.shutil,'copy2',side_effect=changed):
            try:campaign.prepare(root/'series',gate);accepted=True
            except Exception:accepted=False
        print(json.dumps({'changed_copy_accepted':accepted}),flush=True)
'''


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1]
    directory=root/'results/cycle5-validation/post-review-hardening-20261006-v5'
    if directory.exists(): raise FileExistsError('v5 validation already exists')
    directory.mkdir(parents=True)
    prior=root/'results/cycle5-validation/post-review-hardening-20261006-v4'
    shutil.copytree(prior/'after',directory/'before')
    (directory/'negative_probe.py').write_text(NEGATIVE_PROBE,encoding='utf-8')
    negatives=[]
    for mode in ('timing','cold_optional','analysis_disposition','copy_race'):
        process=subprocess.run([sys.executable,str(directory/'negative_probe.py'),str(directory/'before'),mode,str(root)],capture_output=True,text=True,timeout=30)
        negatives.append(dict(mode=mode,returncode=process.returncode,stdout=process.stdout,stderr=process.stderr))
    closure=[path for folder in ('csc','tests','experiments') for path in sorted((root/folder).glob('*.py'))]
    hashes={}
    for path in closure:
        relative=path.relative_to(root);target=directory/'after'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);hashes[relative.as_posix()]=sha(path)
    command=[sys.executable,'-m','unittest','discover','-s','tests','-q'];started=time.monotonic()
    gate=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=300);elapsed=time.monotonic()-started
    (directory/'unittest.log').write_text(gate.stdout+gate.stderr,encoding='utf-8')
    changed=[name for name,expected in hashes.items() if sha(root/name)!=expected]
    config=asdict(Config(duration_epochs=2,warmup_epochs=0,max_shadow_slots=1,shadow_timeout_s=.15))
    manifest_path=directory/'manifest.json';artifacts={p.relative_to(directory).as_posix():sha(p) for p in sorted(directory.rglob('*')) if p.is_file() and p!=manifest_path}
    csc_hashes={name:value for name,value in hashes.items() if name.startswith('csc/')};complete=gate.returncode==0 and not changed
    manifest=dict(status='COMPLETE' if complete else 'FAILED',gate_passed=complete,scope='final reviewed correctness gate; no performance rerun',
        before_variant='post-review-hardening-20261006-v4',source_hashes=hashes,source_identity_sha256=digest(hashes),
        csc_source_identity_sha256=digest(csc_hashes),config=config,config_hash=digest(config),seed=config['random_seed'],command=command,
        exit_code=gate.returncode,gate_elapsed_s=elapsed,source_changed_during_gate=changed,negative_probes=negatives,artifact_hashes=artifacts,
        analysis_script_identity_sha256=sha(Path(__file__)),environment=dict(python=platform.python_version(),platform=platform.platform(),cpu_count=os.cpu_count()),
        limitations=['Correctness gate only','No performance or empirical claim upgrade','Finite cooperative tests do not prove hostile containment or universal OS cleanup','All earlier evidence immutable'])
    manifest_path.write_bytes(canonical(manifest));print(json.dumps({k:manifest[k] for k in ('status','gate_passed','source_identity_sha256','csc_source_identity_sha256','exit_code','gate_elapsed_s')}))
    if not complete:raise SystemExit(1)
if __name__=='__main__':main()
