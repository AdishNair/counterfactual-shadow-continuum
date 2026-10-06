"""Verify and summarize the final reviewed v5 correctness closure."""
import hashlib
import json
from pathlib import Path
import re
from csc.contracts import canonical

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'results/cycle5-validation/post-review-hardening-20261006-v5'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest=json.loads((DIRECTORY/'manifest.json').read_text())
    broken=[name for name,expected in manifest['artifact_hashes'].items() if sha(DIRECTORY/name)!=expected]
    changed=[name for name,expected in manifest['source_hashes'].items() if not (ROOT/name).is_file() or sha(ROOT/name)!=expected]
    runtime_changed=[name for name in changed if name.startswith(('csc/','tests/')) or name in ('experiments/cycle5_async.py','experiments/cycle5_pressure.py','experiments/cycle5_loss.py','experiments/replay.py')]
    log=(DIRECTORY/'unittest.log').read_text();match=re.search(r'Ran (\d+) tests in ([\d.]+)s',log)
    if manifest['status']!='COMPLETE' or manifest.get('gate_passed') is not True or broken or runtime_changed or not match or '\nOK\n' not in log:raise ValueError((broken,runtime_changed))
    negatives={row['mode']:json.loads(row['stdout']) for row in manifest['negative_probes']}
    summary=dict(status='LOCALLY_TESTED_POST_MEASUREMENT',tests=int(match[1]),test_seconds=float(match[2]),gate_elapsed_s=manifest['gate_elapsed_s'],
        validation_path=DIRECTORY.relative_to(ROOT).as_posix(),source_identity_sha256=manifest['source_identity_sha256'],csc_source_identity_sha256=manifest['csc_source_identity_sha256'],
        manifest_sha256=sha(DIRECTORY/'manifest.json'),broken_artifact_hashes=broken,runtime_source_changes_after_gate=runtime_changed,
        other_source_changes_after_gate=[name for name in changed if name not in runtime_changed],negative_controls=negatives,analysis_script_sha256=sha(Path(__file__)),
        performance_claim='none; immutable measured source not rerun')
    (ROOT/'research/tables/cycle5_post_review_hardening_v5.json').write_bytes(canonical(summary))
    report=f"""# Cycle 5 final reviewed correctness hardening

**Status:** Implemented and locally tested after the immutable main study. The v5
source-bound gate passed **{summary['tests']} tests in {summary['test_seconds']:.3f} seconds**.
No performance, memory, storage or evidence-yield experiment was rerun.

## Evidence and method

The v4 independent review identified three bounded MODERATE paths: consumed timing
values could break reduction, cleanup-failed artifacts could enter complete-run
analysis, and checked workspace source could change before its execution copy.
The immutable correction is `{summary['validation_path']}`. Full closure identity:
`{summary['source_identity_sha256']}`; CSC identity:
`{summary['csc_source_identity_sha256']}`. Artifact failures: `{broken}`;
runtime/test/campaign changes after the gate: `{runtime_changed}`.

Negative controls against archived v4 show: accepted hydration values produced a
nonfinite median and returned the worker; cold string startup timing was accepted;
cleanup-failed execution was absent from failure accounting; and an altered copied
pressure helper was accepted. These are mechanism probes, not main-run frequencies.

## Corrections

All required worker timings and optional startup timing, when present, now use a
finite arithmetic envelope with ordering checks. Cold and warm paths share it;
warm reset metadata remains conditional. Extreme hydration and malformed cold
startup values are rejected before publication or lease return.

Analysis reads `execution_status.json`. A control/cleanup-failed run preserves its
artifact status and production observations but is classified
`FAILED_CONTROL_OR_CLEANUP`, excluded from completed groups/effects, and retained
in the failure table.

Preparation rehashes every required copied source against the accepted gate before
collection can start. A deterministic copy-race regression corrupts the copied
pressure helper and requires preparation to fail. Explicit current-compatible
gate, protocol and unique-directory requirements remain.

## Limits

This closes named local cooperative mechanisms only. It does not prove exhaustive
schedules, OS cleanup, hostile containment, resource isolation, memory boundedness,
storage durability or corrected-source performance. The measured source retains
R1 storage, R5 memory, R6 cadence and R7 delayed-yield findings. Trust remains D;
learning remains BLOCKED. Any Cycle 6 collection requires a separate preregistration.
"""
    (ROOT/'research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v5.md').write_text(report,encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('status','tests','test_seconds','broken_artifact_hashes','runtime_source_changes_after_gate')}))
if __name__=='__main__':main()
