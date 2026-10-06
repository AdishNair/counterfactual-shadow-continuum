"""Preregistered finite continuous systems pilot: immutable runs and deterministic analysis."""
import argparse
from collections import Counter, defaultdict
import csv
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
import statistics
import subprocess
import sys
import time

from csc.contracts import Config, canonical, digest
from csc.runner import distribution as runtime_distribution, run, summarize
from experiments.replay import read_lines, sha256_file

ROOT = Path(__file__).resolve().parent.parent
MODES = ("k0", "cold1", "cold2", "warm1", "warm2")
CELLS = (("normal", "normal", 0.), ("moderate", "normal", .12), ("severe", "normal", .6),
         ("cpu", "cpu", 0.), ("memory", "memory", 0.), ("storage", "storage", 0.))


def distribution(values):
    values=[v for v in values if v is not None]
    return dict(runtime_distribution(values), min=min(values) if values else None, max=max(values) if values else None)


def registry():
    rows = []
    for seed in (1501, 1502, 1503):
        block = [dict(kind="factorial", seed=seed, mode=mode, condition=name, load=load, delay_s=delay)
                 for mode in MODES for name, load, delay in CELLS
                 if mode != "k0" or name not in ("moderate", "severe")]
        random.Random(51501+seed).shuffle(block)
        rows.extend(block)
    rows += [dict(kind="long", seed=1510, mode="warm2", condition="long-normal", load="normal", delay_s=0.),
             dict(kind="long", seed=1511, mode="warm2", condition="long-saturation", load="normal", delay_s=.6)]
    for index, row in enumerate(rows):
        row.update(order=index, run_id=f"{row['kind']}-{row['seed']}-{row['mode']}-{row['condition']}")
    return rows


def configuration(row):
    k = 0 if row["mode"] == "k0" else int(row["mode"][-1])
    duration = 3000 if row["condition"] == "long-normal" else 1000 if row["kind"] == "long" else 200
    return Config(experiment_name="cycle5-systems-pilot", random_seed=row["seed"], duration_epochs=duration,
                  warmup_epochs=20, horizon_ticks=6, shadow_count=k, mirror_count=int(k > 0),
                  max_shadow_slots=1 if row["condition"] == "long-saturation" else 3,
                  execution_mode="asynchronous", production_period_s=.04, shadow_timeout_s=2.,
                  shadow_result_deadline_s=.3, max_pending_shadow_tasks=12, max_pending_epochs=16,
                  shadow_injected_delay_s=row["delay_s"], worker_mode="warm" if row["mode"].startswith("warm") else "cold",
                  worker_max_tasks=100, worker_max_lifetime_s=60., retention_completed_epochs=64)


def stop_pressure(pressure, scratch):
    """Cooperative stop first; bounded terminate/kill even if stop storage fails."""
    try:
        (scratch / "stop").write_text("stop", encoding="utf-8")
    except OSError:
        pass
    for action,timeout in ((None,10),(pressure.terminate,2),(pressure.kill,2)):
        if action:
            try:action()
            except OSError:pass  # Still attempt remaining owned cleanup and reap.
        try:
            pressure.wait(timeout=timeout)
            return
        except (subprocess.TimeoutExpired,OSError):pass
    raise RuntimeError('pressure ownership cleanup is unconfirmed')


def run_one(series, row):
    series = Path(series).resolve()
    pressure = None
    scratch = series / "pressure" / row["run_id"]
    ownership=series/'ownership'/row['run_id']
    ownership.mkdir(parents=True,exist_ok=False)
    cleanup_confirmed=False
    run_succeeded=False
    try:
        if row["load"] != "normal":
            scratch.mkdir(parents=True, exist_ok=False)
            pressure = subprocess.Popen([sys.executable, "-m", "experiments.cycle5_pressure", row["load"], str(scratch)],
                                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            deadline = time.perf_counter() + 10
            while not (scratch / "ready.json").exists():
                if pressure.poll() is not None or time.perf_counter() >= deadline:
                    raise RuntimeError("pressure helper did not become ready")
                time.sleep(.01)
        run(configuration(row), series / "runs", row["run_id"])
        run_succeeded=True
    finally:
        try:
            if pressure:stop_pressure(pressure, scratch)
            cleanup_confirmed=run_succeeded  # On runtime exception its own cleanup is uncertain.
        finally:
            temporary=ownership/'cleanup.json.tmp'
            temporary.write_bytes(canonical(dict(cleanup_confirmed=cleanup_confirmed,run_succeeded=run_succeeded,
                                                 pressure_pid=pressure.pid if pressure else None,
                                                 scope='normal return and pressure reap; failures conservatively uncertain')))
            temporary.replace(ownership/'cleanup.json')


def campaign_watchdog_s(row):
    # Generous execution control, not a production/evidence success target.
    return 300 + 2 * configuration(row).duration_epochs


def cleanup_owned_child(proc):
    """Attempt all owned cleanup steps; retain uncertainty rather than skip reaping."""
    errors=[]
    if os.name=='nt':
        try:
            cleanup=subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,timeout=10)
            if cleanup.returncode!=0:errors.append('owned-tree termination unconfirmed')
        except (OSError,subprocess.TimeoutExpired) as exc:errors.append('tree:'+repr(exc))
    else:
        try:os.killpg(proc.pid,signal.SIGKILL)
        except OSError as exc:errors.append('group:'+repr(exc))
    try:
        if proc.poll() is None:proc.kill()
    except OSError as exc:errors.append('kill:'+repr(exc))
    stdout,stderr='', ''
    try:
        stdout,stderr=proc.communicate(timeout=5)
    except Exception as exc:
        # A broken communication channel does not prevent a separate process reap.
        errors.append('communication:'+repr(exc))
        try:proc.kill()
        except OSError as kill_error:errors.append('kill:'+repr(kill_error))
        try:proc.wait(timeout=2)
        except (OSError,subprocess.TimeoutExpired) as reap_error:errors.append('reap:'+repr(reap_error))
    return stdout,stderr,errors


