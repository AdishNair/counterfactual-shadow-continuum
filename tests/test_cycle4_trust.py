"""Mutations test causal implementation separation; fixtures are not research runs."""
import ast
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from csc.contracts import Config, Event, State, StateCaptureEngine, Anchor
from csc.world import ProductionWorld, ShadowWorldModel, domain_metrics
from experiments import trust_reference as ref
from experiments.trust_selector import select, validate_features


class SourceIsolation(unittest.TestCase):
    def setUp(self):
        self.state=State(queue_ns=20,queue_ew=15,rng_seed=123)
        self.events=[Event(f"e{i}","fixture",i,i,0,1,2,i%2==0) for i in range(6)]
        self.records=[asdict(event) for event in self.events]
        self.config=Config(horizon_ticks=6,production_heterogeneity=False,model_incidents=True)
        self.features=dict(horizon=6,epsilon=1,estimated_improvement=2,divergence=3,
                           capabilities={"incident_semantics":"blocked-ew-v1"},
                           window_metadata={"incident_semantics":"blocked-ew-v1","declared_at_decision":True,"requires_incident":True})
        self.rule=dict(family="DIVERGENCE",d=4,h=None)

    def sem(self):
        model=ShadowWorldModel(self.state,self.config)
        return [model.step(event,"EW_GREEN",tick) for tick,event in enumerate(self.events)]

    def test_reference_import_firewall(self):
        source=Path(ref.__file__).read_text();tree=ast.parse(source)
        imports=[n.module if isinstance(n,ast.ImportFrom) else a.name for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom)) for a in (n.names if isinstance(n,ast.Import) else [None])]
        self.assertEqual(sorted(imports),["copy","random"])
        code="import sys; from experiments import trust_reference; assert not any(x == 'csc' or x.startswith('csc.') for x in sys.modules)"
        subprocess.run([sys.executable,"-c",code],check=True)

    def test_sem_transition_mutation_reference_unchanged(self):
        baseline=ref.simulate(asdict(self.state),"EW_GREEN",self.records,6)
        with patch.object(ShadowWorldModel,"step",return_value={"mutated":True}):
            self.assertEqual(baseline,ref.simulate(asdict(self.state),"EW_GREEN",self.records,6))
            self.assertEqual(self.sem()[0],{"mutated":True})

    def test_production_transition_metric_mutation_reference_unchanged(self):
        baseline=ref.simulate(asdict(self.state),"EW_GREEN",self.records,6)
        with patch.object(ProductionWorld,"step",side_effect=RuntimeError("mutated")),patch("csc.world.domain_metrics",return_value={"mean_queue":999}):
            self.assertEqual(baseline,ref.simulate(asdict(self.state),"EW_GREEN",self.records,6))
            self.assertEqual(ref.value(baseline[1]),-ref.metrics(baseline[1])["mean_queue"])

    def test_reference_transition_and_metric_mutation_sem_unchanged(self):
        baseline=self.sem()
        with patch.object(ref,"simulate",return_value=({},[{"mutated":True}])),patch.object(ref,"metrics",return_value={"mean_queue":999}):
            self.assertEqual(self.sem(),baseline)
            self.assertEqual(ref.simulate({},"EW_GREEN",[],6)[1],[{"mutated":True}])
            self.assertEqual(ref.value([]),-999)

    def test_common_serialization_and_independent_semantics(self):
        before=deepcopy(self.records);anchor=StateCaptureEngine().capture(self.state,"fixture",0)
        recovered=Anchor.from_envelope(json.loads(json.dumps(anchor.envelope())))
        _,trace=ref.simulate(json.loads(recovered.payload)["state"],"EW_GREEN",json.loads(json.dumps(self.records)),6)
        self.assertEqual(trace,self.sem());self.assertEqual(before,self.records)
        self.assertEqual(asdict(self.state),asdict(recovered.hydrate()))
        self.assertEqual(ref.metrics(trace),domain_metrics(trace))

    def test_all_action_authoritative_reference_contract(self):
        for heterogeneous in (False,True):
            for horizon in (2,6,20):
                events=[Event(f"e{i}","fixture",i,i,0,1,2,i%2==0) for i in range(horizon)]
                for action in ("NS_GREEN","EW_GREEN","BALANCED"):
                    config=Config(horizon_ticks=horizon,production_heterogeneity=heterogeneous)
                    capability=object();world=ProductionWorld(self.state,capability,config);world.apply_plan(action,capability,"fixture")
                    actual=[world.step(e,i) for i,e in enumerate(events)]
                    final,trace=ref.simulate(asdict(self.state),action,[asdict(e) for e in events],horizon,2,heterogeneous)
                    self.assertEqual(actual,trace);self.assertEqual(asdict(world.snapshot_state()),final)

    def test_no_oracle_fields_allowed(self):
        for key in ("reference_positive","mismatch","oracle_gain","reference"):
            features=deepcopy(self.features);features[key]=True
            with self.assertRaises(ValueError):select(features,self.rule)

    def test_unknown_late_unsupported_metadata_abstain(self):
        for key,value,status in (("incident_semantics","unknown","UNKNOWN_OR_LATE_SEMANTICS"),("declared_at_decision",False,"UNKNOWN_OR_LATE_SEMANTICS")):
            features=deepcopy(self.features);features["window_metadata"][key]=value
            self.assertEqual(select(features,self.rule),(False,status))
        features=deepcopy(self.features);features["capabilities"]["incident_semantics"]="unsupported"
        self.assertEqual(select(features,self.rule),(False,"UNSUPPORTED_SEMANTICS"))

    def test_misdeclared_capability_unobservable(self):
        # A claimed capability can lie; interface alone cannot discover model mismatch.
        self.assertEqual(select(self.features,self.rule),(True,"AVAILABLE"))
        features=deepcopy(self.features);features["window_metadata"]["incident_semantics"]="misdeclared-v2"
        self.assertFalse(select(features,self.rule)[0])

    def test_inclusive_divergence_strict_gain(self):
        features=deepcopy(self.features);features["divergence"]=4
        self.assertTrue(select(features,self.rule)[0]);features["estimated_improvement"]=1
        self.assertFalse(select(features,self.rule)[0])

    def test_selector_import_firewall(self):
        source=Path("experiments/trust_selector.py").read_text()
        for forbidden in ("trust_reference","csc.world","csc.compare","reference_gain","mismatch_regime"):
            self.assertNotIn(forbidden,source)

    def test_final_generation_blocked_without_selection(self):
        from experiments import cycle4_trust as driver
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/"source-manifest.json").write_text(json.dumps({"files":{},"bundle_digest":"fixture"}))
            gate=root/"gate.json";gate.write_text(json.dumps({"selected_rule":None,"bundle_digest":"fixture","decision":"D"}))
            with patch.object(driver,"ROOT",root):
                with self.assertRaisesRegex(ValueError,"no qualifying"):
                    driver.collect("final-held-out",root/"forbidden",gate)
            self.assertFalse((root/"forbidden").exists())

    def test_final_analysis_blocked_before_read_without_selection(self):
        from experiments import analyze_cycle4_trust as analysis
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);series=root/"series";series.mkdir()
            (series/"manifest.json").write_text(json.dumps({"phase":"final-held-out","bundle_digest":"fixture"}))
            gate=root/"gate.json";gate.write_text(json.dumps({"selected_rule":None,"bundle_digest":"fixture","decision":"D"}))
            with patch.object(analysis,"observations",side_effect=AssertionError("forbidden outcome read")):
                with self.assertRaisesRegex(ValueError,"invalid final gate"):
                    analysis.analyze(series,root/"output",gate)
            self.assertFalse((root/"output").exists())

    def test_final_baseline_coverage_and_fpr_checks_independent(self):
        from experiments.analyze_cycle4_trust import final_cell_check
        baseline=dict(median_coverage=.75,median_false_positive_rate=.02)
        coverage_failure=final_cell_check(dict(median_coverage=.5,median_false_positive_rate=.01),baseline)
        self.assertEqual(coverage_failure,dict(baseline_fpr_not_worse=True,baseline_coverage_80pct=False))
        fpr_failure=final_cell_check(dict(median_coverage=.75,median_false_positive_rate=.03),baseline)
        self.assertEqual(fpr_failure,dict(baseline_fpr_not_worse=False,baseline_coverage_80pct=True))

    def test_final_uses_frozen_rule_never_recalibrates(self):
        from experiments import analyze_cycle4_trust as analysis
        from experiments.cycle4_trust import sha
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);series=root/"series";series.mkdir()
            rule=dict(id="frozen-fixture",family="DIVERGENCE",d=4,h=None,q=.5,duplicate_of=None)
            baseline=dict(id="baseline",family="BASELINE",d=None,h=None,q=None,duplicate_of=None)
            gate=root/"gate.json";gate.write_text(json.dumps(dict(selected_rule=rule,bundle_digest="fixture",decision="QUALIFIED_FOR_FINAL_ONLY",candidates=[dict(rule=baseline),dict(rule=rule)])))
            (series/"manifest.json").write_text(json.dumps(dict(phase="final-held-out",bundle_digest="fixture",prerequisite_hash=sha(gate))))
            (series/"frozen-design.json").write_text("{}")
            row=dict(run_id="fixture",seed=999,horizon=6,demand="light",incident="none",mismatch="fixture",features=self.features,
                     feature_status="AVAILABLE",reference_positive=True,any_reference_positive=True,selected_action="EW_GREEN",
                     epsilon_coverage=True,ranking_agreement=True,regret_sign_agreement=True,choice_value_loss=0,selected_error=0)
            with patch.object(analysis,"observations",return_value=[deepcopy(row) for _ in range(8)]),patch.object(analysis,"candidates",side_effect=AssertionError("final recalibration forbidden")):
                analysis.analyze(series,root/"output",gate)
            result=json.loads((root/"output/final-decision.json").read_text())
            self.assertEqual(result["selected_rule"],rule)
            self.assertEqual(result["decision"],"D") # only one fixture cell, never 60.


if __name__=="__main__":unittest.main()
