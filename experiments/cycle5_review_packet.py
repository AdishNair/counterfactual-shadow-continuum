"""Deterministic compact packet for independent systems review; no raw mutation."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    source = ROOT / 'research/tables/cycle5_reviewer_brief.json'
    brief = json.loads(source.read_text(encoding='utf-8'))
    keys = ('mode', 'condition', 'seeds', 'coverage_by_seed', 'partial_fraction',
            'semantic_partial_fraction_by_seed', 'cadence_ms', 'cadence_p95_by_seed',
            'cadence_p99_by_seed', 'production_interval_ms_by_seed',
            'admitted_k_by_seed', 'completed_k_by_seed', 'branch_denominators',
            'expired', 'dropped', 'mirror_completion_fraction_by_seed',
            'alternative_completion_fraction_by_seed', 'complete_evidence_age_ms_by_seed',
            'complete_age_p95_by_seed', 'paired_cadence_effect_vs_same_load_k0_ms',
            'paired_cadence_effect_vs_same_mode_normal_ms')
    packet = {k: v for k, v in brief.items() if k not in ('main_groups', 'long_runs', 'long_hot_state_all_epochs')}
    packet['main_groups'] = [{k: g[k] for k in keys if k in g} for g in brief['main_groups']]
    long_keys = ('condition', 'measured_epochs', 'complete_fraction', 'partial_fraction',
                 'requested_k', 'admitted_k', 'completed_k', 'branch_status_counts',
                 'production_interval_ms', 'complete_evidence_age_ms',
                 'complete_records_during_production_per_s', 'serialized_bytes_per_complete_record',
                 'offline_summary_rss_bytes', 'offline_summary_ms', 'worker_recycles',
                 'artifact_bytes', 'coordinator_rss_bytes', 'coordinator_python_current_bytes',
                 'worker_rss_bytes', 'max_active', 'max_pending', 'max_queued')
    packet['long_runs'] = [{k: r[k] for k in long_keys if k in r} for r in brief['long_runs']]
    state_keys = ('minimum', 'maximum', 'end', 'all_epoch_slope', 'all_time_slope_per_s', 'second_half_epoch_slope')
    packet['long_hot_state_all_epochs'] = [dict(run_id=r['run_id'], epochs=r['epochs'],
        metrics={k: {n: m[n] for n in state_keys if n in m} for k, m in r['metrics'].items()})
        for r in brief['long_hot_state_all_epochs']]
    packet['packet_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    packet['input_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    target = ROOT / 'research/tables/cycle5_review_packet.json'
    target.write_text(json.dumps(packet, sort_keys=True, indent=2), encoding='utf-8')
    print(json.dumps(dict(path=str(target), bytes=target.stat().st_size,
                         sha256=hashlib.sha256(target.read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
