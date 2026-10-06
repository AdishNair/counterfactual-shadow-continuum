import argparse
import json
from .contracts import Config
from .runner import run


def main():
    parser = argparse.ArgumentParser(description="Run a reproducible CSC research experiment")
    parser.add_argument("config")
    parser.add_argument("--output", default="results")
    parser.add_argument("--experiment-id")
    args = parser.parse_args()
    path, summary = run(Config.load(args.config), args.output, args.experiment_id)
    print(json.dumps({"result_path": str(path), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
