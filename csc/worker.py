"""Single-request process worker. Deliberately contains no authoritative API."""
import json
import sys
from .branches import execute_shadow
from .contracts import canonical


def main():
    if "--warm" in sys.argv:
        from .warm import WarmSession
        session = WarmSession()
        sys.stdout.buffer.write(canonical({"status": "READY", "metadata_version": 1}) + b"\n")
        sys.stdout.buffer.flush()
        for line in sys.stdin.buffer:
            try:
                result = session.evaluate(json.loads(line))
            except BaseException as exc:
                sys.stdout.buffer.write(canonical({"status": "WORKER_ERROR", "error": f"{type(exc).__name__}: {exc}"}) + b"\n")
                sys.stdout.buffer.flush()
                return  # Every reset/assignment/execution failure destroys session.
            sys.stdout.buffer.write(canonical(result) + b"\n")
            sys.stdout.buffer.flush()
            del result, line  # No previous task outcome/input survives the loop.
        return
    request = json.load(sys.stdin)
    sys.stdout.buffer.write(canonical(execute_shadow(request)))


if __name__ == "__main__":
    main()
