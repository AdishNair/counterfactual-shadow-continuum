"""Meaningful integrity/reduction regressions; no performance campaign."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from csc.contracts import Config
from experiments.cycle6_analyze import ScalarStore, analyze_run, canonical, json_lines, memory_trend, strict_json, write_figure
from experiments.cycle6_verify import assert_equal, frozen_registry, ordered_coverage, replay_run, verify_authority_and_evidence, verify_bounds, verify_registry, verify_run


def metadata():
    rows = frozen_registry()
    configs = {}
    for row in rows:
        k = 0 if row["mode"] == "k0" else int(row["mode"][-1])
        duration, warmup = ((10000, 500) if row["kind"] == "continuous" else
                            (200, 20) if row["kind"] == "storage_fault" else (500, 50))
        config = Config(experiment_name="cycle6-gate-a", random_seed=row["seed"], duration_epochs=duration,
                        warmup_epochs=warmup, horizon_ticks=6, shadow_count=k, mirror_count=int(k > 0),
                        execution_mode="asynchronous", production_period_s=.04, shadow_timeout_s=2.,
                        shadow_result_deadline_s=.3, max_shadow_slots=1 if row["condition"] == "capacity1" else 3,
                        max_pending_shadow_tasks=1 if row["condition"] == "capacity1" else 12,
                        max_pending_epochs=16, shadow_injected_delay_s=row["delay_s"], worker_mode="warm" if k else "cold")
        configs[row["run_id"]] = asdict(config)
    return {"registry": rows, "registry_sha256": hashlib.sha256(canonical(rows)).hexdigest(),
            "configs": configs, "config_hashes": {key: hashlib.sha256(canonical(value)).hexdigest() for key, value in configs.items()}}


class Cycle6IntegrityTests(unittest.TestCase):
    def test_disposable_smoke_registry_is_explicitly_non_evidentiary(self):
        from experiments.cycle6_campaign import configuration, registry
        base = registry()[0]
        rows = [dict(base, run_id="smoke-normal", mode="warm2", condition="normal", load="normal", delay_s=0.),
                dict(base, run_id="smoke-storage", mode="warm1", condition="storage", load="storage", delay_s=0.),
                dict(base, run_id="smoke-torn", kind="storage_fault", mode="warm2", condition="torn", load="normal", delay_s=0., fault="torn")]
        configs = {row["run_id"]: asdict(configuration(row, smoke=True)) for row in rows}
        meta = {"smoke": True, "registry": rows,
                "registry_sha256": hashlib.sha256(canonical(rows)).hexdigest(),
                "configs": configs,
                "config_hashes": {key: hashlib.sha256(canonical(value)).hexdigest()
                                  for key, value in configs.items()}}
        self.assertEqual(verify_registry(meta)["registry_identity"],
                         "VERIFIED_NON_EVIDENTIARY_SMOKE")

    def test_exact_registry_independent_builder(self):
        meta = metadata()
        report = verify_registry(meta)
        self.assertEqual(report["factor_counts"], {"factorial": 54, "storage_fault": 15, "continuous": 1})
        from experiments.cycle6_campaign import registry
        self.assertEqual(meta["registry"], registry())

    def test_wrong_factor_even_rehashed_rejected(self):
        meta = metadata()
        meta["registry"][0]["delay_s"] = .9
        meta["registry_sha256"] = hashlib.sha256(canonical(meta["registry"])).hexdigest()
        with self.assertRaisesRegex(ValueError, "exact preregistered"):
            verify_registry(meta)

    def test_k0_does_not_hydrate_unused_warm_workers(self):
        meta = metadata()
        row = next(row for row in meta["registry"] if row["mode"] == "k0")
        self.assertEqual(meta["configs"][row["run_id"]]["worker_mode"], "cold")
        from experiments.cycle6_campaign import configuration
        self.assertEqual(configuration(row).worker_mode, "cold")

    def test_duplicate_identity_rejected(self):
        meta = metadata()
        meta["registry"][-1] = meta["registry"][0]
        with self.assertRaises(ValueError):
            verify_registry(meta)

    def test_deadline_change_even_rehashed_rejected(self):
        meta = metadata()
        run_id = meta["registry"][0]["run_id"]
        meta["configs"][run_id]["shadow_result_deadline_s"] = 3.
        meta["config_hashes"][run_id] = hashlib.sha256(canonical(meta["configs"][run_id])).hexdigest()
        with self.assertRaisesRegex(ValueError, "factor/config"):
            verify_registry(meta)

    def test_json_rejects_duplicate_and_nonfinite(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e309}'):
            with self.assertRaises(ValueError):
                strict_json(raw)

    def test_torn_and_oversized_jsonl_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "records.jsonl"
            path.write_bytes(b'{"epoch":0}')
            with self.assertRaisesRegex(ValueError, "torn"):
                list(json_lines(path))
            path.write_bytes(b'{"epoch":0}\n')
            with self.assertRaisesRegex(ValueError, "oversized"):
                list(json_lines(path, max_line_bytes=5))

    def test_epoch_gap_and_duplicate_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "journal.jsonl"
            for epochs in ([0, 2], [0, 0], [0]):
                path.write_bytes(b"".join(canonical({"epoch": epoch}) + b"\n" for epoch in epochs))
                with self.assertRaises(ValueError):
                    ordered_coverage(path, 3)

    def test_physical_and_spool_bounds_fail_separately(self):
        config = asdict(Config())
        state = {key: 0 for key in ("physical_queue_depth", "physical_inflight_tasks", "physical_high_water_queue_depth",
            "physical_high_water_inflight_tasks", "physical_queue_bytes", "physical_inflight_bytes",
            "physical_high_water_queue_bytes", "physical_high_water_inflight_bytes", "physical_running_tasks",
            "physical_running_bytes", "evidence_spool_items", "evidence_spool_high_water_items", "evidence_spool_bytes",
            "evidence_spool_high_water_bytes", "pending_epochs", "retained_completed_epochs", "duplicate_cache_size")}
        state.update(physical_task_capacity=config["max_pending_shadow_tasks"], physical_byte_capacity=config["max_pending_shadow_bytes"])
        verify_bounds(state, config)
        for key, limit in (("physical_inflight_bytes", config["max_pending_shadow_bytes"]),
                           ("evidence_spool_high_water_bytes", config["evidence_spool_max_bytes"]),
                           ("physical_high_water_queue_depth", config["max_pending_shadow_tasks"])):
            with self.assertRaises(ValueError):
                verify_bounds(dict(state, **{key: limit + 1}), config)

    def test_summary_mismatch(self):
        with self.assertRaisesRegex(ValueError, "numeric mismatch"):
            assert_equal({"timing": {"p99": 9.}}, {"timing": {"p99": 8.}})


class Cycle6ReductionTests(unittest.TestCase):
    def test_exact_external_quantiles(self):
        store = ScalarStore()
        try:
            for index, value in enumerate((4, 1, None, 9, 2)):
                store.add("x", index, value)
            result = store.distribution("x")
            self.assertEqual(result["n"], 4)
            for key, expected in (("p50", 3), ("p90", 7.5), ("p95", 8.25), ("p99", 8.85), ("max", 9)):
                self.assertAlmostEqual(result[key], expected)
            self.assertEqual(store.quantile("x", .5, 3), 5.5)
        finally:
            store.close()

    def test_frozen_trends_detect_growth_and_plateau(self):
        store = ScalarStore()
        try:
            for epoch in range(100):
                store.add("growing", epoch, 1000000 + 200 * epoch)
                store.add("flat", epoch, 1000000)
            growth = memory_trend(store, "growing", 0, 100, 104.8576, 1048576)
            flat = memory_trend(store, "flat", 0, 100, 104.8576, 1048576)
            self.assertEqual(growth["classification"], "positive trend remains")
            self.assertEqual(growth["ols_slope"], 200)
            self.assertEqual(growth["theil_sen_slope"], 200)
            self.assertEqual(growth["theil_sen_subsample_n"], 5)
            self.assertEqual(flat["classification"], "supports a plateau at study resolution")
        finally:
            store.close()

    def test_missing_memory_samples_do_not_pass_plateau(self):
        store = ScalarStore()
        try:
            for epoch in range(99):
                store.add("flat", epoch, 1000000)
            result = memory_trend(store, "flat", 0, 100, 104.8576, 1048576)
            self.assertEqual(result["classification"], "inconclusive")
            self.assertFalse(result["complete_sample_coverage"])
        finally:
            store.close()

    def test_optional_cfr_loss_preserves_original_evidence_denominator(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            config = asdict(Config(duration_epochs=4, warmup_epochs=1))
            (path / "manifest.json").write_bytes(canonical({"experiment_id": "fixture", "status": "COMPLETE", "config": config, "config_hash": "fixture"}))
            journal, lifecycle, resources = [], [], []
            for epoch in range(4):
                journal.append({"epoch": epoch, "committed_monotonic_s": epoch, "branches": []})
                lifecycle.append({"epoch": epoch, "status": "FINALIZED", "evidence_completeness":
                    "COMPLETE_COMPARISON" if epoch != 2 else "MIRROR_COMPLETE",
                    "requested_k": 2, "admitted_k": 2, "completed_k": 2 if epoch != 2 else 0,
                    "mirror_accepted": True, "comparison_completion_ms": 5.})
                resources.append({"epoch": epoch, "production_interval_ms": 45. if epoch else None,
                                  "coordinator_rss_bytes": 1000000, "coordinator_python_current_bytes": 10000})
            for name, rows in (("epoch_journal.jsonl", journal), ("lifecycle.jsonl", lifecycle), ("resource_metrics.jsonl", resources)):
                (path / name).write_bytes(b"".join(canonical(row) + b"\n" for row in rows))
            report = analyze_run(path)
            self.assertEqual(report["evidence"]["complete_fraction"], 2 / 3)
            self.assertEqual(report["evidence"]["partial_fraction"], 1 / 3)
            self.assertEqual(report["evidence"]["persisted_cfr_fraction"], 0)
            self.assertEqual(report["evidence"]["mirror_availability_fraction"], 1)
            self.assertEqual(report["cadence_ms"]["missed_intervals_above_44ms"], 3)

    def test_durable_completeness_requires_every_original_branch_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            config = asdict(Config(duration_epochs=3, warmup_epochs=1))
            (path / "manifest.json").write_bytes(canonical({"experiment_id": "durable-fixture", "status": "COMPLETE", "config": config, "config_hash": "fixture"}))
            journal, lifecycle, delivery = [], [], []
            for epoch in range(3):
                journal.append({"epoch": epoch, "committed_monotonic_s": epoch, "branches":
                    [{"branch_id": f"{epoch}-{role}", "role": "MIRROR" if role == "m" else "SHADOW"} for role in ("m", "a", "b")]})
                lifecycle.append({"epoch": epoch, "status": "FINALIZED", "evidence_completeness": "COMPLETE_COMPARISON",
                                  "requested_k": 2, "admitted_k": 2, "completed_k": 2, "mirror_accepted": True})
                for suffix in ("comparison", f"branch:{epoch}-m", f"branch:{epoch}-a", f"branch:{epoch}-b"):
                    delivery.append({"record_id": f"epoch:{epoch}:{suffix}", "status": "FAILED" if epoch == 2 and suffix.endswith("-m") else "PERSISTED", "persistence_latency_ms": 12.})
            for name, rows in (("epoch_journal.jsonl", journal), ("lifecycle.jsonl", lifecycle), ("resource_metrics.jsonl", [{"epoch": i} for i in range(3)]), ("evidence_delivery.jsonl", delivery)):
                (path / name).write_bytes(b"".join(canonical(row) + b"\n" for row in rows))
            report = analyze_run(path)
            self.assertEqual(report["evidence"]["complete_fraction"], 1)
            self.assertEqual(report["evidence"]["durably_complete_fraction"], .5)
            self.assertEqual(report["evidence"]["durable_complete_availability_ms"]["p50"], 12)

    def test_short_native_run_summary_authority_and_replay(self):
        from csc.runner import run
        from experiments.cycle6_analyze import file_hash
        with tempfile.TemporaryDirectory() as temporary:
            config = Config(duration_epochs=3, warmup_epochs=1, shadow_count=1, mirror_count=1,
                            execution_mode="asynchronous", worker_mode="warm", max_shadow_slots=2,
                            production_period_s=.04, shadow_result_deadline_s=.3)
            path, _ = run(config, temporary, "cycle6-unit-integration")
            manifest = strict_json((path / "manifest.json").read_bytes())
            checked = verify_run(path, asdict(config), manifest["config_hash"], manifest["source_hashes"])
            self.assertEqual(checked["production_epochs"], 3)
            replay = replay_run(path, Path(__file__).resolve().parent.parent)
            self.assertGreaterEqual(replay["branches_replayed"], 3)
            self.assertEqual(replay["trajectory_mismatches"], 0)
            audit_path = path / "environment_audit.jsonl"
            rows = list(json_lines(audit_path))
            rows[0]["action"] = "unauthorized"
            audit_path.write_bytes(b"".join(canonical(row) + b"\n" for row in rows))
            with self.assertRaisesRegex(ValueError, "unauthorized"):
                verify_authority_and_evidence(path, asdict(config))

    def test_deterministic_svg(self):
        with tempfile.TemporaryDirectory() as temporary:
            one, two = Path(temporary) / "one.svg", Path(temporary) / "two.svg"
            rows = [{"run_id": "<escaped>", "cadence_ms": {"p99": 55}, "evidence": {"complete_fraction": .3}}]
            write_figure(rows, one)
            write_figure(rows, two)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            self.assertIn("&lt;escaped&gt;", one.read_text())


if __name__ == "__main__":
    unittest.main()
