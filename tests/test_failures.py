from dataclasses import asdict, replace
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from csc.contracts import Config, canonical
from csc.runner import run
from csc.service import ShadowServer


class FailureTests(unittest.TestCase):
    def test_failure_matrix_preserves_production(self):
        config = Config(duration_epochs=2, warmup_epochs=0, failure_epoch=0, horizon_ticks=3, shadow_timeout_s=1)
        with tempfile.TemporaryDirectory() as root:
            _, baseline = run(replace(config, shadow_count=0, mirror_count=0), root, "baseline")
            for fault in ("drop", "duplicate", "reorder", "delay", "model_error", "timeout", "resource_budget", "capture"):
                with self.subTest(fault=fault):
                    _, result = run(replace(config, failure_scenario=fault), root, fault)
                    self.assertEqual(result["production_semantic_sha256"], baseline["production_semantic_sha256"])
                    self.assertEqual(result["unauthorized_production_mutations_from_shadow"], 0)
                    if fault in ("drop", "model_error", "timeout"):
                        self.assertGreaterEqual(result["excluded_branches"], 1)

    def test_no_mirror_does_not_invent_fidelity(self):
        with tempfile.TemporaryDirectory() as root:
            path, _ = run(Config(duration_epochs=1, warmup_epochs=0, mirror_count=0), root)
            record = json.loads((path / "cfr.jsonl").read_text())
            self.assertIsNone(record["epsilon"])
            self.assertIsNone(record["regret_discounted"])

    def test_independent_models_exact_control_and_biased_model(self):
        config = Config(duration_epochs=2, warmup_epochs=0, production_heterogeneity=False)
        with tempfile.TemporaryDirectory() as root:
            _, exact = run(config, root, "exact")
            _, biased = run(replace(config, shadow_service_rate=4), root, "biased")
            self.assertEqual(exact["fidelity_gap"]["median"], 0)
            self.assertGreater(biased["fidelity_gap"]["median"], 0)

    def test_http_backend_and_denied_mutation(self):
        server = ShadowServer(("127.0.0.1", 0), timeout=2)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            with tempfile.TemporaryDirectory() as root:
                config = Config(duration_epochs=2, warmup_epochs=0, backend="http", remote_shadow_urls=[url], shadow_count=1)
                _, result = run(config, root)
                self.assertEqual(result["excluded_branches"], 0)
                self.assertEqual(result["complete_fraction"], 1)
            request = urllib.request.Request(url + "/v1/actuate", b"{}", {"Content-Type": "application/json"})
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request)
            self.assertEqual(caught.exception.code, 403)
            caught.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
