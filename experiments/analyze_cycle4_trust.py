"""Deterministic seed-unit statistics for the frozen trust study, no selectors added."""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import csv
import json
import math
from pathlib import Path
import random
from statistics import median

from experiments.cycle4_trust import hashed, lines, sha, write
from experiments.trust_selector import select

CELL = ("horizon", "demand", "incident", "mismatch")
METRICS = ("coverage", "precision", "false_positive_rate", "false_negative_rate", "abstention", "epsilon_coverage", "ranking_agreement", "regret_sign_agreement", "choice_value_loss", "oracle_coverage", "oracle_coverage_lost", "selected_error")


def observations(series):
    return [row for path in sorted(Path(series).glob("run-*.jsonl")) for row in lines(path)]


def summary(rows, rule):
    accepted = [select(row["features"], rule)[0] for row in rows]
    recommended = sum(accepted)
    true = sum(chosen and row["reference_positive"] for row, chosen in zip(rows, accepted))
    false = recommended - true
    ref_negative = sum(not row["reference_positive"] for row in rows)
    any_positive = sum(row["any_reference_positive"] for row in rows)
    false_negative = sum(not chosen and row["any_reference_positive"] for row, chosen in zip(rows, accepted))
    first = rows[0]
    return dict(run_id=first["run_id"], **{key:first[key] for key in ("seed",)+CELL}, eligible=len(rows), selected=recommended,
                coverage=recommended/len(rows), precision=true/recommended if recommended else None,
                false_positive_rate=false/ref_negative if ref_negative else None,
                false_negative_rate=false_negative/any_positive if any_positive else None,
                abstention=1-recommended/len(rows), tp=true,fp=false,fn=false_negative,
                reference_negative=ref_negative,oracle_positive=any_positive,
                unavailable=sum(row["feature_status"]!="AVAILABLE" for row in rows), incomplete=8-len(rows),
                epsilon_coverage=sum(row["epsilon_coverage"] for row in rows)/len(rows),
                trusted_epsilon_coverage=sum(chosen and row["epsilon_coverage"] for row,chosen in zip(rows,accepted))/recommended if recommended else None,
                ranking_agreement=sum(row["ranking_agreement"] for row in rows)/len(rows),
                regret_sign_agreement=sum(row["regret_sign_agreement"] for row in rows)/len(rows),
                choice_value_loss=sum(row["choice_value_loss"] for row in rows)/len(rows),
                oracle_coverage=any_positive/len(rows),oracle_coverage_lost=false_negative/len(rows),
                selected_error=sum(row["selected_error"] for row in rows)/len(rows),
                accepted_actions=dict(Counter(row["selected_action"] for row, chosen in zip(rows,accepted) if chosen)))


def reduce_runs(rows, rule):
    groups=defaultdict(list)
    for row in rows:
        groups[row["run_id"]].append(row)
    return [summary(values,rule) for _,values in sorted(groups.items())]


def values(runs,metric):
    return [row[metric] if row[metric] is not None else 0 for row in runs]


def bootstrap(vector, identity, iterations=1000):
    rng=random.Random("trust-bootstrap-v1:"+str(identity))
    boot=sorted(median([vector[rng.randrange(len(vector))] for _ in vector]) for _ in range(iterations))
    return [boot[24],boot[974]]


def cells(runs, intervals=False):
    groups=defaultdict(list)
    for row in runs:
        groups[tuple(row[key] for key in CELL)].append(row)
    output=[]
    for identity,group in sorted(groups.items()):
        result=dict(zip(CELL,identity))
        result.update(runs=len(group),undefined_precision=sum(row["precision"] is None for row in group),
                      undefined_fpr=sum(row["false_positive_rate"] is None for row in group),
                      undefined_fnr=sum(row["false_negative_rate"] is None for row in group),
                      recommending_runs=sum(row["selected"]>0 for row in group), median_recommendations=median([row["selected"] for row in group]))
        for metric in METRICS:
            result["median_"+metric]=median(values(group,metric))
            if intervals:
                result[metric+"_seed_bootstrap_95"]=bootstrap(values(group,metric),str(identity)+metric)
        reasons=[]
        checks={"undefined_precision":result["undefined_precision"]==0,"recommendations":result["median_recommendations"]>=2,
                "recommending_runs":result["recommending_runs"]>=12,"coverage":result["median_coverage"]>=.25,
                "precision":result["median_precision"]>=.95,"fpr":result["median_false_positive_rate"]<=.05,
                "abstention":result["median_abstention"]<.75}
        reasons=[key for key,passed in checks.items() if not passed]
        result.update(passed=not reasons,failure_reasons=reasons)
        output.append(result)
    return output