def execute_child(command, cwd, env, timeout):
    """Bound launcher wait and cleanup owned tree on every post-spawn failure."""
    kwargs=dict(cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if os.name=='nt':kwargs['creationflags']=subprocess.CREATE_NO_WINDOW
    else:kwargs['start_new_session']=True
    proc=subprocess.Popen(command,**kwargs)
    try:
        stdout,stderr=proc.communicate(timeout=timeout)
        return subprocess.CompletedProcess(command,proc.returncode,stdout,stderr),False
    except BaseException as initiating_error:
        stdout,stderr,cleanup_errors=cleanup_owned_child(proc)
        if isinstance(initiating_error,subprocess.TimeoutExpired) and not cleanup_errors:
            return subprocess.CompletedProcess(command,proc.returncode,stdout,stderr),True
        message='launcher error: '+repr(initiating_error)+'; cleanup_confirmed='+str(not bool(cleanup_errors))+'; cleanup_errors='+repr(cleanup_errors)+'; campaign must stop'
        if not isinstance(initiating_error,Exception):raise
        raise RuntimeError(message) from initiating_error


def prepare(series, gate_path=None):
    series = Path(series).resolve()
    if gate_path is None:
        raise RuntimeError("Fresh campaign requires an explicit compatible --gate manifest; historical gates do not authorize current source")
    gate_path=Path(gate_path).resolve()
    gate=json.loads(gate_path.read_text())
    gate_passed = isinstance(gate,dict) and (gate.get('gate_passed') is True or gate.get('status') == 'COMPLETE')
    if not gate_passed or gate.get('exit_code')!=0:
        raise RuntimeError('Warm correctness gate did not pass')
    required={str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'csc').glob('*.py')}
    required.update(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'tests').glob('*.py'))
    required.update(('experiments/__init__.py', 'experiments/cycle5_async.py',
                     'experiments/cycle5_pressure.py', 'experiments/cycle5_loss.py',
                     'experiments/replay.py'))
    if not required.issubset(gate.get('source_hashes',{})):
        raise RuntimeError('Readiness gate lacks full current CSC/campaign/test source closure')
    for name in required:
        if sha256_file(ROOT/name)!=gate['source_hashes'][name]:
            raise RuntimeError('Current source differs from explicit readiness gate: '+name)
    for name in ('research/evidence/cycle5/cycle5_protocol.md','research/archive/cycle5/protocol_review/cycle5_protocol_review.md','research/archive/cycle5/protocol_review/cycle5_protocol_rereview.md','research/evidence/cycle5/warm_worker_correctness.md'):
        if not (ROOT/name).is_file():raise RuntimeError('Missing precollection evidence: '+name)
    series.mkdir(parents=True, exist_ok=False)
    sources = sorted([str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "csc").glob("*.py")])
    sources += ["experiments/__init__.py", "experiments/cycle5_async.py", "experiments/cycle5_loss.py",
                "experiments/cycle5_pressure.py", "experiments/replay.py", "research/evidence/cycle5/cycle5_protocol.md"]
    sources += [str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "tests").glob("*.py")]
    sources += ["tests/test_cycle5_runtime.py", "research/evidence/cycle5/warm_worker_correctness.md", "research/archive/cycle5/protocol_review/cycle5_protocol_review.md",
                "research/archive/cycle5/protocol_review/cycle5_protocol_rereview.md", "research/evidence/cycle5/cycle5_failure_recovery.md",
                "research/tables/cycle5_warm_gate.json"]
    hashes = {}
    for name in sorted(set(sources)):
        if not (ROOT / name).is_file():
            continue
        target = series / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
        hashes[name] = sha256_file(target)
    copied_mismatches = [name for name in required if hashes.get(name) != gate["source_hashes"].get(name)]
    if copied_mismatches:
        raise RuntimeError("Copied execution source differs from readiness gate: " + ",".join(sorted(copied_mismatches)))
    gate_target=series/'source/gates/readiness_manifest.json'
    gate_target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(gate_path,gate_target)
    hashes['gates/readiness_manifest.json']=sha256_file(gate_target)
    if (gate_path.parent/'unittest.log').is_file():
        shutil.copy2(gate_path.parent/'unittest.log',gate_target.parent/'unittest.log')
        hashes['gates/unittest.log']=sha256_file(gate_target.parent/'unittest.log')
    meta = dict(status="PREREGISTERED_NOT_STARTED", started_utc=datetime.now(timezone.utc).isoformat(),
                registry=registry(), order_seeds=[53002,53003,53004], source_hashes=hashes, protocol_sha256=hashes["research/evidence/cycle5/cycle5_protocol.md"],
                correctness_gate_source_identity_sha256=gate.get('source_identity_sha256',gate.get('source_identity')),correctness_gate_manifest_sha256=sha256_file(gate_path),
                analysis_script_sha256=hashes["experiments/cycle5_async.py"],
                stress_mechanism=dict(cpu="one sustained integer-LCG process, no affinity; achieved CPU seconds logged",
                                      memory="64MiB resident bytearray, touch each4KiB page every loop plus5ms sleep; bounded additional resident working set",
                                      storage="one4MiB same-volume scratch file rewritten with Python flush and5ms sleep; no fsync, no physical disk saturation claim"),
                environment=dict(python=sys.version, platform=platform.platform(), processor=platform.processor(),
                                 logical_cpu_count=os.cpu_count(), timing_clock=time.get_clock_info("perf_counter")._asdict() if hasattr(time.get_clock_info("perf_counter"), "_asdict") else str(time.get_clock_info("perf_counter"))))
    meta["configs"] = {r["run_id"]: asdict(configuration(r)) for r in meta["registry"]}
    (series / "preregistration.json").write_bytes(canonical(meta))
    return meta


def execute(series, gate_path=None):
    series = Path(series).resolve()
    meta = prepare(series, gate_path)
    env = dict(os.environ, PYTHONPATH=str(series / "source"))
    statuses=[]
    for index, row in enumerate(meta["registry"]):
        started=time.perf_counter()
        try:
            proc,watchdog_expired=execute_child([sys.executable, "-m", "experiments.cycle5_async", "run-one", str(series), "--row", canonical(row).decode()],
                                              cwd=series / "source",env=env,timeout=campaign_watchdog_s(row))
        except (OSError,RuntimeError) as exc:
            proc=subprocess.CompletedProcess([],128,'',str(exc))
            watchdog_expired=True  # Conservative control abort; never another condition.
        status=dict(run_id=row['run_id'],return_code=proc.returncode,duration_s=time.perf_counter()-started,
                    status="COMPLETE" if proc.returncode==0 and not watchdog_expired else "FAILED",stderr=proc.stderr,
                    watchdog_s=campaign_watchdog_s(row),watchdog_expired=watchdog_expired)
        statuses.append(status)
        (series/"execution_status.json").write_bytes(canonical(statuses))
        ownership=series/'ownership'/row['run_id']/'cleanup.json'
        try:
            confirmation=json.loads(ownership.read_text())
            cleanup_confirmed=isinstance(confirmation,dict) and confirmation.get('cleanup_confirmed') is True
        except (OSError,ValueError):cleanup_confirmed=False
        status['cleanup_confirmed']=cleanup_confirmed
        unsafe='campaign watchdog expired; owned coordinator tree terminated' if watchdog_expired else None
        if proc.returncode!=0 or not cleanup_confirmed:
            unsafe='run failed or ownership cleanup unconfirmed; application final marker cannot authorize continuation'
        result_path=series/'runs'/row['run_id']
        if (result_path/'summary.json').exists() and json.loads((result_path/'summary.json').read_text()).get('unauthorized_production_mutations_from_shadow',0):
            unsafe='authority breach'
        if (result_path/'resource_metrics.jsonl').exists():
            for sample in read_lines(result_path/'resource_metrics.jsonl'):
                if sample.get('active_shadow_tasks',0)>12 or sample.get('pending_epochs',0)>16 or sample.get('retained_completed_epochs',0)>64:
                    unsafe='runtime structural bound exceeded';break
        if unsafe:
            status['status']='FAILED'
            status['unsafe_to_continue']=unsafe
            statuses.extend(dict(run_id=r['run_id'],status='NOT_ATTEMPTED',return_code=None) for r in meta['registry'][index+1:])
            (series/'execution_status.json').write_bytes(canonical(statuses))
            break
        print(f"{index+1}/{len(meta['registry'])} {row['run_id']}", flush=True)
    report = analyze(series)
    (series / "analysis.json").write_bytes(canonical(report))
    meta.update(status="COMPLETE" if all(s['status']=='COMPLETE' for s in statuses) else "HAS_FAILED_OR_UNATTEMPTED_RUNS", ended_utc=datetime.now(timezone.utc).isoformat())
    meta["artifact_hashes"] = {str(p.relative_to(series)).replace("\\", "/"): sha256_file(p)
                              for p in sorted(series.rglob("*")) if p.is_file() and p.name != "series_manifest.json" and "__pycache__" not in p.parts}
    (series / "series_manifest.json").write_bytes(canonical(meta))
    return report


