"""Check manuscript-only revisions against a preserved source backup."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

NUMBERS = re.compile(r"(?<![A-Za-z0-9_])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?(?![A-Za-z0-9_])")
LEAKS = re.compile(r"\bGate\b|Decision D|\bO[45]\b|cycle|\.json|\.py\b|results/|research/|experiments\.|\bSHA\b|b3d2a39|StateCaptureEngine|SumoProductionWorld|\d{8}T\d{6}", re.I)


def expanded(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    return re.sub(r"\\input\{([^}]+)\}", lambda m: (path.parent/m[1]).read_text(encoding="utf-8"), text)


def contexts(text, token):
    return [text[max(0, m.start()-55):m.end()+75].replace("\n", " ")
            for m in NUMBERS.finditer(text) if m[0] == token][:8]


def audit(original, revised, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    before, after = expanded(original), expanded(revised)
    a, b = Counter(NUMBERS.findall(before)), Counter(NUMBERS.findall(after))
    removed, added = a-b, b-a
    detail = {}
    for token in sorted(set(removed)|set(added)):
        detail[token] = dict(before=a[token], after=b[token], removed=removed[token], added=added[token],
                             original_context=contexts(before, token), revised_context=contexts(after, token))
    citations = lambda text: {key for group in re.findall(r"\\cite\{([^}]+)\}", text) for key in group.split(",")}
    assert citations(before) == citations(after), (citations(before)-citations(after), citations(after)-citations(before))
    assert Path(original).with_name("references.bib").read_bytes() == Path(revised).with_name("references.bib").read_bytes()
    table_pairs = [("o5_results_table.tex", "simulator_results.tex"),
                   ("o5_modes_table.tex", "execution_modes.tex"),
                   ("o5_conditions_table.tex", "scenario_results.tex")]
    for old, new in table_pairs:
        old_table = Path(original).with_name(old).read_text()
        new_table = Path(revised).with_name(new).read_text()
        assert NUMBERS.findall(old_table) == NUMBERS.findall(new_table), (old, new)
    containment = Path(revised).with_name("containment_results.tex").read_text()
    assert containment.count("PASS (initial)") == 8
    assert containment.count("FAIL (initial)") == 2
    assert containment.count("N/A (initial)") == 2
    assert containment.count("INCONCLUSIVE (initial)") == 1
    assert containment.count("NOT TESTED (initial)") == 1
    assert containment.count("PASS (re-test)") == 5
    assert containment.count("INCONCLUSIVE (re-test)") == 1
    refs = re.findall(r"\\ref\{([^}]+)\}", after)
    labels = re.findall(r"\\label\{([^}]+)\}", after)
    assert len(labels) == len(set(labels))
    assert not set(refs)-set(labels), set(refs)-set(labels)
    for environment in ("figure", "table"):
        for block in re.findall(r"\\begin\{"+environment+r"\*?\}.*?\\end\{"+environment+r"\*?\}", after, re.S):
            label = re.search(r"\\label\{([^}]+)\}", block)
            assert label and label[1] in refs, block[:100]
    abstract = after.split(r"\begin{abstract}")[1].split(r"\end{abstract}")[0]
    def result_values(text, opening):
        section = text.split(opening, 1)[1].split(r"\section{Discussion}", 1)[0]
        section = re.sub(r"\\path\{[^}]+\}", "", section)
        section = re.sub(r"\\texttt\{[a-f0-9]{6,}\.\.\.[a-f0-9]+\}", "", section)
        section = re.sub(r"\\includegraphics(?:\[[^]]*\])?\{[^}]+\}", "", section)
        section = re.sub(r"p\{[0-9.]+\\(?:textwidth|columnwidth)\}", "", section)
        return set(NUMBERS.findall(section))
    before_values = result_values(before, r"\section{Gate A: Runtime and Evidence Results}")
    after_values = result_values(after, r"\section{Results}")
    assert not before_values-after_values, before_values-after_values
    sections = re.findall(r"\\section\{([^}]+)\}", after)
    assert sections == ["Introduction", "Related Work", "Problem Formulation", "CSC Architecture", "Prototype and Implementation",
                        "Experimental Methodology", "Results", "Discussion", "Limitations and Threats to Validity", "Conclusion"]
    result = dict(original_sha256=hashlib.sha256(Path(original).read_bytes()).hexdigest(),
                  revised_sha256=hashlib.sha256(Path(revised).read_bytes()).hexdigest(),
                  numeric_tokens_original=sum(a.values()), numeric_tokens_revised=sum(b.values()),
                  removed_counts=dict(removed), added_counts=dict(added), changed_tokens=detail,
                  unique_values_removed=sorted(set(a)-set(b)), unique_values_added=sorted(set(b)-set(a)),
                  citation_keys_unchanged=sorted(citations(after)), bibliography_bytes_unchanged=True,
                  simulator_table_numeric_sequences_unchanged=True, initial_containment_outcomes_preserved=True,
                  all_figures_tables_referenced=True, section_order=sections,
                  original_result_numeric_values_preserved=sorted(before_values),
                  abstract_words=len(abstract.split()), leaked_internal_matches=[m[0] for m in LEAKS.finditer(after)])
    (output/"numeric-diff.json").write_text(json.dumps(result, indent=2))
    (output/"original-expanded.tex").write_text(before)
    (output/"revised-expanded.tex").write_text(after)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--revised", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.original, args.revised, args.output)
    print(json.dumps({k: v for k, v in result.items() if k != "changed_tokens"}, indent=2))
