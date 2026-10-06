"""Compact deterministic reviewer evidence from completed Cycle 5 pilot artifacts."""
from collections import Counter
import argparse
import json
from pathlib import Path
import statistics

from csc.contracts import canonical,digest
from experiments.replay import read_lines,sha256_file


def hot_state_all_epochs(series,row):
    from csc.runner import distribution
    resources=list(read_lines(Path(series)/'runs'/row['run_id']/'resource_metrics.jsonl'))
    fields=('coordinator_rss_bytes','coordinator_python_current_bytes','coordinator_python_peak_bytes','coordinator_handles','worker_rss_bytes','worker_handles','worker_count','worker_launches','worker_recycles','worker_failures','pending_epochs','retained_completed_epochs','duplicate_cache_size','result_ledger_size','resource_history_size','worker_lifecycle_hot_count','queued_shadow_tasks','active_shadow_tasks','synchronization_hot_count','replay_metadata_hot_count','artifact_storage_bytes')
    def fit(points):
        if len(points)<2:return None
        xm=statistics.mean(p[0] for p in points);ym=statistics.mean(p[1] for p in points)
        d=sum((x-xm)**2 for x,_ in points)
        return sum((x-xm)*(y-ym) for x,y in points)/d if d else None
    stats={}
    for name in fields:
        rows=[r for r in resources if type(r.get(name)) in (int,float)]
        vals=[r[name] for r in rows];q=max(1,len(rows)//4)
        stats[name]=dict(n=len(vals),minimum=min(vals),maximum=max(vals),end=vals[-1],
                        all_epoch_slope=fit([(r['epoch'],r[name]) for r in rows]),
                        all_time_slope_per_s=fit([(r['epoch_started_monotonic_s'],r[name]) for r in rows]),
                        second_half_epoch_slope=fit([(r['epoch'],r[name]) for r in rows[len(rows)//2:]]),
                        first_quarter=distribution(vals[:q]),last_quarter=distribution(vals[-q:])) if vals else None
    return dict(run_id=row['run_id'],epochs=len(resources),cohort='all online epochs including0..19; evidence cohort remainswarmup-excluded',metrics=stats)


def brief(series,output):
    series=Path(series)
    report=json.loads((series/'analysis.json').read_text())
    groups=[]
    for g in report['groups']:
        rows=[r for r in report['runs'] if (r['mode'],r['condition'])==(g['mode'],g['condition']) and r.get('status')=='COMPLETE']
        item={k:g[k] for k in ('mode','condition','seeds','scheduled_runs','failed_runs','cadence_ms','complete_fraction','coverage_by_seed','partial_fraction','paired_cadence_effect_vs_same_mode_normal_ms','paired_cadence_effect_vs_same_load_k0_ms','expired','dropped')}
        for key,sub in (('production_interval_ms','median'),('production_decision_ms','median'),('complete_evidence_age_ms','median'),('admitted_k','median'),('completed_k','median'),('worker_startup_ms','median'),('queue_wait_ms','median')):
            item[key+'_by_seed']={str(r['seed']):r[key][sub] for r in rows}
        for key in ('mirror_completion_fraction','alternative_completion_fraction','mirror_plus_any_alternative_fraction','complete_records_during_production_per_s','eventual_cohort_complete_records_per_paced_s','complete_records_during_drain','epoch_execution_over_40ms','cadence_target_overruns','cumulative_schedule_drift_ms'):
            item[key+'_by_seed']={str(r['seed']):r[key] for r in rows}
        for key in ('partial_fraction','no_accepted_evidence_fraction'):
            item[key+'_by_seed']={str(r['seed']):r[key] for r in rows}
        item['k_distribution_by_seed']={}
        item['evidence_classes_by_seed']={}
        for r in rows:
            cohort=[e for e in read_lines(series/'runs'/r['run_id']/'cfr.jsonl') if e['epoch']>=20]
            item['k_distribution_by_seed'][str(r['seed'])]={key:dict(mean=statistics.mean(e[key] for e in cohort),median=r[key]['median'],p95=r[key]['p95'],p99=r[key]['p99']) for key in ('requested_k','admitted_k','completed_k')}
            classes=Counter(e['evidence_completeness'] for e in cohort)
            semantic_partial=sum(any(b.get('status')=='REPORTED' and b.get('synchronization',{}).get('comparable') for b in e['branches'][1:]) and e['evidence_completeness']!='COMPLETE_COMPARISON' for e in cohort)
            item['evidence_classes_by_seed'][str(r['seed'])]=dict(counts=dict(classes),any_accepted_but_incomplete_epoch_fraction=semantic_partial/len(cohort) if r['mode']!='k0' else None,
                raw_record_status_partial_fraction=r['partial_fraction'],note='Mirror-only or alternative-only evidence is partial requested-set evidence even if rawrecord_status uses another label')
        item['cadence_p95_by_seed']={str(r['seed']):r['production_interval_ms']['p95'] for r in rows}
        item['cadence_p99_by_seed']={str(r['seed']):r['production_interval_ms']['p99'] for r in rows}
        item['complete_age_p95_by_seed']={str(r['seed']):r['complete_evidence_age_ms']['p95'] for r in rows}
        actioncounts={}
        for key in rows[0]['per_action_role_counts']:
            actioncounts[key]=dict(Counter({field:sum(r['per_action_role_counts'][key][field] for r in rows) for field in rows[0]['per_action_role_counts'][key]}))
        item['per_action_role_counts']=actioncounts
        item['branch_denominators']=dict(requested=sum(r['requested_branches'] for r in rows),admitted=sum(r['admitted_branches'] for r in rows),accepted=sum(r['accepted_branches'] for r in rows))
        groups.append(item)
    effects=[]
    for k in (1,2):
        for c in ('normal','moderate','severe','cpu','memory','storage'):
            es=[e for e in report['warm_cold_paired_effects'] if (e['k'],e['condition'])==(k,c)]
            effects.append(dict(k=k,condition=c,coverage_gain_by_seed={str(e['seed']):e['complete_fraction_gain'] for e in es},cadence_change_by_seed_ms={str(e['seed']):e['cadence_change_ms'] for e in es}))
    pressure={}
    for kind in ('cpu','memory','storage'):
        rows=[r['pressure_validation'] for r in report['runs'] if r.get('pressure_validation') and r['pressure_validation']['kind']==kind]
        name='cpu_s_per_wall_s' if kind=='cpu' else 'page_touch_rounds_per_s' if kind=='memory' else 'flushed_MiB_per_s'
        vals=[r['cpu_s']/r['duration_s'] if kind=='cpu' else r['memory_touch_rounds']/r['duration_s'] if kind=='memory' else r['written_bytes']/r['duration_s']/2**20 for r in rows]
        pressure[kind]=dict(runs=len(rows),unit=name,min=min(vals),median=statistics.median(vals),max=max(vals),all_values=vals)
    long=[r for r in report['runs'] if r['kind']=='long']
    statuses=json.loads((series/'execution_status.json').read_text())
    verification=Path('research/tables/cycle5_verification.json')
    prereg=json.loads((series/'preregistration.json').read_text())
    main_csc={k:v for k,v in prereg['source_hashes'].items() if k.startswith('csc/')}
    gate=json.loads((series/'source/results/cycle5-gate/runtime-20261006-v2/manifest.json').read_text())
    gate_csc={k:v for k,v in gate['source_hashes'].items() if k.startswith('csc/')}
    result=dict(source_series=str(series),analysis_script_sha256=sha256_file(__file__),main_analysis_sha256=sha256_file(series/'analysis.json'),
                environment=prereg['environment'],
                gate_source_identity=prereg['correctness_gate_source_identity_sha256'],
                main_archive_source_identity=digest(prereg['source_hashes']),
                main_csc_source_identity=digest(main_csc),gate_csc_source_identity=digest(gate_csc),main_gate_csc_match=main_csc==gate_csc,
                verification=json.loads(verification.read_text()) if verification.exists() else None,
                scheduled_attempt_statuses=dict(Counter(r['status'] for r in statuses)),failed_attempts=[r for r in statuses if r['status']!='COMPLETE'],
                main_groups=groups,warm_cold_effects=effects,pressure=pressure,long_runs=long,
                long_hot_state_all_epochs=[hot_state_all_epochs(series,r) for r in long],
                production_errors=sum(r.get('production_failures',0) for r in report['runs']),
                missing_production_epochs=sum(r.get('missed_epoch_count',r.get('missing_production_epochs',0)) for r in report['runs']),
                unauthorized_mutations=sum(r.get('unauthorized_mutations',0) for r in report['runs']),
                assumptions=report['experimental_unit'],specification=report['specification'],cpu_efficiency_limit=report['cpu_efficiency_limit'])
    Path(output).write_bytes(canonical(result))
    return result


def order_figure(series,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    report=json.loads((Path(series)/'analysis.json').read_text())
    fig,ax=plt.subplots(figsize=(11,4))
    for mode in ('k0','cold1','cold2','warm1','warm2'):
        rows=[r for r in report['runs'] if r['kind']=='factorial' and r['mode']==mode and r.get('status')=='COMPLETE']
        ax.scatter([r['order'] for r in rows],[r['production_interval_ms']['median'] for r in rows],label=mode,s=26)
    ax.axhline(40,color='black',linestyle='--',alpha=.4,label='40ms pacing target')
    ax.set_xlabel('Recorded run order; conditions randomized within seed blocks');ax.set_ylabel('Per-run production median interval (ms)');ax.grid(alpha=.2);ax.legend(ncol=3)
    fig.tight_layout();fig.savefig(output,dpi=180);plt.close(fig)
    Path(output).with_suffix('.json').write_bytes(canonical(dict(source=str(Path(series)/'analysis.json'),analysis_script_sha256=sha256_file(__file__),purpose='Expose order/host-state heterogeneity; descriptive, not a fitted condition correction',matplotlib_version=matplotlib.__version__)))


def addendum(report,output):
    path=Path(output);text=path.read_text(encoding='utf-8')
    text=text.split('\n## Postcollection measurement clarifications\n')[0]
    text=text.replace('Partial fraction median |','Raw record-status PARTIAL fraction median |')
    lines=['','## Postcollection measurement clarifications','','**Status:** Independently hashed deterministic derived supplement; frozen source, raw outcomes and original analysis remain unchanged. Supplement identity: `experiments/cycle5_compact.py` / `research/tables/cycle5_reviewer_brief.json`. No deadline, cohort, threshold or duration changed.','','The frozen partial-fraction field counts raw `record_status == PARTIAL`. That label omits some mirror-only/alternative-only evidence. The following semantic partial measure counts epochs with any accepted comparable nonproduction branch but without the full originally requested mirror-plus-K set. Both measures remain visible; complete-epoch completeness is unchanged.','','| Mode | Condition | Any accepted but incomplete requested-set evidence (seeds 1501,1502,1503) |','|---|---|---|']
    for g in report['main_groups']:
        if g['mode']=='k0':continue
        values=[g['evidence_classes_by_seed'][str(s)]['any_accepted_but_incomplete_epoch_fraction'] for s in (1501,1502,1503)]
        lines.append(f"| {g['mode']} | {g['condition']} | {', '.join(f'{v:.6f}' for v in values)} |")
    lines += ['','Frozen resource trend tables exclude the first20warmups. The preregistered online-state estimand includes all epochs; the independently hashed supplement below restores that all-epoch estimand, while retaining frozen estimates. All-state plots already include all epochs.','','| Run | All online epochs | RSS maximum MiB | RSS all-epoch slope bytes/epoch | RSS second-half slope bytes/epoch | Python current all-epoch slope bytes/epoch | Python current second-half slope bytes/epoch |','|---|---:|---:|---:|---:|---:|---:|']
    for r in report['long_hot_state_all_epochs']:
        rss=r['metrics']['coordinator_rss_bytes'];py=r['metrics']['coordinator_python_current_bytes']
        lines.append(f"| {r['run_id']} | {r['epochs']} | {rss['maximum']/2**20:.6f} | {rss['all_epoch_slope']:.6f} | {rss['second_half_epoch_slope']:.6f} | {py['all_epoch_slope']:.6f} | {py['second_half_epoch_slope']:.6f} |")
    lines += ['','Positive finite-duration slopes do not establish an indefinitely stable memory plateau. Structural count caps, small observed RSS ranges, Python allocations and archival growth are separate findings. Main source-archive identity: `'+report['main_archive_source_identity']+'`; gate source identity: `'+report['gate_source_identity']+'`; exact CSC subclosure match: `'+str(report['main_gate_csc_match'])+'`.','','Figure caption clarification: K excludes the mirror from the alternative count. Complete evidence in every coverage figure requires the mirror and all K requested alternatives; the words "mirror excluded" in the frozen plot title refer only to K counting. The run-order figure exposes heterogeneous early timing; no fitted correction or selective exclusion is applied.']
    path.write_text(text+'\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('series');p.add_argument('--output',default='research/tables/cycle5_reviewer_brief.json');p.add_argument('--order-figure');p.add_argument('--document');a=p.parse_args()
    b=brief(a.series,a.output)
    if a.order_figure:order_figure(a.series,a.order_figure)
    if a.document:addendum(b,a.document)
    print(json.dumps(dict(statuses=b['scheduled_attempt_statuses'],groups=len(b['main_groups']),warm_cold_effect_groups=len(b['warm_cold_effects']),long_runs=len(b['long_runs']),verification=b['verification']),indent=2))
