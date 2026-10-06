"""Hash, split, factor, trace and analysis reproducibility verification."""
import argparse
from collections import Counter
import itertools
import json
from pathlib import Path

from csc.contracts import Anchor, Config, Event
from csc.world import ShadowWorldModel, domain_metrics
from experiments import trust_reference
from experiments.cycle4_trust import hashed, lines, sha, write
from experiments.trust_selector import validate_features


def verify(series, replay=True, analysis=None):
    series=Path(series);manifest=json.loads((series/"manifest.json").read_text());design=json.loads((series/"frozen-design.json").read_text())
    errors=[];counts=Counter();run_ids=set();conditions=[]
    for name,digest in manifest["artifacts"].items():
        if sha(series/name)!=digest:errors.append("hash:"+name)
    source=json.loads((series/"source/source-manifest.json").read_text())
    if hashed(source["files"])!=manifest["bundle_digest"]:errors.append("bundle_digest")
    for name,digest in source["files"].items():
        if sha(series/"source"/name)!=digest:errors.append("source:"+name)
    for path in sorted(series.glob("run-*.jsonl")):
        rows=lines(path);first=rows[0];condition={key:first[key] for key in ("seed","horizon","demand","incident","mismatch")};conditions.append(condition)
        if first["run_id"] in run_ids:errors.append("duplicate_run:"+first["run_id"])
        run_ids.add(first["run_id"])
        if len(rows)!=8 or sorted(row["anchor_index"] for row in rows)!=list(range(8)):errors.append("anchor_count:"+first["run_id"])
        counts["runs"]+=1;counts["anchors"]+=len(rows)
        for row in rows:
            anchor=Anchor.from_envelope(row["anchor"]);state=anchor.hydrate()
            if hashed(row["events"])!=row["input_hash"]:errors.append("input_hash")
            if validate_features(row["features"])!=row["feature_status"]:errors.append("feature_status")
            counts["feature_"+row["feature_status"]]+=1
            if not replay:continue
            config=Config(**row["config"])
            for action,outcome in row["reference"].items():
                _,trace=trust_reference.simulate(json.loads(anchor.payload)["state"],action,row["events"],row["horizon"],design["production_rate"],config.production_heterogeneity)
                if trace!=outcome["trace"] or trust_reference.value(trace)!=outcome["utility"] or trust_reference.metrics(trace)!=outcome["metrics"]:errors.append("reference_replay")
                model=ShadowWorldModel(state,config);sem_trace=[model.step(Event(**event),action,tick) for tick,event in enumerate(row["events"])]
                if sem_trace!=row["sem"][action]["trace"] or -domain_metrics(sem_trace)["mean_queue"]!=row["sem"][action]["utility"]:errors.append("sem_replay")
                counts["replayed_action_pairs"]+=1
            mirror=row["sem"][row["production_action"]];selected=row["sem"][row["selected_action"]]
            divergence=sum(((a["queue_ns"]-m["queue_ns"])**2+(a["queue_ew"]-m["queue_ew"])**2)**.5 for a,m in zip(selected["trace"],mirror["trace"]))
            if divergence!=row["features"]["divergence"] or abs(mirror["utility"]-row["production_utility"])!=row["features"]["epsilon"]:errors.append("feature_replay")
    low,high=design["splits"][manifest["phase"]]
    expected=set(itertools.product(range(low,high+1),design["horizons"],design["demand"],design["incident"],design["mismatch"]))
    actual=set(tuple(row[key] for key in ("seed","horizon","demand","incident","mismatch")) for row in conditions)
    if expected!=actual:errors.append("factorial_coverage")
    planned=json.loads((series/"planned-conditions.json").read_text())
    if conditions!=planned:errors.append("saved_order")
    seed_sets=[set(range(a,b+1)) for a,b in design["splits"].values()]
    if any(a&b for i,a in enumerate(seed_sets) for b in seed_sets[i+1:]):errors.append("split_overlap")
    analysis_checks=0
    if analysis:
        from experiments.analyze_cycle4_trust import candidates, reduce_runs, cells, observations
        report=json.loads((Path(analysis)/"calibration-selection.json").read_text());raw=observations(series)
        regenerated=candidates(raw)
        if [x["rule"] for x in report["candidates"]]!=regenerated:errors.append("candidate_regeneration")
        for candidate in report["candidates"]:
            passing=sum(cell["passed"] for cell in cells(reduce_runs(raw,candidate["rule"])))
            if passing!=candidate["passing_cells"]:errors.append("cell_summary_regeneration")
            analysis_checks+=1
    return dict(passed=not errors,phase=manifest["phase"],counts=dict(counts),expected_runs=1200,expected_cells=60,
                seed_range=[low,high],split_overlap=False,errors=dict(Counter(errors)),bundle_digest=manifest["bundle_digest"],
                analysis_candidate_checks=analysis_checks,heldout_access_audit="runner gating plus absence of final series; external reads not independently auditable")


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("series");parser.add_argument("--output",required=True);parser.add_argument("--analysis");args=parser.parse_args()
    result=verify(args.series,analysis=args.analysis);write(args.output,result);print(json.dumps(result))
