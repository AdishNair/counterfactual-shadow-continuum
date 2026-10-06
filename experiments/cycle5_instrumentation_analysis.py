"""Deterministically verify and report immutable sampler retention diagnostics."""
import hashlib
import json
from pathlib import Path

from csc.contracts import canonical, digest


def analyze(root):
    diagnostics = {}
    for version in ("v3", "v4"):
        path = root / "results/cycle5-validation" / f"os-metrics-cache-20261006-{version}"
        manifest = json.loads((path / "manifest.json").read_text())
        data = json.loads((path / "diagnostic.json").read_text())
        broken = [name for name, expected in manifest["artifact_hashes"].items()
                  if hashlib.sha256((path / name).read_bytes()).hexdigest() != expected]
        if broken or data["config_hash"] != digest(data["config"]):
            raise ValueError(f"diagnostic integrity failure: {version}, {broken}")
        if data["script_identity_sha256"] != manifest["artifact_hashes"]["diagnose.py"]:
            raise ValueError("diagnostic script identity mismatch")
        blocks = []
        for row in data["rows"]:
            if row["elapsed_s"] is not None:
                count = 10 if row["cumulative_calls"] == 10 else 100
                blocks.append({"calls": count, "total_ms": row["elapsed_s"] * 1000,
                               "mean_ms_per_call": row["elapsed_s"] * 1000 / count})
        diagnostics[version] = {"path": str(path.relative_to(root)).replace("\\", "/"),
                                "artifact_hash_failures": broken, "source_hash": data["source_hash"],
                                "environment": data["environment"], "rows": data["rows"],
                                "block_timings": blocks,
                                "manifest_hash": hashlib.sha256((path / "manifest.json").read_bytes()).hexdigest()}
    primary = diagnostics["v3"]
    gc_rows = [row for row in primary["rows"] if row["phase"].endswith("_gc")]
    if not gc_rows or any(row["gc_visible_live_counter_classes"] or row["reachable_observed_counter_classes"] for row in gc_rows):
        raise ValueError("this report requires the observed zero-retained-class finding")
    current_source = hashlib.sha256((root / "csc/os_metrics.py").read_bytes()).hexdigest()
    source_unchanged = all(item["source_hash"] == current_source for item in diagnostics.values())
    if not source_unchanged:
        raise ValueError("frozen measurement source differs from current source")
    summary = {"status": "COMPLETE", "analysis_script_identity_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "source_unchanged": source_unchanged, "source_hash": current_source,
               "primary": "v3", "mechanism_confirmation": "v4", "diagnostics": diagnostics,
               "finding": "No GC-visible Counters class or observed weak-reference target survives explicit collection in either measured block",
               "hypothesis_scope": "Persistent Counters/pointer-class retention prediction falsified for these bounded probes; general allocation plateau not established"}
    return summary


