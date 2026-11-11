"""Layout-only rendering of the existing exported delay measurements."""
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt


def render(output):
    source = Path(__file__).resolve().parents[1] / "figure_data.json"
    values = json.loads(source.read_text())["gate_a"]["delay_percent"]
    labels, data = list(values), list(values.values())
    assert labels == ["Normal (0 ms)", "120 ms", "400 ms"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, ax = plt.subplots(figsize=(4.0, 2.7))
    ax.plot(range(len(data)), data, marker="o", color="#C62828", linewidth=2)
    ax.set(xticks=range(len(data)), xticklabels=labels, ylim=(-3, 103),
           ylabel="Complete evidence (%)", xlabel="Added delay per assignment")
    ax.grid(axis="y", alpha=.25)
    for index, value in enumerate(data):
        offset = (10, -17) if index == 0 else ((-10, 9) if index == len(data)-1 else (0, 9))
        ax.annotate(f"{value:.2f}%", (index, value), xytext=offset,
                    textcoords="offset points", ha="left" if index == 0 else "center")
    fig.tight_layout()
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return {"export_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "labels": labels, "data": data, "change": "label placement and axis wording only"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render(args.output)))
