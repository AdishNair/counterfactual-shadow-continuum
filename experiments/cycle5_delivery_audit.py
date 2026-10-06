"""Read-only final delivery/provenance audit; never regenerates raw evidence."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


REQUIRED = (
    "research/evidence/cycle5/CYCLE5_EXECUTIVE_SUMMARY.md", "research/evidence/cycle5/cycle5_protocol.md",
    "research/evidence/cycle5/cycle5_evidence_loss_analysis.md", "research/evidence/cycle5/warm_worker_correctness.md",
    "research/evidence/cycle5/runtime_retention_design.md", "research/evidence/cycle5/information_timing_audit.md",
    "research/evidence/cycle5/cycle5_results_analysis.md", "research/evidence/cycle5/cycle5_red_team_review.md",
    "research/CLAIM_EVIDENCE_MATRIX.md", "research/RESEARCH_STATUS.md",
    "research/RESEARCH_CONTEXT.md", "research/HUMAN_GUIDE.md",
    "IMPLEMENTATION_STATUS.md", "RESULTS.md", "docs/DOMAIN_INTERFACE.md",
    "research/evidence/cycle5/cycle5_failure_recovery.md", "research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening.md",
    "research/archive/cycle5/post_collection_hardening/cycle5_post_review_campaign_hardening.md", "research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview.md",
    "research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v2.md",
    "research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v3.md", "research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v3.md",
    "research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v4.md", "research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v4.md",
    "research/archive/cycle5/post_collection_hardening/cycle5_post_review_hardening_v5.md", "research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v5.md",
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def hashed(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def check_hashes(root, hashes):
    broken = []
    for relative, expected in hashes.items():
        target = root / relative
        if not target.is_file() or hashed(target) != expected:
            broken.append(relative)
    return {"files_checked": len(hashes), "broken": broken}


def audit(repository=Path("."), hardening="results/cycle5-validation/post-review-hardening-20261006-v1"):
    repository = Path(repository).resolve()
    main = repository / "results/cycle5-async/local-20261006-v1"
    manifest = read(main / "series_manifest.json")
    plan = read(main / "preregistration.json")
    registry = plan["registry"]
    ids = [row["run_id"] for row in registry]
    statuses = read(main / "execution_status.json")
    actual = [directory.name for directory in (main / "runs").iterdir() if directory.is_dir()]
    failures = []
    series_hashes = check_hashes(main, manifest["artifact_hashes"])
    archived_source = check_hashes(main / "source", plan["source_hashes"])
    if series_hashes["broken"] or archived_source["broken"]:
        failures.append("main artifact/source hashes")
    differences = {"missing": sorted(set(ids) - set(actual)), "unexpected": sorted(set(actual) - set(ids)),
                   "duplicate_registry": sorted(key for key, count in Counter(ids).items() if count != 1),
                   "duplicate_status": sorted(key for key, count in Counter(x["run_id"] for x in statuses).items() if count != 1)}
    if any(differences.values()):
        failures.append("run identity inventory")
    registry_matches_manifest = manifest["registry"] == registry and manifest["configs"] == plan["configs"]
    recorded_order_matches = [row["run_id"] for row in statuses] == ids
    if not registry_matches_manifest or not recorded_order_matches:
        failures.append("frozen registry/order mismatch")
    factor_errors, run_checks = [], []
    paired = defaultdict(lambda: {"production": set(), "workload": set(), "runs": 0})
    main_seeds, long_seeds = set(), set()
    for row in registry:
        run_path = main / "runs" / row["run_id"]
        if not (run_path / "manifest.json").is_file():
            continue
        run_manifest = read(run_path / "manifest.json")
        config = run_manifest["config"]
        expected = plan["configs"][row["run_id"]]
        hashes = check_hashes(run_path, run_manifest["artifact_hashes"])
        source = check_hashes(main / "source", run_manifest["source_hashes"])
        config_ok = config == expected and hashlib.sha256(canonical(config)).hexdigest() == run_manifest["config_hash"]
        mode_k = {"k0": 0, "cold1": 1, "cold2": 2, "warm1": 1, "warm2": 2}[row["mode"]]
        factor_ok = (config["random_seed"] == row["seed"] and config["shadow_count"] == mode_k
                     and config["worker_mode"] == ("warm" if row["mode"].startswith("warm") else "cold")
                     and config["mirror_count"] == (0 if mode_k == 0 else 1)
                     and config["shadow_injected_delay_s"] == row["delay_s"]
                     and config["shadow_result_deadline_s"] == .3 and config["production_period_s"] == .04
                     and config["max_pending_shadow_tasks"] == 12 and config["max_pending_epochs"] == 16
                     and config["retention_completed_epochs"] == 64 and not config["learning_enabled"])
        if not config_ok or not factor_ok:
            factor_errors.append(row["run_id"])
        summary = read(run_path / "summary.json")
        summary_workload_ok = summary["workload_sha256"] == run_manifest["workload_sha256"]
        result = {"run_id": row["run_id"], "status": run_manifest["status"], "config_matches_plan": config_ok,
                  "factors_match_registry": factor_ok, "artifact_files": hashes["files_checked"], "broken_artifacts": hashes["broken"],
                  "source_files": source["files_checked"], "broken_source": source["broken"],
                  "summary_workload_matches_manifest": summary_workload_ok}
        run_checks.append(result)
        if hashes["broken"] or source["broken"] or not summary_workload_ok or run_manifest["status"] != "COMPLETE":
            failures.append("run provenance " + row["run_id"])
        if row["kind"] == "factorial":
            main_seeds.add(row["seed"])
            paired[row["seed"]]["production"].add(summary["production_semantic_sha256"])
            paired[row["seed"]]["workload"].add(summary["workload_sha256"])
            paired[row["seed"]]["runs"] += 1
        else:
            long_seeds.add(row["seed"])
    if factor_errors:
        failures.append("run config/factor mismatch")
    allowed_cells = {("k0", condition) for condition in ("normal", "cpu", "memory", "storage")}
    allowed_cells |= {(mode, condition) for mode in ("cold1", "cold2", "warm1", "warm2")
                     for condition in ("normal", "moderate", "severe", "cpu", "memory", "storage")}
    actual_grid = {(r["seed"], r["mode"], r["condition"]) for r in registry if r["kind"] == "factorial"}
    grid_counts = Counter((r["seed"], r["mode"], r["condition"]) for r in registry if r["kind"] == "factorial")
    grid_ok = (actual_grid == {(seed, mode, condition) for seed in (1501, 1502, 1503) for mode, condition in allowed_cells}
               and all(value == 1 for value in grid_counts.values()))
    if not grid_ok or main_seeds & long_seeds or long_seeds != {1510, 1511}:
        failures.append("grid/seed allocation")
    paired_checks = {str(seed): {"runs": values["runs"], "production_hash_count": len(values["production"]),
                               "workload_hash_count": len(values["workload"])} for seed, values in paired.items()}
    if any(row["production_hash_count"] != 1 or row["workload_hash_count"] != 1 for row in paired_checks.values()):
        failures.append("paired trajectory/workload mismatch")
    gate_path = repository / "results/cycle5-gate/runtime-20261006-v2"
    gate = read(gate_path / "manifest.json")
    gate_hashes = check_hashes(gate_path, gate["artifact_hashes"])
    measured_csc = {key: value for key, value in plan["source_hashes"].items() if key.startswith("csc/")}
    gate_csc = {key: value for key, value in gate["source_hashes"].items() if key.startswith("csc/")}
    gate_matches = measured_csc == gate_csc
    if not gate_matches or gate_hashes["broken"] or not gate["gate_passed"]:
        failures.append("measured source gate")
    hard_path = repository / hardening
    hard = read(hard_path / "manifest.json")
    hard_hashes = check_hashes(hard_path, hard["artifact_hashes"])
    current_csc = {str(path.relative_to(repository)).replace("\\", "/"): hashed(path)
                   for path in (repository / "csc").glob("*.py")}
    hard_source_hashes = hard.get("after_source_hashes", hard.get("source_hashes", {}))
    hard_csc = {key: value for key, value in hard_source_hashes.items() if key.startswith("csc/")}
    hard_changes = sorted(key for key in set(current_csc) | set(hard_csc) if current_csc.get(key) != hard_csc.get(key))
    if hard_hashes["broken"] or hard_changes or hard["status"] != "COMPLETE" or hard["exit_code"]:
        failures.append("current corrected gate")
    fault_directories = []
    for path in sorted((repository / "results/cycle5-validation").glob("faults-*")):
        evidence = read(path / "manifest.json")
        checked = check_hashes(path, evidence["artifact_hashes"])
        fault_directories.append({"path": str(path.relative_to(repository)), "status": evidence["status"], **checked})
        if checked["broken"]:
            failures.append("fault archive mutation")
    cleanup = []
    for path in sorted((repository / "results/cycle5-post-review").glob("campaign-cleanup-*/manifest.json")):
        evidence = read(path)
        cleanup_hashes = evidence.get("artifact_hashes", {"unittest.log": evidence["log_sha256"]})
        checked = check_hashes(path.parent, cleanup_hashes)
        cleanup.append({"path": str(path.parent.relative_to(repository)), "status": evidence["status"], **checked})
        if checked["broken"]:
            failures.append("cleanup archive mutation")
    if not cleanup:
        failures.append("missing campaign cleanup evidence")
    forbidden = set(range(841, 861))
    forbidden_main_seeds = sorted({r["seed"] for r in registry} & forbidden)
    trust_directory_names = sorted(path.name for path in (repository / "results/cycle4-trust").iterdir() if path.is_dir())
    forbidden_final_dirs = [name for name in trust_directory_names if "final" in name.lower() or "held" in name.lower()]
    if forbidden_main_seeds or forbidden_final_dirs:
        failures.append("unexpected forbidden final trust seed/directory")
    required_checks = {path: (repository / path).is_file() and (repository / path).stat().st_size > 0 for path in REQUIRED}
    missing_required = [path for path, exists in required_checks.items() if not exists]
    if missing_required:
        failures.append("missing delivery artifact")
    previous_verification = read(repository / "research/tables/cycle5_verification.json")
    if previous_verification["status"] != "VERIFIED" or previous_verification["failures"]:
        failures.append("previous deterministic replay/summary verification failed")
    review_files = ("research/evidence/cycle5/cycle5_red_team_review.md", "research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview.md",
                    "research/archive/cycle5/post_collection_hardening/cycle5_post_review_rereview_v2.md")
    review_evidence = [{"path": relative, "sha256": hashed(repository / relative) if (repository / relative).is_file() else None,
                       "scope": "independent static review of supplied source/evidence; no independent test execution or hash recomputation"}
                      for relative in review_files]
    return {"status": "VERIFIED" if not failures else "INCOMPLETE_OR_FAILED", "failures": sorted(set(failures)),
            "method": "read-only streaming hash/inventory/config audit; reuses prior deterministic replay/summary checks without rerunning trajectories",
            "analysis_script_sha256": hashed(Path(__file__)), "required_artifacts": required_checks,
            "missing_required": missing_required, "run_inventory": differences, "scheduled_runs": len(registry),
            "execution_status_counts": dict(Counter(x["status"] for x in statuses)),
            "main_artifacts": series_hashes, "main_source": archived_source, "run_provenance": run_checks,
            "factor_errors": factor_errors, "grid_exact": grid_ok, "main_seeds": sorted(main_seeds),
            "registry_matches_manifest": registry_matches_manifest, "recorded_order_matches": recorded_order_matches,
            "long_seeds": sorted(long_seeds), "unexpected_seed_overlap": sorted(main_seeds & long_seeds),
            "paired_hashes": paired_checks, "measured_gate": {"hashes": gate_hashes, "csc_closure_equal": gate_matches},
            "corrected_gate": {"hashes": hard_hashes, "current_csc_changes": hard_changes,
                               "source_variant": hard.get("source_variant", hard.get("scope")),
                               "source_identity": hard["source_identity_sha256"]},
            "fault_archives": fault_directories, "campaign_cleanup": cleanup,
            "independent_review_evidence": review_evidence,
            "forbidden_trust_checks": {"main_seed_overlap": forbidden_main_seeds, "observed_top_level_directories": trust_directory_names,
                                      "unexpected_final_or_heldout_directories": forbidden_final_dirs,
                                      "scope": "Cycle4 trust top-level directory inventory plus Cycle5 frozen seed plan; not exhaustive arbitrary-filesystem surveillance"},
            "prior_replay_and_summary_verification": previous_verification,
            "limitations": ["Hash equality verifies preserved recorded bytes, not physical validity or complete OS event history",
                            "Post-review current source has no repeated main performance campaign",
                            "Prior replay is reused; this delivery audit does not regenerate headline statistics"]}


def report(result, target):
    text = f"""# Cycle 5 reproducibility and delivery audit

