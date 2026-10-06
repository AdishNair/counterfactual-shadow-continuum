from dataclasses import asdict, replace
import json
import tempfile
import time
import unittest

from csc.branches import MultiBranchScheduler, execute_shadow
from csc.compare import RegretCalculator
from csc.contracts import Anchor, Branch, Config, State, StateCaptureEngine
from csc.runner import run
from csc.safety import ActuatorGateway, TokenIssuer, VirtualActuator
from csc.sync import InputSynchronizationLayer
from csc.world import ProductionWorld, workload


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.config = Config(duration_epochs=3, warmup_epochs=0, horizon_ticks=4)
        self.anchor = StateCaptureEngine().capture(State(), "test", 0)
        self.branches = MultiBranchScheduler().plan(self.anchor, self.config, "test", 0, "NS_GREEN")
        self.events = list(workload(self.config, "test"))[:4]

    def request(self, branch=None, config=None, fault="none"):
        return {"anchor": self.anchor.envelope(), "branch": asdict(branch or self.branches[1]),
                "events": [asdict(e) for e in self.events], "config": asdict(config or self.config), "fault": fault}

    def test_anchor_integrity_and_isolation(self):
        state = self.anchor.hydrate()
        state.queue_ns = 999
        state.policy_context["version"] = "evil"
        self.assertEqual(self.anchor.hydrate().queue_ns, 14)
        self.assertEqual(self.anchor.hydrate().policy_context["version"], "heuristic-v1")
        with self.assertRaises(ValueError):
            Anchor(self.anchor.snapshot_id, self.anchor.payload + b" ").hydrate()

    def test_version_validation(self):
        with self.assertRaises(ValueError):
            State(schema_version=2).validate()
        with self.assertRaises(ValueError):
            Config(shadow_count=3).validate()
        with self.assertRaises(ValueError):
            Config(learning_enabled=True).validate()

    def test_distinct_alternatives_and_mirror(self):
        self.assertEqual(len(self.branches), 4)
        self.assertEqual(self.branches[0].action, self.branches[1].action)
        self.assertEqual(len({b.action for b in self.branches if b.role != "MIRROR"}), 3)

    def test_order_repair_and_missing_window(self):
        sync = InputSynchronizationLayer()
        for fault in ("duplicate", "reorder"):
            _, metrics = sync.deliver(self.events, self.branches[1], True, fault)
            self.assertTrue(metrics["comparable"])
        _, metrics = sync.deliver(self.events, self.branches[1], True, "drop")
        self.assertFalse(metrics["comparable"])
        self.assertEqual(metrics["missing_events"], 1)
        _, metrics = sync.deliver(self.events, self.branches[1], False, "reorder")
        self.assertFalse(metrics["comparable"])

    def test_determinism_same_action_and_alternative(self):
        first = execute_shadow(self.request())
        second = execute_shadow(self.request())
        self.assertEqual(first["trace"], second["trace"])
        self.assertEqual(first["final_state"], second["final_state"])
        alternative = execute_shadow(self.request(self.branches[2]))
        self.assertNotEqual(first["trace"], alternative["trace"])
        self.assertEqual(first["synchronization"]["input_hash"], alternative["synchronization"]["input_hash"])

    def test_refuse_production_identity_in_shadow_runtime(self):
        with self.assertRaises(PermissionError):
            execute_shadow(self.request(self.branches[0]))

    def test_regret_signed_discounted_unavailable(self):
        self.assertEqual(RegretCalculator.calculate(-10, [-8], 3)["regret_discounted"], 0)
        self.assertEqual(RegretCalculator.calculate(-10, [-12], 0)["regret_signed"], -2)
        self.assertIsNone(RegretCalculator.calculate(-10, [], None)["regret_raw"])
        self.assertIsNone(RegretCalculator.calculate(-10, [-8], None)["regret_discounted"])

    def test_gateway_hostile_requests_and_interlock(self):
        issuer, capability = TokenIssuer(), object()
        world = ProductionWorld(State(), capability, self.config)
        gateway = ActuatorGateway(issuer, world, capability, "test")
        production = self.branches[0]
        gateway.open_epoch(0, production.branch_id)
        hostile = [None, "", "garbage", "ab.nope", issuer.issue(self.branches[1], time.time() + 60),
                   issuer.issue(self.branches[2], time.time() + 60), issuer.issue(production, time.time() - 1),
                   issuer.issue(replace(production, epoch=1), time.time() + 60),
                   issuer.issue(replace(production, experiment_id="other"), time.time() + 60)]
        token = issuer.issue(self.branches[1], time.time() + 60)
        payload, signature = token.split(".")
        claims = json.loads(bytes.fromhex(payload))
        claims["role"] = "PRODUCTION"
        hostile.append(json.dumps(claims).encode().hex() + "." + signature)
        for token in hostile:
            with self.subTest(token=token):
                with self.assertRaises(PermissionError):
                    gateway.actuate(token, "NS_GREEN")
                self.assertEqual(world.audit, [])
        valid = issuer.issue(production, time.time() + 60)
        with self.assertRaises(PermissionError):
            gateway.actuate(valid, "EW_GREEN")
        gateway.actuate(valid, "NS_GREEN")
        with self.assertRaises(PermissionError):
            gateway.actuate(valid, "NS_GREEN")
        self.assertEqual(len(world.audit), 1)
        gateway.open_epoch(1, "next-production")
        with self.assertRaises(PermissionError):
            gateway.actuate(valid, "NS_GREEN")

    def test_shadow_direct_state_mutation_denied(self):
        world = ProductionWorld(State(), object(), self.config)
        before = asdict(world.snapshot_state())
        with self.assertRaises(PermissionError):
            world.apply_plan("EW_GREEN", object(), "forged")
        self.assertEqual(before, asdict(world.snapshot_state()))
        self.assertEqual(world.audit, [])
        virtual = VirtualActuator(self.branches[1], 1)
        virtual.actuate("EW_GREEN", 0)
        self.assertEqual(world.audit, [])
        with self.assertRaises(ValueError):
            virtual.actuate("EW_GREEN", 1)

    def test_full_run_replay_and_failure_isolation(self):
        with tempfile.TemporaryDirectory() as root:
            _, baseline = run(replace(self.config, shadow_count=0, mirror_count=0), root, "baseline")
            path, csc = run(self.config, root, "csc")
            _, replay = run(self.config, root, "replay")
            _, failed = run(replace(self.config, failure_scenario="crash", failure_epoch=1), root, "crash")
            self.assertEqual(baseline["production_semantic_sha256"], csc["production_semantic_sha256"])
            self.assertEqual(csc["production_semantic_sha256"], replay["production_semantic_sha256"])
            self.assertEqual(csc["production_semantic_sha256"], failed["production_semantic_sha256"])
            self.assertEqual(baseline["workload_sha256"], csc["workload_sha256"])
            self.assertEqual(failed["excluded_branches"], 1)
            self.assertTrue((path / "manifest.json").exists())
            self.assertEqual(json.loads((path / "manifest.json").read_text())["status"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
