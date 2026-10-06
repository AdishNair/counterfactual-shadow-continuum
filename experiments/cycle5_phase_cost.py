"""Read-only timing diagnostic; supplements rather than changes frozen main analysis."""
import argparse
import json
from pathlib import Path

from csc.contracts import canonical
from csc.runner import distribution
from experiments.replay import read_lines, sha256_file


def diagnose(series,output):
    series=Path(series)
    statuses=json.loads((series/'execution_status.json').read_text())
    reports=[]
    for status in statuses:
        path=series/'runs'/status['run_id']
        if status['status']!='COMPLETE' or not (path/'summary.json').exists():continue
        manifest=json.loads((path/'manifest.json').read_text())
        resources=list(read_lines(path/'resource_metrics.jsonl'))
        warmup=manifest['config']['warmup_epochs']
        measured=resources[warmup:]
        item=dict(run_id=status['run_id'],elapsed_attempt_s=status['duration_s'],
                  production_span_s=resources[-1]['epoch_started_monotonic_s']-resources[0]['epoch_started_monotonic_s'])
        for field in ('production_interval_ms','production_path_ms','production_decision_ms','evidence_bookkeeping_ms','epoch_ms','worker_count','coordinator_cpu_ms'):
            item[field]=distribution([r.get(field) for r in measured])
        # Interval ending at e covers previous e-1 work, not current e work.
        gaps=[resources[e]['production_interval_ms']-resources[e-1]['epoch_ms'] for e in range(max(1,warmup),len(resources))]
        excess=[resources[e]['production_interval_ms']-max(manifest['config']['production_period_s']*1000,resources[e-1]['epoch_ms']) for e in range(max(1,warmup),len(resources))]
        item['unmeasured_after_epoch_timer_including_sleep_and_jitter_ms']=distribution(gaps)
        item['interval_excess_beyond_max_pacing_or_prior_epoch_timer_ms']=distribution(excess)
        summary=json.loads((path/'summary.json').read_text())
        for field in ('worker_pool_initialization_s','offline_summary_ms','shutdown_after_production_ms'):
            item[field]=summary.get(field)
        reports.append(item)
    report=dict(source_series=str(series),analysis_script_sha256=sha256_file(__file__),runs=reports,
                status='READ_ONLY_PHASE_COST_DIAGNOSTIC; no performance retuning',
                interpretation_limits=[
                    'epoch_ms ends before coordinator OS process metrics, per-worker OS metrics, artifact directory stats, resource-row serialization/flush and sleep.',
                    'Residual contains these operations plus pacing sleep and host scheduling jitter. It does not identify an OS-sampling-only causal duration.',
                    'Production cadence includes all these costs. No phase correction is applied to measured cadence.',
                    'Early completed cells are a runtime diagnostic, not a selected condition-effect or evidence-yield analysis.'])
    Path(output).write_bytes(canonical(report))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('series');p.add_argument('--output',default='research/tables/cycle5_phase_cost_diagnostic.json');a=p.parse_args()
    print(json.dumps(diagnose(a.series,a.output),indent=2))
