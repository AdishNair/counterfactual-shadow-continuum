"""Build the canonical IEEE paper with pinned Tectonic and existing TeX cache."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(engine, output):
    paper = Path(__file__).resolve().parent
    lock = json.loads((paper / "build-engine.json").read_text(encoding="utf-8"))
    engine, output = Path(engine).resolve(), Path(output).resolve()
    if sha(engine) != lock["executable_sha256"]:
        raise ValueError("compiler differs from build-engine.json")
    if output.is_relative_to(paper):
        raise ValueError("build output must be outside manuscript sources")
    text = (paper / "main.tex").read_text(encoding="utf-8")
    names = {"main.tex", "references.bib", "build.py", "build-engine.json"}
    names.update(re.findall(r"\\input\{([^}]+)\}", text))
    names.update(re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", text))
    for name in names:
        if not (paper / name).resolve().is_relative_to(paper) or not (paper / name).is_file():
            raise ValueError("missing or external build input: " + name)
    output.mkdir(parents=True, exist_ok=False)
    source, destination = output / "src", output / "out"
    destination.mkdir()
    for name in names:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(paper / name, target)
    args = [str(engine), "--only-cached", "--untrusted", "--keep-logs", "--keep-intermediates",
            "--outdir", str(destination), "main.tex"]
    metadata = {"command": args, "working_directory": str(source), "compiler_sha256": sha(engine),
                "input_sha256": {name: sha(source / name) for name in sorted(names)}}
    try:
        result = subprocess.run(args, cwd=source, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=300)
        (output / "console.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        metadata["returncode"] = result.returncode
        if result.returncode:
            raise RuntimeError("TeX build failed; inspect console.log")
        pdf = destination / "main.pdf"
        assert pdf.is_file() and pdf.stat().st_size > 10000
        metadata["pdf_sha256"] = sha(pdf)
        metadata["status"] = "compiled"
    except Exception as error:
        metadata.update(status="failed", error=repr(error))
        raise
    finally:
        (output / "build.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.engine, args.output), indent=2))