def candidates(rows):
    divergences=sorted(row["features"]["divergence"] for row in rows)
    if not divergences:
        return []
    rules=[dict(id="baseline",family="BASELINE",d=None,h=None,q=None)]
    for q in (.25,.5,.75,1):
        d=divergences[math.ceil(q*len(divergences))-1]
        rules.append(dict(id=f"divergence-q{q}",family="DIVERGENCE",d=d,h=None,q=q))
        rules.extend(dict(id=f"divergence-horizon-q{q}-h{h}",family="DIVERGENCE_HORIZON",d=d,h=h,q=q) for h in (2,6,20))
    masks={}
    for rule in rules:
        mask=tuple(select(row["features"],rule)[0] for row in rows)
        rule["duplicate_of"]=masks.get(mask)
        rule["baseline_equivalent"]=mask==tuple(select(row["features"],rules[0])[0] for row in rows)
        if mask not in masks:
            masks[mask]=rule["id"]
    return rules


def global_summary(runs, raw, rule):
    n=sum(row["eligible"] for row in runs); selected=sum(row["selected"] for row in runs);tp=sum(row["tp"] for row in runs)
    per_seed=defaultdict(list)
    for row in runs:
        per_seed[row["seed"]].append(row)
    seed_rows=[dict(seed=seed,coverage=sum(row["selected"] for row in group)/sum(row["eligible"] for row in group),
                    precision=sum(row["tp"] for row in group)/sum(row["selected"] for row in group) if sum(row["selected"] for row in group) else 0,
                    abstention=1-sum(row["selected"] for row in group)/sum(row["eligible"] for row in group)) for seed,group in sorted(per_seed.items())]
    return dict(eligible=n,selected=selected,coverage=selected/n,precision=tp/selected if selected else None,
                abstention=1-selected/n,fp=sum(row["fp"] for row in runs),unavailable=sum(row["unavailable"] for row in runs),
                undefined_precision_runs=sum(row["precision"] is None for row in runs),
                false_positive_rate=sum(row["fp"] for row in runs)/sum(row["reference_negative"] for row in runs) if sum(row["reference_negative"] for row in runs) else None,
                false_negative_rate=sum(row["fn"] for row in runs)/sum(row["oracle_positive"] for row in runs) if sum(row["oracle_positive"] for row in runs) else None,
                trusted_epsilon_coverage=sum((row["trusted_epsilon_coverage"] or 0)*row["selected"] for row in runs)/selected if selected else None,
                accepted_actions=dict(sum((Counter(row["accepted_actions"]) for row in runs),Counter())),
                median_run_metrics={metric:median(values(runs,metric)) for metric in METRICS},
                seed_distribution=seed_rows,seed_bootstrap={metric:bootstrap([row[metric] for row in seed_rows],rule["id"]+metric) for metric in ("coverage","precision","abstention")})


def csv_write(path, rows):
    if not rows:return
    with Path(path).open("x",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(key for row in rows for key in row)));writer.writeheader()
        writer.writerows({key:json.dumps(value) if isinstance(value,(list,dict)) else value for key,value in row.items()} for row in rows)