**Status:** {result['status']}; deterministic read-only delivery audit, 2026-10-06.

## Question, evidence and method

Are the required research artifacts present, the frozen run inventory/configs/seeds exact, and raw/source/gate evidence unchanged? `experiments/cycle5_delivery_audit.py` streams SHA-256 checks and compares manifests without modifying results. Machine evidence: `research/tables/cycle5_delivery_audit.json`. Existing deterministic archived-source replay/summary verification is reused, not rerun.

## Findings

- Scheduled main/long runs: {result['scheduled_runs']}; execution status counts: {result['execution_status_counts']}.
- Exact factorial grid: {result['grid_exact']}; unexpected seed overlap: {result['unexpected_seed_overlap']}; config/factor errors: {result['factor_errors']}.
- Main series artifact hashes: {result['main_artifacts']['files_checked']} checked, {len(result['main_artifacts']['broken'])} broken. Archived source hashes: {result['main_source']['files_checked']} checked, {len(result['main_source']['broken'])} broken. Per-run provenance checks remain in JSON.
- Measured CSC/gate closure matches: {result['measured_gate']['csc_closure_equal']}; current corrected CSC/gate differences: {result['corrected_gate']['current_csc_changes']}.
- Prior replay/summary verification: {result['prior_replay_and_summary_verification']['status']}, {result['prior_replay_and_summary_verification']['runs_verified']} runs, {result['prior_replay_and_summary_verification']['branches_replayed']} accepted branch replays; failures: {result['prior_replay_and_summary_verification']['failures']}.
- Missing required artifacts: {result['missing_required']}; retained fault and cleanup archive checks are individually recorded, including failed validation attempts.
- Forbidden final trust checks: {result['forbidden_trust_checks']}.
- Delivery failures: {result['failures']}.

## Limitations, open questions and next actions

These are byte/inventory/config checks, not physical traffic, hostile containment, OS-wide non-interference or hidden-file surveillance. Prior replay verification does not establish total resource accounting or recovery. The corrected source has local validation but no repeated main performance campaign. Independent reviews retain their methodological scope and open findings. Preserve all raw results; any new performance run requires fresh source/protocol identity and a unique output directory. Trust remains Decision D and learning BLOCKED.
"""
    Path(target).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default=".")
    parser.add_argument("--hardening", default="results/cycle5-validation/post-review-hardening-20261006-v5")
    args = parser.parse_args()
    result = audit(Path(args.repository), args.hardening)
    Path("research/tables/cycle5_delivery_audit.json").write_bytes(canonical(result))
    report(result, "research/evidence/cycle5/cycle5_reproducibility_audit.md")
    print(json.dumps({key: result[key] for key in ("status", "failures", "scheduled_runs", "missing_required", "grid_exact")}, indent=2))
    raise SystemExit(0 if result["status"] == "VERIFIED" else 1)
