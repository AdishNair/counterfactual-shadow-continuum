"""Frozen-rule diagnostics and publication plots, never selector construction."""
import argparse
from collections import Counter,defaultdict
import csv
import json
from pathlib import Path
from statistics import median

from experiments.cycle4_trust import sha,write


def diagnose(analysis,output):
    analysis,output=Path(analysis),Path(output);output.mkdir(parents=True,exist_ok=False)
    selection=json.loads((analysis/"calibration-selection.json").read_text())
    with (analysis/"candidate-run-summary.csv").open(encoding="utf-8") as stream:rows=list(csv.DictReader(stream))
    ids=("baseline","divergence-q0.5","divergence-horizon-q0.5-h20")
    strata=[];actions={};oracle=[]
    for identity in ids:
        selected_rows=[row for row in rows if row["rule_id"]==identity]
        action_count=Counter()
        for row in selected_rows:action_count.update(json.loads(row["accepted_actions"]))
        actions[identity]=dict(action_count)
        for factor in ("horizon","demand","incident","mismatch"):
            groups=defaultdict(list)
            for row in selected_rows:groups[row[factor]].append(row)
            for level,group in sorted(groups.items()):
                n=sum(int(row["eligible"]) for row in group);selected=sum(int(row["selected"]) for row in group)
                tp=sum(int(row["tp"]) for row in group);fp=sum(int(row["fp"]) for row in group)
                negatives=sum(int(row["reference_negative"]) for row in group);positives=sum(int(row["oracle_positive"]) for row in group)
                strata.append(dict(rule=identity,factor=factor,level=level,seed_run_units=len(group),eligible=n,selected=selected,
                                   coverage=selected/n,precision=tp/selected if selected else None,abstention=1-selected/n,
                                   false_positive_rate=fp/negatives if negatives else None,
                                   false_negative_rate=sum(int(row["fn"]) for row in group)/positives if positives else None,
                                   undefined_precision_runs=sum(not row["precision"] for row in group),
                                   median_run_coverage=median(float(row["coverage"]) for row in group)))
        oracle.append(dict(rule=identity,maximum_perfect_information_coverage=sum(int(row["oracle_positive"]) for row in selected_rows)/9600,
                           coverage_lost_by_abstention=sum(int(row["fn"]) for row in selected_rows)/9600,
                           mean_selected_choice_value_loss=sum(float(row["choice_value_loss"]) for row in selected_rows)/1200))
    result=dict(status="secondary diagnostics without retuning",condition_metrics=strata,accepted_actions=actions,oracle_bounds=oracle,
                family_display="predeclared q=.50; horizon<=20",nominal_epsilon_coverage=None,
                epsilon_calibration_limit="epsilon is not a confidence interval and has no declared probabilistic nominal coverage; empirical error coverage reported only")
    write(output/"robustness.json",result)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,"savefig.dpi":180})
    fig,ax=plt.subplots(figsize=(6.8,3.8))
    for entry in selection["candidates"]:
        rule=entry["rule"];g=selection["global_metrics"][rule["id"]]
        ax.scatter(g["coverage"],g["precision"] or 0,marker={"BASELINE":"s","DIVERGENCE":"o","DIVERGENCE_HORIZON":"^"}[rule["family"]],s=38,
                   alpha=.75,label=rule["id"] if rule["id"] in ids else None)
    ax.set(xlabel="Recommendation coverage (selected / 9,600 eligible anchors)",ylabel="Positive recommendation precision",ylim=(-.02,1.04),xlim=(-.02,.6),title="Frozen trust grid: reliability and coverage")
    ax.legend(loc="lower right",fontsize=7);fig.tight_layout();fig.savefig(output/"trust-reliability-coverage.png");plt.close(fig)
    with (analysis/"candidate-cell-summary.csv").open(encoding="utf-8") as stream:cells=list(csv.DictReader(stream))
    fig,ax=plt.subplots(figsize=(10,2.8));matrix=[[int(row["passed"]=="True") for row in cells if row["rule_id"]==identity] for identity in ids]
    ax.imshow(matrix,cmap="RdYlGn",vmin=0,vmax=1,aspect="auto",interpolation="nearest");ax.set_yticks(range(3),ids);ax.set(xlabel="Full factorial cell (CSV sorted H, demand, incident, mismatch)",title="Exposure-aware calibration cell qualification (green=pass)");fig.tight_layout();fig.savefig(output/"trust-cell-qualification.png");plt.close(fig)
    figure_sources={name:sha(analysis/name) for name in ("calibration-selection.json","candidate-run-summary.csv","candidate-cell-summary.csv")}
    write(output/"figure-metadata.json",dict(source_artifacts=figure_sources,analysis_script_sha256=sha(__file__),
                                            seed_count=20,independent_unit="seed x full cell; shared seed across cells",anchors_per_run=8,
                                            metrics={"coverage":"recommended / eligible (unit fraction)","precision":"selected reference-positive / recommended (fraction)","cell_qualification":"frozen all criteria including exposure (binary)"},
                                            aggregation="precision/coverage plot descriptive anchor-weighted totals; inferential bootstrap seed units in analysis JSON/CSV",matplotlib=matplotlib.__version__))
    report=["# Cycle 4 selector robustness diagnostics","","**Status:** Predefined secondary diagnostics; no new rule or tuning.",
            "**Question:** is apparent reliability explained by abstention, a few conditions, actions, or unstable seeds?",
            f"**Evidence/method:** `{analysis.as_posix()}` deterministic seed/run summaries; q=.50 family display fixed before outcomes; all candidate cell results retained.","",
            "| Rule | Factor | Level | Coverage | Precision | Abstention | Undefined precision runs |",
            "|---|---|---|---:|---:|---:|---:|"]
    for row in strata:report.append(f"| {row['rule']} | {row['factor']} | {row['level']} | {row['coverage']:.4f} | {row['precision']} | {row['abstention']:.4f} | {row['undefined_precision_runs']} |")
    report.extend(["","Accepted-action counts and oracle coverage/value-loss bounds are in `robustness.json`. Per-seed distributions and all-cell coverage floors are in the frozen calibration selection JSON. Figures are descriptive; no significance is inferred from pooled anchors.","",
                   "Limitations: no calibrated probability or nominal epsilon error coverage exists. Precision near one can coexist with inadequate coverage. Cells with unsupported metadata abstain by design. Final heldout remains ungenerated if qualification fails. Next action: preserve frozen decision; no replacement selectors."])
    (output/"robustness.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print(json.dumps({"diagnostics":str(output),"strata":len(strata),"figures":2}))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("analysis");parser.add_argument("--output",required=True);args=parser.parse_args();diagnose(args.analysis,args.output)