def controls(rows,rule, design):
    rng=random.Random(design["controls"]["seed"])
    shuffled=deepcopy(rows);groups=defaultdict(list)
    for index,row in enumerate(shuffled):groups[tuple(row[k] for k in design["controls"]["strata"])].append(index)
    for indices in groups.values():
        signals=[shuffled[i]["features"]["divergence"] for i in indices];rng.shuffle(signals)
        for index,signal in zip(indices,signals):shuffled[index]["features"]["divergence"]=signal
    constant=deepcopy(rows)
    for row in constant:row["features"]["divergence"]=0
    observed=global_summary(reduce_runs(rows,rule),rows,rule)
    shuffle_summary=global_summary(reduce_runs(shuffled,rule),shuffled,rule)
    constant_summary=global_summary(reduce_runs(constant,rule),constant,rule)
    label_groups=defaultdict(list)
    for index,row in enumerate(rows):label_groups[tuple(row[k] for k in design["controls"]["labels_strata"])].append(index)
    labels=[row["reference_positive"] for row in rows];accepted=[select(row["features"],rule)[0] for row in rows]
    run_indices=defaultdict(list)
    for index,row in enumerate(rows):run_indices[row["run_id"]].append(index)
    def mean_precision(label_values):
        stats=[]
        for indices in run_indices.values():
            chosen=[i for i in indices if accepted[i]]
            stats.append(sum(label_values[i] for i in chosen)/len(chosen) if chosen else 0)
        return sum(stats)/len(stats)
    original=mean_precision(labels);permuted=[]
    for _ in range(design["controls"]["permutations"]):
        target=labels.copy()
        for indices in label_groups.values():
            local=[labels[i] for i in indices];rng.shuffle(local)
            for i,value in zip(indices,local):target[i]=value
        permuted.append(mean_precision(target))
    return dict(rule=rule,observed={k:observed[k] for k in ("coverage","precision","abstention")},
                shuffled_divergence={k:shuffle_summary[k] for k in ("coverage","precision","abstention")},
                constant_divergence={k:constant_summary[k] for k in ("coverage","precision","abstention")},
                label_permutation=dict(observed_mean_run_precision=original,null_mean=sum(permuted)/len(permuted),
                                       null_min=min(permuted),null_max=max(permuted),permutations=len(permuted),
                                       diagnostic_tail_fraction=(1+sum(x>=original for x in permuted))/(len(permuted)+1)),
                interpretation="Secondary descriptive controls; no threshold selection, no confirmatory multiple-testing claim")


def final_gate(manifest, path):
    if not path:
        raise ValueError("final analysis requires archived calibration selection gate")
    gate=json.loads(Path(path).read_text())
    if gate.get("selected_rule") is None or gate.get("bundle_digest")!=manifest["bundle_digest"]:
        raise ValueError("invalid final gate")
    if gate.get("decision")!="QUALIFIED_FOR_FINAL_ONLY" or sha(path)!=manifest.get("prerequisite_hash"):
        raise ValueError("final prerequisite identity mismatch")
    return gate


def final_cell_check(value, baseline):
    return dict(baseline_fpr_not_worse=value["median_false_positive_rate"]<=baseline["median_false_positive_rate"],
                baseline_coverage_80pct=value["median_coverage"]>=.8*baseline["median_coverage"])


