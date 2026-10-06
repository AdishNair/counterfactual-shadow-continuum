"""Read-only final derived tables and prose polishing; no measured source mutation."""
import argparse
from collections import Counter,defaultdict
import csv
import json
from pathlib import Path
import statistics

from csc.contracts import canonical
from experiments.replay import read_lines,sha256_file


def finalize(series):
    series=Path(series);table=Path('research/tables')
    registry=json.loads((series/'preregistration.json').read_text())['registry']
    epochs=[];groups=defaultdict(list)
    for row in registry:
        path=series/'runs'/row['run_id']; config=json.loads((path/'manifest.json').read_text())['config']
        lifecycle=list(read_lines(path/'lifecycle.jsonl'))
        physically_returned={e['branch_id'] for e in lifecycle if e.get('worker_runtime') and e['status'] in ('COMPLETED','LATE','FAILED','TIMED_OUT')}
        for r in read_lines(path/'cfr.jsonl'):
            reasons=Counter();statuses=Counter();physical=0
            for b in r['branches'][1:]:
                statuses[b['status']]+=1;physical+=b['branch_id'] in physically_returned
                if b['status']=='REPORTED' and b.get('synchronization',{}).get('comparable'):continue
                flags=b.get('failure_flags',[])
                if b['status']=='DROPPED':reason='queue_admission_failure:'+('+'.join(sorted(flags)) or 'unknown')
                elif b['status']=='EXPIRED':reason='expiry:'+('+'.join(sorted(flags)) or 'unknown')
                elif b['status']=='TIMEOUT':reason='execution_or_transport_timeout'
                elif b['status']=='FAULTED':reason='worker_or_transport_failure:'+('+'.join(sorted(flags)) or 'unknown')
                elif b['status']=='REJECTED':reason='schema_or_identity_rejection:'+('+'.join(sorted(flags)) or 'unknown')
                else:reason='other:'+b['status']+':'+('+'.join(sorted(flags)) or 'unknown')
                reasons[reason]+=1
            accepted=sum(b.get('status')=='REPORTED' and b.get('synchronization',{}).get('comparable') for b in r['branches'][1:])
            entry=dict(run_id=row['run_id'],kind=row['kind'],seed=row['seed'],mode=row['mode'],condition=row['condition'],epoch=r['epoch'],
                measured_cohort=r['epoch']>=config['warmup_epochs'],requested_k=r['requested_k'],admitted_k=r['admitted_k'],completed_k=r['completed_k'],
                requested_branches=len(r['branches'])-1,accepted_branches=accepted,physical_worker_returns=physical,
                complete_comparable_epoch=r['evidence_completeness']=='COMPLETE_COMPARISON',partial_requested_set=accepted>0 and r['evidence_completeness']!='COMPLETE_COMPARISON',
                branch_terminal_counts=dict(statuses),branch_loss_reason_counts=dict(reasons),epoch_loss_reason_set='+'.join(sorted(reasons)) or 'none',
                evidence_completeness=r['evidence_completeness'],resource_state=r['resource_state'])
            epochs.append(entry)
            if entry['measured_cohort'] and entry['requested_branches']:groups[(row['kind'],row['mode'],row['condition'])].append(entry)
    fields=list(epochs[0])
    with (table/'cycle5_epoch_loss.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fields);writer.writeheader()
        for row in epochs:
            writer.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,dict) else v for k,v in row.items()})
    output=[]
    for (kind,mode,condition),rows in sorted(groups.items()):
        loss=Counter();epochsets=Counter();status=Counter()
        for r in rows:
            loss.update(r['branch_loss_reason_counts']);status.update(r['branch_terminal_counts'])
            if not r['complete_comparable_epoch']:epochsets[r['epoch_loss_reason_set']]+=1
        output.append(dict(kind=kind,mode=mode,condition=condition,measured_epochs=len(rows),requested_branches=sum(r['requested_branches'] for r in rows),
            accepted_branches=sum(r['accepted_branches'] for r in rows),physical_worker_returns=sum(r['physical_worker_returns'] for r in rows),
            complete_comparable_epochs=sum(r['complete_comparable_epoch'] for r in rows),partial_requested_epochs=sum(r['partial_requested_set'] for r in rows),
            branch_terminal_counts=dict(status),branch_loss_reason_counts=dict(loss),incomplete_epoch_reason_sets=dict(epochsets),
            requested_k_mean=statistics.mean(r['requested_k'] for r in rows),admitted_k_mean=statistics.mean(r['admitted_k'] for r in rows),completed_k_mean=statistics.mean(r['completed_k'] for r in rows)))
    report=dict(source_series=str(series),analysis_script_sha256=sha256_file(__file__),epochs_classified=len(epochs),groups=output,
        limitations=['Physical returns mean lifecycle delivered worker-runtime envelope; this is not a count of all subprocess computations that may finish without accepted output.',
                     'Terminal flags establish observed queue/deadline loss, not a causal startup/scheduler/storage allocation. Startup-only cause remains unknown.',
                     'Loss categories can overlap within an epoch; every incomplete nonzero-K epoch retains its full reason set. K0 is excluded from evidence-loss denominators.'])
    (table/'cycle5_loss_groups.json').write_bytes(canonical(report))
    doc=Path('research/evidence/cycle5/cycle5_evidence_loss_analysis.md');text=doc.read_text(encoding='utf-8').split('\n## Cycle 5 completed-run loss decomposition\n')[0]
    lines=['','## Cycle 5 completed-run loss decomposition','','**Status:** Read-only deterministic derived analysis of the completed immutable Cycle 5 campaign. Epoch table: `research/tables/cycle5_epoch_loss.csv`; machine group counts and method identity: `research/tables/cycle5_loss_groups.json`. This appendix does not modify Cycle 4 findings.','','Every requested epoch (including separately marked warmups) has branch terminal statuses, observed reason counts, complete versus partial requested-set evidence, requested/admitted/completed K, and resource state. Headline groups below exclude declared warmups. Counts distinguish physical worker-return telemetry, timely accepted comparable branches, and complete comparable epochs. K excludes mirrors.','','| Track | Mode | Condition | Measured epochs | Accepted / requested branches | Complete epochs | Partial requested-set epochs | Branch loss reason counts |','|---|---|---|---:|---|---:|---:|---|']
    for g in output:lines.append(f"| {g['kind']} | {g['mode']} | {g['condition']} | {g['measured_epochs']} | {g['accepted_branches']} / {g['requested_branches']} | {g['complete_comparable_epochs']} | {g['partial_requested_epochs']} | {g['branch_loss_reason_counts']} |")
    lines += ['','Limitations: '+' '.join(report['limitations']),'','No incomplete requested epoch was discarded or recoded as success because fewer alternatives were admitted. Any accepted-but-incomplete mirror/alternative subset is scientifically partial even when the original raw `record_status` label differs. The frozen raw partial-label metric remains unchanged in the main archive.']
    doc.write_text(text+'\n'.join(lines)+'\n',encoding='utf-8')
    brief=json.loads((table/'cycle5_reviewer_brief.json').read_text())
    packet={k:brief[k] for k in ('source_series','gate_source_identity','main_archive_source_identity','main_csc_source_identity','gate_csc_source_identity','main_gate_csc_match','verification','scheduled_attempt_statuses','failed_attempts','pressure','production_errors','missing_production_epochs','unauthorized_mutations','assumptions','specification','cpu_efficiency_limit')}
    packet['script_sha256']=sha256_file(__file__)
    packet['main_groups']=[]
    for g in brief['main_groups']:
        selected={k:g[k] for k in ('mode','condition','coverage_by_seed','production_interval_ms_by_seed','cadence_p95_by_seed','cadence_p99_by_seed','partial_fraction_by_seed','no_accepted_evidence_fraction_by_seed','k_distribution_by_seed','evidence_classes_by_seed','branch_denominators','expired','dropped','complete_evidence_age_ms_by_seed','complete_age_p95_by_seed','paired_cadence_effect_vs_same_mode_normal_ms','paired_cadence_effect_vs_same_load_k0_ms')}
        selected['semantic_partial_by_seed']={s:e['any_accepted_but_incomplete_epoch_fraction'] for s,e in selected.pop('evidence_classes_by_seed').items()}
        selected['K_by_seed']={s:{k:[v['mean'],v['median'],v['p95'],v['p99']] for k,v in ds.items()} for s,ds in selected.pop('k_distribution_by_seed').items()}
        packet['main_groups'].append(selected)
    packet['K_units']='K_by_seed arrays: mean,median,p95,p99; excludesmirror'
    packet['warm_cold_effects']=brief['warm_cold_effects']
    packet['long_hot_state_all_epochs']=[dict(run_id=r['run_id'],epochs=r['epochs'],metrics={k:{f:v[f] for f in ('minimum','maximum','end','all_epoch_slope','all_time_slope_per_s','second_half_epoch_slope')} if v else None for k,v in r['metrics'].items()}) for r in brief['long_hot_state_all_epochs']]
    packet['long_runs']=[{k:r[k] for k in ('run_id','measured_epochs','complete_fraction','partial_fraction','no_accepted_evidence_fraction','requested_branches','admitted_branches','accepted_branches','branch_status_counts','production_interval_ms','complete_evidence_age_ms','requested_k','admitted_k','completed_k','offline_summary_ms','offline_summary_rss_bytes','artifact_bytes','complete_records_during_production_per_s','eventual_cohort_complete_records_per_paced_s')} for r in brief['long_runs']]
    for r in packet['long_runs']:r['offline_summary_rss_MiB']=r['offline_summary_rss_bytes']/2**20 if r['offline_summary_rss_bytes'] is not None else None
    (table/'cycle5_review_packet.json').write_bytes(canonical(packet))
    path=Path('research/evidence/cycle5/cycle5_results_analysis.md');text=path.read_text(encoding='utf-8')
    replacements={'and20excluded':'and 20 excluded','same300ms':'same 300 ms','deadline,40ms':'deadline, 40 ms','target,3slots,12active-task capacity,mirror-first':'target, 3 slots, 12 active-task capacity, mirror-first','test3000epochs':'test 3,000 epochs','and1000epochs':'and 1,000 epochs','Strict40ms':'Strict 40 ms','every100epoch':'every 100 epoch','first20warmups':'first 20 warmups','seeds 1501,1502,1503':'seeds 1501, 1502, 1503','full64MiB':'full 64 MiB','DecisionD':'Decision D','remainsBLOCKED':'remains BLOCKED','remaining 20warmups':'remaining 20 warmups'}
    for old,new in replacements.items():text=text.replace(old,new)
    text=text.split('\n## Evidence age and offline reduction details\n')[0]
    lines=['','## Evidence age and offline reduction details','','The exact seed distributions and per-action exposure counts remain in the reviewer packet; means cannot replace requested-set completeness.','','| Normal mode | Complete evidence-age medians by seed (ms) |','|---|---|']
    for mode in ('warm1','warm2'):
        g=next(g for g in brief['main_groups'] if (g['mode'],g['condition'])==(mode,'normal'))
        lines.append(f"| {mode} | {', '.join(f'{g["complete_evidence_age_ms_by_seed"][str(s)]:.6f}' for s in (1501,1502,1503))} |")
    lines+=['','| Long run | Complete / measured requested epochs | Complete age p95 / p99 ms | Offline summary RSS MiB | Requested / expired / dropped branches |','|---|---|---|---:|---|']
    for r in packet['long_runs']:
        complete=round(r['complete_fraction']*r['measured_epochs']);age=r['complete_evidence_age_ms'];counts=r['branch_status_counts']
        lines.append(f"| {r['run_id']} | {complete} / {r['measured_epochs']} | {age['p95']} / {age['p99']} | {r['offline_summary_rss_MiB']:.6f} | {r['requested_branches']} / {counts.get('EXPIRED',0)} / {counts.get('DROPPED',0)} |")
    lines+=['','Offline summary RSS is measured after the live production loop and after full history is loaded for exact reduction. It materially exceeds hot runtime RSS in the long normal run; bounded hot state is not a claim that end-of-run reduction or archival storage stays bounded.']
    path.write_text(text+'\n'.join(lines)+'\n',encoding='utf-8')
    return dict(epochs=len(epochs),loss_groups=len(output),packet_bytes=(table/'cycle5_review_packet.json').stat().st_size)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('series');a=p.parse_args();print(json.dumps(finalize(a.series)))