def slope(rows, name, axis="epoch"):
    points = [(r[axis], r[name]) for r in rows if type(r.get(name)) in (int, float) and type(r.get(axis)) in (int,float)]
    if len(points) < 2:
        return None
    xbar, ybar = statistics.mean(x for x, _ in points), statistics.mean(y for _, y in points)
    denominator = sum((x-xbar)**2 for x, _ in points)
    return sum((x-xbar)*(y-ybar) for x, y in points) / denominator if denominator else None


def reduce_run(path, row):
    if not (path/'summary.json').exists():
        config=configuration(row);records=[];errors=[]
        if (path/'cfr.jsonl').exists():
            for line in (path/'cfr.jsonl').read_text(encoding='utf-8').splitlines():
                try:records.append(json.loads(line))
                except ValueError:errors.append('truncated_or_invalid_cfr_line')
        measured=[r for r in records if r['epoch']>=config.warmup_epochs]
        known_complete=sum(r.get('evidence_completeness')=='COMPLETE_COMPARISON' for r in measured)
        expected=config.duration_epochs-config.warmup_epochs
        return dict(**row,status='FAILED_OR_NOT_ATTEMPTED',observed_epochs=len(records),measured_epochs=len(measured),
                    missing_production_epochs=config.duration_epochs-len(records),full_requested_cohort_epochs=expected,
                    known_complete_fraction_of_requested_cohort=known_complete/expected,
                    observed_prefix_complete_fraction=known_complete/len(measured) if measured else None,
                    production_failures=1,parse_errors=errors,error='Missing complete summary; prefix is not a full-run performance sample')
    manifest = json.loads((path / "manifest.json").read_text())
    config = Config(**manifest["config"])
    resources = list(read_lines(path / "resource_metrics.jsonl"))[config.warmup_epochs:]
    records = list(read_lines(path / "cfr.jsonl"))[config.warmup_epochs:]
    lifecycle = list(read_lines(path / "lifecycle.jsonl"))
    branches = [b for r in records for b in r["branches"][1:]]
    completed = [r for r in records if r.get("evidence_completeness") == "COMPLETE_COMPARISON"]
    accepted = [b for b in branches if b.get("status") == "REPORTED" and b.get("synchronization", {}).get("comparable")]
    partial = [r for r in records if r.get("record_status") == "PARTIAL"]
    intervals = [r["production_interval_ms"] for r in resources if r.get("production_interval_ms") is not None]
    wall = sum(intervals)/1000
    runtimes = [e["worker_runtime"] for e in lifecycle if e.get("epoch", -1) >= config.warmup_epochs and e.get("worker_runtime")]
    worker_cpu = sum(r.get("cpu_ms", 0) for r in runtimes)/1000
    coordinator_cpu = sum(r.get("coordinator_cpu_ms", 0) for r in resources)/1000
    statuses = Counter(b["status"] for b in branches)
    reasons = Counter(flag for b in branches if b["status"] != "REPORTED" for flag in b.get("failure_flags", []))
    production_finished=next((e.get('monotonic_s') for e in lifecycle if e['status']=='PRODUCTION_FINISHED'),None)
    production_span_start=resources[0].get('epoch_started_monotonic_s') if resources else None
    if production_finished is not None and production_span_start is not None:
        wall=production_finished-production_span_start
    finalization_times={e['epoch']:e['monotonic_s'] for e in lifecycle if e['status']=='FINALIZED'}
    completed_during_production=sum(production_finished is not None and finalization_times.get(r['epoch'],float('inf'))<=production_finished for r in completed)
    peraction={}
    accepted_ids={b['branch_id'] for b in accepted}
    for action in ("NS_GREEN","EW_GREEN","BALANCED"):
        for role in ("MIRROR","SHADOW"):
            planned=[b for b in branches if (b['action'],b['role'])==(action,role)]
            peraction[role+':'+action]=dict(requested=len(planned),admitted=sum(b['status']!='DROPPED' for b in planned),accepted=sum(b['branch_id'] in accepted_ids for b in planned),
                                         dropped=sum(b['status']=='DROPPED' for b in planned),expired=sum(b['status']=='EXPIRED' for b in planned))
    result = dict(**row, status="COMPLETE" if manifest['status']=='COMPLETE' else 'FAILED_WITH_SUMMARY', measured_epochs=len(records), production_interval_ms=distribution(intervals),
                  production_decision_ms=distribution([r["production_decision_ms"] for r in resources]),
                  production_path_ms=distribution([r["production_path_ms"] for r in resources]),
                  complete_fraction=len(completed)/len(records) if config.shadow_count else None, partial_fraction=len(partial)/len(records) if config.shadow_count else None,
                  usable_full_comparison_fraction=len(completed)/len(records) if config.shadow_count else None,
                  mirror_plus_any_alternative_fraction=sum(any(b.get("status")=="REPORTED" and b["role"]=="MIRROR" for b in r["branches"][1:]) and any(b.get("status")=="REPORTED" and b["role"]=="SHADOW" for b in r["branches"][1:]) for r in records)/len(records) if config.shadow_count else None,
                  no_accepted_evidence_fraction=sum(not any(b.get("status") == "REPORTED" for b in r["branches"][1:]) for r in records)/len(records),
                  requested_branches=len(branches), admitted_branches=sum(e["status"] == "QUEUED" and e.get("epoch", -1) >= config.warmup_epochs for e in lifecycle),
                  accepted_branches=len(accepted), branch_completion_fraction=len(accepted)/len(branches) if branches else None,
                  mirror_completion_fraction=sum(b["role"] == "MIRROR" for b in accepted)/sum(b["role"] == "MIRROR" for b in branches) if branches else None,
                  alternative_completion_fraction=sum(b["role"] == "SHADOW" for b in accepted)/sum(b["role"] == "SHADOW" for b in branches) if config.shadow_count else None,
                  branch_status_counts=dict(statuses), branch_loss_reasons=dict(reasons),
                  requested_k=distribution([r.get("requested_k", config.shadow_count) for r in records]),
                  admitted_k=distribution([r.get("admitted_k", 0) for r in records]),
                  completed_k=distribution([r.get("completed_k", 0) for r in records]),
                  complete_evidence_age_ms=distribution([r["comparison_completion_ms"] for r in completed]),
                  branch_acceptance_age_ms=distribution([e.get("branch_completion_ms") for e in lifecycle if e.get("epoch", -1) >= config.warmup_epochs and e["status"] == "COMPLETED"]),
                  late_successful_results=sum(e["status"] == "LATE" and e.get("worker_runtime") is not None and e.get("epoch", -1) >= config.warmup_epochs for e in lifecycle),
                  cadence_target_overruns=sum(i > 40 for i in intervals),
                  cumulative_schedule_drift_ms=sum(i-40 for i in intervals),
                  epoch_execution_over_40ms=sum(r["epoch_ms"] > 40 for r in resources),
                  missed_epoch_count=config.duration_epochs-len(list(read_lines(path / "cfr.jsonl"))),
                  measured_production_span_s=wall,
                  complete_records_per_s=completed_during_production/wall if wall and production_finished is not None else None,
                  complete_records_during_production=completed_during_production if production_finished is not None else None,
                  complete_records_during_production_per_s=completed_during_production/wall if wall and production_finished is not None else None,
                  eventual_cohort_complete_records_per_paced_s=len(completed)/wall if wall else None,
                  eventual_cohort_complete_records_per_observation_s=len(completed)/(max([production_finished or 0]+[finalization_times[r['epoch']] for r in completed])-production_span_start) if production_span_start is not None else None,
                  complete_records_during_drain=len(completed)-completed_during_production if production_finished is not None else None,
                  per_action_role_counts=peraction,
                  coordinator_cpu_s=coordinator_cpu, accepted_or_late_worker_cpu_s=worker_cpu,
                  complete_records_per_cpu_s=None,
                  serialized_bytes_per_complete_record=sum(len(canonical(r))+1 for r in completed)/len(completed) if completed else None,
                  observed_transport_bytes_per_complete_record=sum(r.get("request_bytes",0)+r.get("response_bytes",0) for r in runtimes)/len(completed) if completed else None,
                  complete_records_per_worker_slot=len(completed)/config.max_shadow_slots if config.shadow_count else None,
                  artifact_bytes=sum(p.stat().st_size for p in path.iterdir() if p.is_file()),
                  max_active=max(r.get("active_shadow_tasks",0) for r in resources), max_queued=max(r.get("queued_shadow_tasks",0) for r in resources),
                  max_pending=max(r.get("pending_epochs",0) for r in resources))
    for name in ("coordinator_rss_bytes", "coordinator_python_current_bytes", "coordinator_python_peak_bytes",
                 "worker_rss_bytes", "worker_count", "retained_completed_epochs", "duplicate_cache_size",
                 "worker_lifecycle_hot_count", "coordinator_handles", "artifact_storage_bytes", "result_ledger_size", "synchronization_hot_count", "replay_metadata_hot_count", "resource_history_size", "worker_launches", "worker_recycles", "worker_failures"):
        values = [r[name] for r in resources if type(r.get(name)) in (int, float)]
        result[name] = dict(min=min(values), max=max(values), end=values[-1], slope_per_epoch=slope(resources,name),
                            second_half_slope_per_epoch=slope(resources[len(resources)//2:],name),
                            slope_per_second=slope(resources,name,'epoch_started_monotonic_s'),
                            first_quarter_distribution=distribution(values[:max(1,len(values)//4)]),last_quarter_distribution=distribution(values[-max(1,len(values)//4):]),
                            first_quarter_mean=statistics.mean(values[:max(1,len(values)//4)]),
                            last_quarter_mean=statistics.mean(values[-max(1,len(values)//4):])) if values else None
    for name in ("queue_wait_ms","worker_startup_ms","process_launch_to_entry_ms","hydrate_ms","execution_ms","transport_overhead_ms","dispatch_roundtrip_ms"):
        result[name]=distribution([r.get(name) for r in runtimes])
    result["result_store_ms"]=distribution([e.get("result_store_ms") for e in lifecycle if e.get("epoch",-1)>=config.warmup_epochs and e["status"]=="FINALIZED"])
    acceptance_by_epoch=defaultdict(list)
    for e in lifecycle:
        if e.get("epoch",-1)>=config.warmup_epochs and e["status"]=="COMPLETED" and e.get("branch_completion_ms") is not None:
            acceptance_by_epoch[e["epoch"]].append(e["branch_completion_ms"])
    result["comparison_wait_after_last_accept_ms"]=distribution([r["comparison_completion_ms"]-max(acceptance_by_epoch[r["epoch"]]) for r in completed if acceptance_by_epoch[r["epoch"]]])
    result["evidence_time_blocks"]=[dict(first_epoch=chunk[0]["epoch"],last_epoch=chunk[-1]["epoch"],
        complete_fraction=sum(r.get("evidence_completeness")=="COMPLETE_COMPARISON" for r in chunk)/len(chunk),
        expired_fraction=sum(b["status"]=="EXPIRED" for r in chunk for b in r["branches"][1:])/sum(len(r["branches"])-1 for r in chunk) if config.shadow_count else None,
        dropped_fraction=sum(b["status"]=="DROPPED" for r in chunk for b in r["branches"][1:])/sum(len(r["branches"])-1 for r in chunk) if config.shadow_count else None)
        for chunk in [records[i:i+100] for i in range(0,len(records),100)]]
    summary = json.loads((path / "summary.json").read_text())
    result.update(production_hash=summary["production_semantic_sha256"], workload_hash=summary["workload_sha256"],
                  production_failures=int(manifest["status"] != "COMPLETE"), unauthorized_mutations=summary["unauthorized_production_mutations_from_shadow"])
    for name in ("worker_pool_initialization_s","worker_ready_startup_ms","offline_summary_ms","offline_summary_rss_bytes","offline_summary_python_current_bytes","offline_summary_python_peak_bytes","shutdown_after_production_ms"):
        result[name]=summary.get(name)
    result['production_path_cpu_ms']=distribution([r.get('production_path_cpu_ms') for r in resources])
    launches=result.get('worker_launches')
    result['complete_records_per_observed_worker_process']=len(completed)/launches['end'] if launches and launches['end'] else None
    pressure = path.parent.parent / "pressure" / row["run_id"] / "final.json"
    result["pressure_validation"] = json.loads(pressure.read_text()) if pressure.exists() else None
    return result


def analyze(series):
    series = Path(series)
    meta = json.loads((series / "preregistration.json").read_text())
    runs = [reduce_run(series / "runs" / r["run_id"], r) for r in meta["registry"]]
    execution_path = series / "execution_status.json"
    execution = json.loads(execution_path.read_text()) if execution_path.exists() else []
    execution_by_run = {row["run_id"]: row for row in execution}
    for result in runs:
        disposition = execution_by_run.get(result["run_id"])
        if disposition is not None and disposition.get("status") != "COMPLETE":
            result["artifact_status"] = result.get("status")
            result["status"] = "FAILED_CONTROL_OR_CLEANUP"
            result["execution_disposition"] = disposition
    valid=[r for r in runs if r.get('status')=='COMPLETE']
    failed=[r for r in runs if r.get('status')!='COMPLETE']
    groups = []
    for mode in MODES:
        for condition, load, delay in CELLS:
            scheduled=[r for r in runs if r["kind"]=="factorial" and (r["mode"],r["condition"])==(mode,condition)]
            rows = [r for r in valid if r["kind"] == "factorial" and (r["mode"],r["condition"]) == (mode,condition)]
            if not rows:
                continue
            normal = {r["seed"]:r for r in valid if (r["mode"],r["condition"]) == (mode,"normal")}
            k0 = {r["seed"]:r for r in valid if r["mode"] == "k0" and r["load"] == load}
            groups.append(dict(mode=mode,condition=condition,load=load,delay_s=delay,seeds=len(rows),scheduled_runs=len(scheduled),failed_runs=len(scheduled)-len(rows),
                failure_note="Timing distributions condition on completed runs; failed prefixes remain in failure table, not substituted" if len(scheduled)!=len(rows) else None,
                cadence_ms=distribution([r["production_interval_ms"]["median"] for r in rows]),
                complete_fraction=distribution([r["complete_fraction"] for r in rows]),
                partial_fraction=distribution([r["partial_fraction"] for r in rows]),
                coverage_by_seed={str(r["seed"]):r["complete_fraction"] for r in rows},
                paired_cadence_effect_vs_same_mode_normal_ms=[r["production_interval_ms"]["median"]-normal[r["seed"]]["production_interval_ms"]["median"] if r["seed"] in normal else None for r in rows],
                paired_cadence_effect_vs_same_load_k0_ms=[r["production_interval_ms"]["median"]-k0[r["seed"]]["production_interval_ms"]["median"] if r["seed"] in k0 else None for r in rows],
                expired=sum(r["branch_status_counts"].get("EXPIRED",0) for r in rows),
                dropped=sum(r["branch_status_counts"].get("DROPPED",0) for r in rows),
                complete_records_per_s=distribution([r["complete_records_per_s"] for r in rows])))
    effects = []
    for k in (1,2):
        for condition, _, _ in CELLS:
            for seed in (1501,1502,1503):
                cold = next((r for r in valid if (r["mode"],r["condition"],r["seed"]) == (f"cold{k}",condition,seed)),None)
                warm = next((r for r in valid if (r["mode"],r["condition"],r["seed"]) == (f"warm{k}",condition,seed)),None)
                if cold is None or warm is None:
                    effects.append(dict(k=k,condition=condition,seed=seed,status='UNAVAILABLE_FAILED_PAIR',complete_fraction_gain=None,cadence_change_ms=None))
                    continue
                effects.append(dict(k=k,condition=condition,seed=seed,complete_fraction_gain=warm["complete_fraction"]-cold["complete_fraction"],
                                    cadence_change_ms=warm["production_interval_ms"]["median"]-cold["production_interval_ms"]["median"]))
    return dict(runs=runs,groups=groups,warm_cold_paired_effects=effects,failed_or_unattempted_runs=failed,
                experimental_unit="3 independent paired seed/run units per cell; epochs repeated observations; no confirmatory inference",
                quantiles="linear-interpolated per-run p50/p95/p99; 180 measured epochs gives <2 observations in p99 tail; tail descriptive",
                coverage_labels="zero=0, low=(0,1/3), moderate=[1/3,2/3), high=[2/3,1]; descriptive thirds, not success thresholds",
                specification="10,000 consecutive epochs at >=90% completeness not evaluated by this 200-epoch factorial / 3000-epoch longest pilot",
                cpu_efficiency_limit="Total CPU efficiency unavailable (null): observed coordinator + accepted/late worker CPU excludes killed/expired workers without output; Windows CPU quantization. Components retained separately.")


def verify(series, output):
    series, output = Path(series).resolve(), Path(output).resolve()
    if ROOT != series / "source":
        env = dict(os.environ,PYTHONPATH=str(series / "source"))
        subprocess.run([sys.executable,"-m","experiments.cycle5_async","verify",str(series),"--output",str(output)],
                       cwd=series / "source",env=env,check=True)
        return json.loads(output.read_text())
    meta = json.loads((series / "series_manifest.json").read_text())
    failures, checked = [], 0
    if meta["registry"] != registry(): failures.append("registry")
    if len({r["run_id"] for r in meta["registry"]}) != len(meta["registry"]): failures.append("duplicate_run_id")
    if {r["seed"] for r in meta["registry"] if r["kind"]=="factorial"} & {r["seed"] for r in meta["registry"] if r["kind"]=="long"}: failures.append("unintended_seed_overlap")
    if {p.name for p in (series / "runs").iterdir()} != {r["run_id"] for r in registry()}: failures.append("run_set")
    for name,h in meta["artifact_hashes"].items():
        if not (series/name).exists() or sha256_file(series/name) != h: failures.append("artifact:"+name)
    from csc.branches import execute_shadow
    from csc.contracts import Anchor, Event
    from csc.world import ProductionWorld
    for row in registry():
        path = series / "runs" / row["run_id"]
        if not (path/'summary.json').exists():
            failures.append('failed_or_unattempted_run:'+row['run_id'])
            continue
        manifest = json.loads((path/"manifest.json").read_text())
        if manifest["config"] != asdict(configuration(row)): failures.append("config:"+row["run_id"])
        if manifest["config_hash"] != digest(manifest["config"]): failures.append("config_hash:"+row["run_id"])
        for name,h in manifest["source_hashes"].items():
            if sha256_file(ROOT/name) != h: failures.append("run_source:"+row["run_id"]+":"+name)
        anchors = {a["snapshot_id"]:Anchor.from_envelope(a) for a in read_lines(path/"anchors.jsonl")}
        events = defaultdict(list)
        for e in read_lines(path/"events.jsonl"): events[e["epoch"]].append(e)
        journal = {e["epoch"]:e for e in read_lines(path/"epoch_journal.jsonl")}
        if len(journal)!=sum(1 for _ in read_lines(path/"epoch_journal.jsonl")): failures.append("duplicate_commit:"+row["run_id"])
        records = list(read_lines(path/"cfr.jsonl"))
        if [r["epoch"] for r in records] != list(range(configuration(row).duration_epochs)): failures.append("epochs:"+row["run_id"])
        for record in records:
            anchor = anchors[record["anchor_hash"]]
            entry = journal.pop(record["epoch"],None)
            if not entry or entry["production"]["trace"] != record["branches"][0]["trace"]: failures.append("journal:"+row["run_id"])
            for branch in record["branches"]:
                if branch["status"] != "REPORTED" or not branch.get("synchronization",{}).get("comparable"): continue
                config = configuration(row)
                # Delays/load are wall-time-only injection and excluded from semantic replay.
                config.shadow_injected_delay_s=0
                config.shadow_load="normal"
                config.failure_scenario="none"
                if branch["role"] == "PRODUCTION":
                    cap=object(); world=ProductionWorld(anchor.hydrate(),cap,config)
                    world.apply_plan(branch["action"],cap,"replay")
                    trace=[world.step(Event(**e),tick) for tick,e in enumerate(events[record["epoch"]])]
                else:
                    request=dict(anchor=anchor.envelope(),config=asdict(config),events=events[record["epoch"]],
                                 branch={k:branch[k] for k in ("branch_id","experiment_id","epoch","role","action","parent_snapshot_id","start_sequence","end_sequence")})
                    trace=execute_shadow(request)["trace"]
                if trace != branch["trace"]: failures.append("replay:"+row["run_id"]+":"+branch["branch_id"])
                checked+=1
            if record["missing"] and record.get("regret_raw") is not None: failures.append("incomplete_regret:"+row["run_id"])
            if any(b["provenance"]!="ESTIMATED" for b in record["branches"][1:]):failures.append("shadow_provenance:"+row["run_id"])
        if journal: failures.append("unfinalized:"+row["run_id"])
        resources=list(read_lines(path/"resource_metrics.jsonl"))
        if any(r.get("active_shadow_tasks",0)>12 or r.get("pending_epochs",0)>16 or r.get("retained_completed_epochs",0)>64 for r in resources): failures.append("capacity:"+row["run_id"])
        # Existing summarize is the exact recorded reducer, post-run only.
        summary=json.loads((path/"summary.json").read_text())
        prod_digest, workload_digest=hashlib.sha256(),hashlib.sha256()
        for r in records:
            b=r["branches"][0]
            prod_digest.update(canonical(dict(action=b["action"],trace=b["trace"],state=b["final_state"])))
        for e in read_lines(path/"events.jsonl"):
            e.pop("experiment_id");workload_digest.update(canonical(e))
        if prod_digest.hexdigest()!=summary["production_semantic_sha256"]:failures.append("production_hash_regeneration:"+row["run_id"])
        if workload_digest.hexdigest()!=summary["workload_sha256"]:failures.append("workload_hash_regeneration:"+row["run_id"])
        regenerated=summarize(records[20:],resources[20:])
        if any(summary.get(k)!=v for k,v in regenerated.items()): failures.append("summary:"+row["run_id"])
    analysis=analyze(series)
    if analysis != json.loads((series/"analysis.json").read_text()): failures.append("analysis_regeneration")
    for seed in (1501,1502,1503):
        rows=[r for r in analysis["runs"] if r["seed"]==seed and r.get('status')=='COMPLETE']
        if len({r["production_hash"] for r in rows})!=1 or len({r["workload_hash"] for r in rows})!=1: failures.append("paired_hash:"+str(seed))
    for r in analysis["runs"]:
        if r.get('status')!='COMPLETE':continue
        p=r["pressure_validation"]
        if r["load"]!="normal" and not p:failures.append("absent_pressure:"+r["run_id"])
        elif p and ((r["load"]=="cpu" and p["operations"]<=0) or (r["load"]=="memory" and (p["allocated_bytes"]!=64*1024*1024 or p["memory_touch_rounds"]<=0)) or (r["load"]=="storage" and (p["written_bytes"]<=0 or p["storage_peak_file_bytes"]>4*1024*1024))):failures.append("ineffective_pressure:"+r["run_id"])
    result=dict(status="VERIFIED" if not failures else "FAILED",failures=failures,runs_verified=len(registry()),branches_replayed=checked,
                source_archive_hashes_verified=len(meta["source_hashes"]),replay_source="ARCHIVED_SOURCE",replay_delay="wall-time injection removed; semantic model/config preserved")
    output.write_bytes(canonical(result))
    return result


def render(series, directory):
    report=analyze(series); directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    for key in ("runs","groups","warm_cold_paired_effects"):
        (directory/f"cycle5_{key}.json").write_bytes(canonical(report[key]))
    (directory/'cycle5_failed_or_unattempted_runs.json').write_bytes(canonical(report['failed_or_unattempted_runs']))
    if report['failed_or_unattempted_runs']:
        (directory/'cycle5_failure_notice.md').write_text('Study has failed/unattempted units. Full dispositions and observed-prefix/full-cohort counts are in cycle5_failed_or_unattempted_runs.json. Timing distributions for surviving runs cannot establish full-study performance. No failed unit was retried or substituted.\n',encoding='utf-8')
        return
    lines=["# Cycle 5 deterministic systems tables","",f"Source: `{Path(series)/'analysis.json'}`; independent unit: seed/run. Three seeds/cell. Full distributions and paired effects are retained in JSON.","",
           "| Mode | Condition | Cadence median ms | Complete fraction median [min,max] | Partial fraction | Expired | Dropped |","|---|---|---:|---|---:|---:|---:|"]
    for g in report["groups"]:
        d=g["complete_fraction"]
        coverage=f"{d['median']:.3f} [{d['min']:.3f},{d['max']:.3f}]" if d['median'] is not None else 'unavailable'
        partial=f"{g['partial_fraction']['median']:.3f}" if g['partial_fraction']['median'] is not None else 'unavailable'
        lines.append(f"| {g['mode']} | {g['condition']} | {g['cadence_ms']['median']:.3f} | {coverage} | {partial} | {g['expired']} | {g['dropped']} |")
    lines += ["",report["specification"],"",report["quantiles"],"",report["cpu_efficiency_limit"]]
    (directory/"cycle5_tables.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    fields=["seed","mode","condition","kind","run_id","measured_epochs","complete_fraction","partial_fraction","requested_branches","admitted_branches","accepted_branches","complete_records_per_s","max_active","max_queued","max_pending"]
    with (directory/"cycle5_runs.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fields);writer.writeheader()
        for r in report["runs"]:writer.writerow({k:r[k] for k in fields})
    with (directory/"cycle5_epochs.csv").open("w",newline="",encoding="utf-8") as stream:
        fields=["run_id","epoch","requested_k","admitted_k","completed_k","evidence_completeness","comparison_completion_ms","drop_reasons","resource_state"]
        writer=csv.DictWriter(stream,fields);writer.writeheader()
        for row in registry():
            for r in read_lines(Path(series)/"runs"/row["run_id"]/"cfr.jsonl"):
                record={k:r.get(k) for k in fields};record["run_id"]=row["run_id"]
                for k in ("drop_reasons","resource_state"):record[k]=json.dumps(record[k],sort_keys=True)
                writer.writerow(record)


def figures(series,directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    report=analyze(series);directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    if report['failed_or_unattempted_runs']:raise RuntimeError('Do not render complete-study figures with failed/unattempted units')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for mode in MODES[1:]:
        groups=[next(g for g in report["groups"] if (g["mode"],g["condition"])==(mode,c)) for c in ("normal","moderate","severe")]
        axes[0].plot([0,120,600],[g["cadence_ms"]["median"] for g in groups],marker="o",label=mode)
        axes[1].plot([0,120,600],[g["complete_fraction"]["median"] for g in groups],marker="o",label=mode)
        for delay,group in zip((0,120,600),groups):
            axes[1].scatter([delay]*len(group['coverage_by_seed']),list(group['coverage_by_seed'].values()),alpha=.45,s=16)
    axes[0].set_ylabel("Production interval, median of run medians (ms)");axes[1].set_ylabel("Complete comparable epoch fraction")
    for ax in axes:ax.set_xlabel("Injected service delay (ms)");ax.legend();ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(directory/"cadence_completeness.png",dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    labels=[c[0] for c in CELLS]
    for k,ax in zip((1,2),axes):
        for mode,color,offset in ((f'cold{k}','tab:blue',-.18),(f'warm{k}','tab:orange',.18)):
            groups=[next(g for g in report['groups'] if (g['mode'],g['condition'])==(mode,c)) for c in labels]
            ax.bar([x+offset for x in range(len(labels))],[g['complete_fraction']['median'] for g in groups],width=.34,color=color,alpha=.35,label=mode)
            for x,g in enumerate(groups):
                vals=[g['coverage_by_seed'][str(s)] for s in (1501,1502,1503)]
                ax.scatter([x+offset+d for d in (-.06,0,.06)],vals,s=24,color=color)
        ax.set_xticks(range(len(labels)),labels,rotation=25);ax.set_ylim(0,1.05);ax.set_title(f'K={k}, mirror excluded');ax.set_ylabel('Complete requested-epoch evidence fraction');ax.legend();ax.grid(axis='y',alpha=.2)
    fig.tight_layout();fig.savefig(directory/'cold_warm_all_seed_coverage.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for mode in MODES:
        groups=[next(g for g in report["groups"] if (g["mode"],g["condition"])==(mode,c)) for c in ("normal","cpu","memory","storage")]
        axes[0].plot(range(4),[g["cadence_ms"]["median"] for g in groups],marker="o",label=mode)
        axes[1].plot(range(4),[g["complete_fraction"]["median"] for g in groups],marker="o",label=mode)
    axes[0].set_ylabel("Production interval (ms)");axes[1].set_ylabel("Complete epoch fraction")
    for ax in axes:ax.set_xticks(range(4),["normal","CPU 1proc","memory64MB","storage4MB"]);ax.legend();ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(directory/"resource_tradeoffs.png",dpi=180);plt.close(fig)
    for row in [r for r in registry() if r["kind"]=="long"]:
        metrics=list(read_lines(Path(series)/"runs"/row["run_id"]/"resource_metrics.jsonl"))
        fig,axes=plt.subplots(2,2,figsize=(11,7));xs=[r["epoch"] for r in metrics]
        for field in ("coordinator_rss_bytes","coordinator_python_current_bytes"):
            vals=[r.get(field) for r in metrics]
            if any(v is not None for v in vals):axes[0,0].plot(xs,[v/1024/1024 if v is not None else float('nan') for v in vals],label=field)
        for field in ("pending_epochs","retained_completed_epochs","active_shadow_tasks","queued_shadow_tasks"):
            axes[0,1].plot(xs,[r.get(field,0) for r in metrics],label=field)
        records=list(read_lines(Path(series)/"runs"/row["run_id"]/"cfr.jsonl"))
        axes[1,0].plot([r["epoch"] for r in records],[r.get("admitted_k",0) for r in records],label="admitted K",alpha=.6)
        axes[1,0].plot([r["epoch"] for r in records],[r.get("completed_k",0) for r in records],label="completed K",alpha=.6)
        ages=[r["comparison_completion_ms"] for r in records if r["evidence_completeness"]=="COMPLETE_COMPARISON"]
        if ages:axes[1,1].hist(ages,bins=30)
        axes[0,0].set_ylabel("MiB");axes[0,1].set_ylabel("Hot state entries / tasks");axes[1,0].set_ylabel("K requested=2");axes[1,1].set_xlabel("Complete comparison age ms")
        for ax in (axes[0,0],axes[0,1],axes[1,0]):ax.set_xlabel("Epoch");ax.legend();ax.grid(alpha=.2)
        fig.suptitle(row["condition"]);fig.tight_layout();fig.savefig(directory/(row["condition"]+".png"),dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for mode in MODES[1:]:
        runs=[r for r in report['runs'] if r['mode']==mode and r['condition']=='normal']
        ages=[]
        for row in runs:
            ages += [r['comparison_completion_ms'] for r in read_lines(Path(series)/'runs'/row['run_id']/'cfr.jsonl') if r['epoch']>=20 and r['evidence_completeness']=='COMPLETE_COMPARISON']
        if ages:
            ages=sorted(ages);axes[0].plot(ages,[(i+1)/len(ages) for i in range(len(ages))],label=mode)
        axes[1].scatter([int(mode[-1])]*len(runs),[r['max_queued'] for r in runs],label=mode)
    axes[0].set_xlabel('Complete comparison age from commit (ms)');axes[0].set_ylabel('Descriptive pooled empirical CDF');axes[1].set_xlabel('Distinct requested alternatives K');axes[1].set_ylabel('Maximum queued tasks per run')
    for ax in axes:ax.legend();ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(directory/'evidence_age_and_k_queue.png',dpi=180);plt.close(fig)
    (directory/"metadata.json").write_bytes(canonical(dict(source=str(Path(series)/"analysis.json"),analysis_script_sha256=sha256_file(__file__),matplotlib_version=matplotlib.__version__,unit="seed/run medians; long-run epoch time series")))


def document(series,output):
    report=analyze(series)
    if report['failed_or_unattempted_runs']:
        Path(output).write_text('# Cycle 5 incomplete systems study\n\n**Status:** Failed/unattempted scheduled units retained; no full-study performance conclusion.\n\nEvidence and deterministic failure dispositions: `research/tables/cycle5_failed_or_unattempted_runs.json`; complete attempt status: immutable series `execution_status.json`. Observed-prefix outcomes cannot substitute for full-run outcomes. No retries under existing identities. Source fixes require a new immutable series.\n',encoding='utf-8')
        return
    lines=["# Cycle 5 continuous asynchronous systems results","", "**Status:** Locally tested finite preregistered systems pilot. Derived deterministically from archived raw artifacts; deployment validation is absent.","",
           "**Question:** Can a bounded local asynchronous runtime maintain production cadence while generating comparable counterfactual evidence during continuous operation?","",
           f"**Evidence:** `{Path(series)/'analysis.json'}`; source/config/protocol/environment archives and per-run artifacts accompany the series. Machine tables: `research/tables/cycle5_runs.json`, `cycle5_groups.json`, `cycle5_warm_cold_paired_effects.json`, `cycle5_runs.csv`, `cycle5_epochs.csv`. See `cycle5_verification.json` for deterministic replay/provenance verdict.","",
           "**Method:** 84 factorial runs, 28 cells, three paired seeds; 200 epochs and20excluded warmups. Main runs execute sequentially in independently started coordinators using archived source. All nonzero modes retain the same300ms evidence deadline,40ms pacing target,3slots,12active-task capacity,mirror-first admission. Long runs separately test3000epochs normal and1000epochs one-slot severe delay. Quantities are descriptive, with three independent seed/run units; epochs are repeated dependent observations.","",
           "## Production and evidence by condition","",
           "| Mode | Condition | Cadence p50 ms, median over seeds | Run p95 ms, median over seeds | Run p99 ms, median over seeds | Complete fraction median [range] | Partial fraction median | Complete evidence/sec median | Expired branches | Dropped branches |",
           "|---|---|---:|---:|---:|---|---:|---:|---:|---:|"]
    for g in report["groups"]:
        rows=[r for r in report["runs"] if (r["mode"],r["condition"])==(g["mode"],g["condition"])]
        d=g["complete_fraction"]
        coverage=f"{d['median']:.3f} [{d['min']:.3f},{d['max']:.3f}]" if d['median'] is not None else 'unavailable'
        partial=f"{g['partial_fraction']['median']:.3f}" if g['partial_fraction']['median'] is not None else 'unavailable'
        lines.append(f"| {g['mode']} | {g['condition']} | {g['cadence_ms']['median']:.3f} | {statistics.median(r['production_interval_ms']['p95'] for r in rows):.3f} | {statistics.median(r['production_interval_ms']['p99'] for r in rows):.3f} | {coverage} | {partial} | {g['complete_records_per_s']['median']:.3f} | {g['expired']} | {g['dropped']} |")
    paired=[dict(seed=s,production_hashes=len({r['production_hash'] for r in report['runs'] if r['seed']==s}),workload_hashes=len({r['workload_hash'] for r in report['runs'] if r['seed']==s})) for s in (1501,1502,1503)]
    lines += ["",f"Production paired hash cardinalities: `{paired}` (one per seed is agreement within this authored software environment). Missing production epochs: {sum(r['missed_epoch_count'] for r in report['runs'])}; failed manifests: {sum(r['production_failures'] for r in report['runs'])}; observed unauthorized mutations: {sum(r['unauthorized_mutations'] for r in report['runs'])}.","",
              "Strict40ms start-interval overruns and cumulative schedule drift are recorded separately in machine tables. The pacing loop sleeps relative to each preceding start, so drift can accumulate despite stable medians. No externally required hard deadline or equivalence margin was predeclared; interval jitter is not a guarantee of missed real-world actuation.","",
              "## Cold versus warm evidence yield","",
              "| K | Condition | Paired complete-fraction gains (three seeds) | Paired cadence changes ms (three seeds) |","|---:|---|---|---|"]
    for k in (1,2):
        for condition,_,_ in CELLS:
            es=[e for e in report['warm_cold_paired_effects'] if e['k']==k and e['condition']==condition]
            lines.append(f"| {k} | {condition} | {[round(e['complete_fraction_gain'],6) for e in es]} | {[round(e['cadence_change_ms'],6) for e in es]} |")
    lines += ["","Comparison age from production commit includes dispatch, queueing, worker execution, coordinator polling and ordered epoch finalization. Worker-stage distributions and comparison waiting after last accepted branch are retained per run. Accepted branch completion is distinguished from complete requested mirror-plus-alternative epoch evidence and late physical worker returns. K0 has no counterfactual denominator.","",
              "## Continuous hot state and archival growth","",
              "| Run | Measured epochs | Complete fraction | Cadence median ms | RSS min/end/max MiB | RSS second-half slope KiB/epoch | Python current second-half slope bytes/epoch | Max pending | Max completed retained | Max duplicate cache | Max queue | Archive end MiB |",
              "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in [r for r in report['runs'] if r['kind']=='long']:
        rss=r['coordinator_rss_bytes'];py=r['coordinator_python_current_bytes'];archive=r['artifact_storage_bytes']
        rssstr=f"{rss['min']/2**20:.3f}/{rss['end']/2**20:.3f}/{rss['max']/2**20:.3f}" if rss else "unavailable"
        lines.append(f"| {r['condition']} | {r['measured_epochs']} | {r['complete_fraction']:.3f} | {r['production_interval_ms']['median']:.3f} | {rssstr} | {rss['second_half_slope_per_epoch']/1024 if rss else None} | {py['second_half_slope_per_epoch'] if py else None} | {r['max_pending']} | {r['retained_completed_epochs']['max']} | {r['duplicate_cache_size']['max']} | {r['max_queued']} | {archive['end']/2**20 if archive else None} |")
    lines += ["", "Full-state OLS slopes per epoch/per second, second-half slopes, first/last-quarter means, worker counts/RSS, handles and every100epoch evidence/loss fraction remain in JSON. RSS is instantaneous working set on Windows, not an exclusive allocation ownership measure. Python current and peak are distinct. Online hot history is count bounded; append-only archived research evidence grows. Full-run exact summary generation occurs after production stops and loads the run history; its RSS/time are a separate offline limitation, not a continuously retained production structure.","",
              "## Resource pressure and graceful degradation","",
              "| Mode | Load | Paired cadence change from normal ms (three seeds) | Requested K median | Admitted K median across runs | Completed K median across runs | Median complete age ms |",
              "|---|---|---|---:|---:|---:|---:|"]
    for g in report['groups']:
        rows=[r for r in report['runs'] if (r['mode'],r['condition'])==(g['mode'],g['condition'])]
        ages=[r['complete_evidence_age_ms']['median'] for r in rows if r['complete_evidence_age_ms']['median'] is not None]
        lines.append(f"| {g['mode']} | {g['condition']} | {[round(e,6) for e in g['paired_cadence_effect_vs_same_mode_normal_ms']]} | {rows[0]['requested_k']['median']} | {statistics.median(r['admitted_k']['median'] for r in rows)} | {statistics.median(r['completed_k']['median'] for r in rows)} | {statistics.median(ages) if ages else 'unavailable'} |")
    pressure=[r['pressure_validation'] for r in report['runs'] if r['pressure_validation']]
    for kind in ('cpu','memory','storage'):
        ps=[p for p in pressure if p['kind']==kind]
        if kind=='cpu':vals=[p['cpu_s']/p['duration_s'] for p in ps];unit='CPU seconds per wall second'
        elif kind=='memory':vals=[p['memory_touch_rounds']/p['duration_s'] for p in ps];unit='full64MiB page-touch rounds per second'
        else:vals=[p['written_bytes']/p['duration_s']/2**20 for p in ps];unit='MiB written per second through Python flushed rewrites'
        lines += ["",f"Achieved {kind} pressure ({len(ps)}runs): median{statistics.median(vals):.3f}, range[{min(vals):.3f},{max(vals):.3f}] {unit}. Full process liveness/intensity logs are immutable. This deliberately safe pressure does not establish host saturation or isolation."]
    lines += ["",report['cpu_efficiency_limit'],"", "Serialized complete CFR bytes/record and observed transport bytes/complete record have separate units/denominators. Per-worker-slot evidence is not unique-process efficiency; launch/recycle counts identify warm reuse.","",
              "## Findings, limitations and next actions","",
              "The tables preserve zero-coverage conditions, all paired effects, requested-versus-admitted work, expiry/drops, evidence time and bounded-state trends. Classification against high/moderate/low thirds is descriptive only. Cycle4 provides historical context: its different short runs and whole-batch admission cannot serve as an isolated worker-reuse control. The concurrent Cycle5 cold modes provide that control.","",
              report['specification'],"",report['quantiles'],"",
              "Limits: cooperative Windows processes; synthetic authored traffic; one host; three main seeds; bounded gentle contention; no hostile-container or Kubernetes isolation; no physical traffic ground truth; no hard real-time guarantee; no universal K scaling beyond two meaningful alternatives. Finite memory slopes and count caps cannot prove all future execution bounded without archival quota/rotation. Review may identify further limitations.","",
              "Open questions/next actions: independently challenge warm reset and lifecycle evidence; evaluate positive RSS slopes versus allocator behavior; audit narrow operating cells with fresh preregistered longer runs, stronger controlled contention and startup/backpressure telemetry before expanding domain or infrastructure claims. Trust remains DecisionD; learning remainsBLOCKED; no selector retuned."]
    Path(output).write_text("\n".join(lines)+"\n",encoding='utf-8')


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=("execute","prepare","run-one","analyze","verify","render","figures","document"));parser.add_argument("series")
    parser.add_argument("--output",default="research/tables/cycle5_verification.json");parser.add_argument("--row");parser.add_argument("--gate")
    args=parser.parse_args()
    if args.command=="execute":execute(args.series,args.gate)
    elif args.command=="prepare":prepare(args.series,args.gate)
    elif args.command=="run-one":run_one(args.series,json.loads(args.row))
    elif args.command=="verify":print(json.dumps(verify(args.series,args.output),indent=2))
    elif args.command=="render":render(args.series,args.output)
    elif args.command=="figures":figures(args.series,args.output)
    elif args.command=="document":document(args.series,args.output)
    else:Path(args.output).write_bytes(canonical(analyze(args.series)))