def analyze(series, output, calibration_gate=None):
    series,output=Path(series),Path(output)
    manifest=json.loads((series/"manifest.json").read_text());phase=manifest["phase"]
    # Validate permit before opening any final outcome, even for analysis.
    gate=final_gate(manifest,calibration_gate) if phase=="final-held-out" else None
    output.mkdir(parents=True,exist_ok=False)
    rows=observations(series);design=json.loads((series/"frozen-design.json").read_text())
    if phase=="development":
        from experiments.verify_cycle4_trust import verify
        verification=verify(series,replay=True)
        result=dict(development_feature_validation="PASS" if verification["passed"] else "FAIL",bundle_digest=manifest["bundle_digest"],
                    series=str(series),series_manifest_hash=sha(series/"manifest.json"),eligible=len(rows),
                    feature_statuses=dict(Counter(row["feature_status"] for row in rows)),
                    feature_range={key:[min(row["features"][key] for row in rows),max(row["features"][key] for row in rows)] for key in ("divergence","epsilon","estimated_improvement")},
                    no_performance_selection=True,verification=verification)
        write(output/"development-freeze.json",result);print(json.dumps({k:result[k] for k in ("development_feature_validation","eligible","feature_statuses")}));return
    if phase == "final-held-out":
        rules=[value["rule"] for value in gate["candidates"] if value["rule"]["id"] in
               {"baseline",gate["selected_rule"]["id"]}]
    else:
        rules=candidates(rows)
    candidate_results=[];all_cells=[];all_runs=[];global_results={}
    diagnostic_ids={"baseline","divergence-q0.5","divergence-horizon-q0.5-h20"}
    for rule in rules:
        runs=reduce_runs(rows,rule);cell=cells(runs,intervals=rule["id"] in diagnostic_ids)
        passing=sum(value["passed"] for value in cell)
        candidate_results.append(dict(rule=rule,qualifies=passing==60 and rule["duplicate_of"] is None,passing_cells=passing,
                                      minimum_cell_median_coverage=min(value["median_coverage"] for value in cell),
                                      mean_cell_median_coverage=sum(value["median_coverage"] for value in cell)/len(cell)))
        all_cells.extend(dict(rule_id=rule["id"],**value) for value in cell)
        all_runs.extend(dict(rule_id=rule["id"],**value) for value in runs)
        global_results[rule["id"]]=global_summary(runs,rows,rule)
    qualified=[value for value in candidate_results if value["qualifies"]] if phase=="calibration" else []
    qualified.sort(key=lambda x:(-x["minimum_cell_median_coverage"],-x["mean_cell_median_coverage"],
                                 {"BASELINE":0,"DIVERGENCE":1,"DIVERGENCE_HORIZON":2}[x["rule"]["family"]],
                                 x["rule"]["d"] or 0,x["rule"]["h"] or 0))
    selected=qualified[0]["rule"] if qualified else None
    if phase == "final-held-out":
        selected=gate["selected_rule"]
        baseline_cells={tuple(value[key] for key in CELL):value for value in all_cells if value["rule_id"]=="baseline"}
        final_cells=[value for value in all_cells if value["rule_id"]==selected["id"]]
        for value in final_cells:
            baseline=baseline_cells[tuple(value[key] for key in CELL)]
            value.update(final_cell_check(value,baseline))
            value["final_passed"]=value["passed"] and value["baseline_fpr_not_worse"] and value["baseline_coverage_80pct"]
        final_pass=all(value["final_passed"] for value in final_cells) and len(final_cells)==60
    result=dict(phase=phase,bundle_digest=manifest["bundle_digest"],series_manifest_hash=sha(series/"manifest.json"),
                selected_rule=selected,candidates=candidate_results,decision="D" if selected is None else "QUALIFIED_FOR_FINAL_ONLY",
                final_heldout="NOT RUN: no qualified calibration candidate" if selected is None else "PERMITTED ONLY AFTER FULL FREEZE",
                global_metrics=global_results)
    if phase == "final-held-out":
        result.update(decision="A" if final_pass else "D",final_heldout="EXECUTED ONCE; NO RETUNING",final_cells=final_cells)
    write(output/("final-decision.json" if phase=="final-held-out" else "calibration-selection.json"),result)
    csv_write(output/"candidate-cell-summary.csv",all_cells);csv_write(output/"candidate-run-summary.csv",all_runs)
    if phase == "calibration":
        write(output/"negative-controls.json",controls(rows,next(rule for rule in rules if rule["id"]=="divergence-q0.5"),design))
    report=["# Cycle 4 trust calibration outcome","","**Status:** Frozen calibration executed; no post-result selector tuning.",
            f"**Evidence:** `{series.as_posix()}`. **Decision:** {result['decision']}. **Final:** {result['final_heldout']}.","",
            "Question: does divergence/horizon add prospective information beyond the epsilon gate in authored J1?",
            "Method: 1,200 seed x full-cell runs, eight repeated anchors each; global frozen quantiles; all 60 cells required. Development was feature validation only. Seed-bootstrap intervals are in the machine summaries. Undefined precision stays in denominators and fails qualification.","",
            "| Candidate | d (queue-vehicle ticks) | h | Pass cells /60 | Coverage | Precision | Abstention | Qualified |",
            "|---|---:|---:|---:|---:|---:|---:|---|"]
    for value in candidate_results:
        rule=value["rule"];g=global_results[rule["id"]]
        report.append(f"| {rule['id']} | {rule['d']} | {rule['h']} | {value['passing_cells']} | {g['coverage']:.4f} | {g['precision']} | {g['abstention']:.4f} | {value['qualifies']} |")
    report.extend(["","Findings: see all candidate cells/runs, global per-seed distributions and predefined negative controls beside this report. No conditional positive category substitutes for all-cell failure.","",
                   "Limitations: authored source-isolated software reference; shared J1 specification and seeded PRNG. Same-window epsilon exists after production execution, so this is offline common-window evidence selection with fresh seeds, not demonstrated real decision-time availability. Calibration results cannot establish prospective final replication. No causal or physical validity and no learning permission.","",
                   "Next action: preserve D when none qualifies; keep final seeds ungenerated. Future mechanism changes require a new protocol and new splits."])
    (output/"report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print(json.dumps({"decision":result["decision"],"selected_rule":selected,"candidates":len(candidate_results),"passing_cells":[[v["rule"]["id"],v["passing_cells"]] for v in candidate_results]}))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("series");parser.add_argument("--output",required=True);parser.add_argument("--gate");args=parser.parse_args()
    analyze(args.series,args.output,args.gate)