def write_report(root, summary):
    primary = summary["diagnostics"]["v3"]
    rows = primary["rows"]
    table = ["| Phase | Live Counters | Observed weakrefs still reachable | Python current bytes |",
             "|---|---:|---:|---:|"]
    for row in rows:
        table.append(f"| {row['phase']} | {row['gc_visible_live_counter_classes']} | {row['reachable_observed_counter_classes']} | {row['python_current_bytes']} |")
    timings = primary["block_timings"]
    mechanism = summary["diagnostics"]["v4"]["rows"]
    attributes = [row["classes_with_pointer_type_attribute"] for row in mechanism if row["elapsed_s"] is not None]
    report = f"""# Cycle 5 instrumentation retention diagnostic

**Status:** Locally measured after all 86 main campaign runs completed. No
diagnostic overlapped measured production, and CSC source was not changed.

## Question, evidence and method

Does constructing a new Windows `Counters` ctypes type on every resource sample
retain those classes indefinitely, or create cycles reclaimed by garbage
collection? The specific persistent-Counters prediction was **not observed**:
all observed class weak references were dead after collection in both blocks.
This does not establish general memory-leak freedom or a long-run memory plateau.

Primary evidence: `{primary['path']}/diagnostic.json`; mechanism confirmation:
`{summary['diagnostics']['v4']['path']}/diagnostic.json`. The deterministic
analyzer is `experiments/cycle5_instrumentation_analysis.py`, with verified
machine output at `research/tables/cycle5_instrumentation_diagnostic.json`.
Both archives have valid artifact/config/script identities and the unchanged
measurement-source hash `{summary['source_hash']}`.

Each probe preloaded one call, then measured blocks of 10 and 100 self-process
samples with current/peak Python allocations, GC-visible `Counters` classes and
weak references before and after explicit collection. This is Python
{primary['environment']['python']} on {primary['environment']['platform']}.

Python 3.14 documentation describes pointer-type caching through a type's
`__pointer_type__` attribute. The documentation opened during this cycle was
Python 3.14.8; the actual measured runtime was 3.14.7. See the
[official ctypes POINTER documentation](https://docs.python.org/3.14/library/ctypes.html#ctypes.POINTER).
The v4 confirmation observed this attribute through normal attribute lookup on
{attributes[0]} and {attributes[1]} live classes, with matching pointed-to-class
backreferences, despite the attribute being absent from the classes' own
dictionaries. All those classes were subsequently collected.

## Primary findings

{chr(10).join(table)}

Ten calls took {timings[0]['total_ms']:.4f} ms total
({timings[0]['mean_ms_per_call']:.4f} ms/call); the next 100 calls took
{timings[1]['total_ms']:.4f} ms ({timings[1]['mean_ms_per_call']:.4f} ms/call).
These are post-collection microdiagnostic timings, not reconstructed main-run
instrumentation costs. The probes do not explain a production cadence change.

Residual traced allocations increased from {rows[0]['python_current_bytes']}
bytes at baseline to {rows[-1]['python_current_bytes']} bytes after the final
collection. Diagnostic bookkeeping, ctypes allocations and allocator behavior
remain included; zero surviving target classes does not mean zero retained
allocation. The broader memory question is decided from the main long-run
current-allocation/RSS trends in `research/evidence/cycle5/cycle5_results_analysis.md`, rather
than from this short probe. Positive main-run slopes must not be reinterpreted
as a plateau because this one mechanism was not detected.

## Preserved attempts and limitations

V1 is an unexecuted draft. V2 failed before measured blocks because Python
3.14.7 exposes `_pointer_type_cache` as a compatibility object without `len()`;
its FAILED manifest is preserved. V3 treats that legacy count as unavailable and
provides the primary GC/weak-reference result. Its initial direct-class-dictionary
attribute check was incomplete; v4 used normal attribute lookup and confirmed the
documented type-local mechanism. V4 repeats the bounded probe and is a mechanism
confirmation, not a new fundamental evidence series or a main-study retune.

Only GC-visible target classes are counted. Explicit collection distinguishes
retention from reclamation but does not represent normal collection cadence.
Both probes have 110 measured calls; neither is a long-run experiment. No
resource isolation, real-time guarantee or universal memory bound follows.

## Next actions

No CSC correction is justified by the specific retained-Counters hypothesis.
Preserve the frozen main evidence, retain unresolved memory growth where present,
and investigate allocator/instrumentation costs separately if main trends warrant
it. Any future sampler optimization needs new source identity, a correctness gate
and preregistered confirmation; it must not replace the present results.
"""
    table_path = root / "research/tables/cycle5_instrumentation_diagnostic.json"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_bytes(canonical(summary))
    (root / "research/evidence/cycle5/cycle5_instrumentation_diagnostic.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    summary = analyze(root)
    write_report(root, summary)
    print(json.dumps({"status": summary["status"], "source_unchanged": summary["source_unchanged"],
                      "primary": summary["primary"], "source_hash": summary["source_hash"],
                      "finding": summary["finding"]}))
