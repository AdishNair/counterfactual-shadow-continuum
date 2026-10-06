"""Deterministic optional-store write-attempt faults, never required journals."""
from contextlib import contextmanager
from csc.store import KnowledgeStore

CASES = ("control", "preappend", "temporary", "sustained", "torn")


@contextmanager
def optional_fault(case):
    if case not in CASES:
        raise ValueError("unknown optional storage fault")
    original = KnowledgeStore._write_optional
    state = dict(case=case, attempts=0, injected=0, torn_bytes=0)

    def write(store, name, line):
        if name not in ("cfr.jsonl", "branch_metrics.jsonl"):
            raise ValueError("fault seam received a required stream")
        state["attempts"] += 1
        attempt = state["attempts"]
        fail = ((case == "preappend" and attempt == 25) or
                (case == "temporary" and 25 <= attempt <= 74) or
                (case == "sustained" and attempt >= 25))
        if fail:
            state["injected"] += 1
            raise OSError("Cycle6 optional pre-append failure")
        if case == "torn" and attempt == 25:
            stream = store._open_evidence_stream(name)
            stream.seek(0, 2)
            boundary = stream.tell()  # Existing successful appends end at newline.
            fragment = line[:max(1, len(line) // 2)].rstrip(b"\n")
            stream.write(fragment)
            stream.flush()
            state["torn_bytes"] += len(fragment)
            state["injected"] += 1
            # Recover the last valid newline before allowing the spool retry.
            stream.seek(boundary)
            stream.truncate()
            stream.flush()
            raise OSError("Cycle6 optional torn append; truncated to valid boundary")
        return original(store, name, line)

    KnowledgeStore._write_optional = write
    try:
        yield state
    finally:
        KnowledgeStore._write_optional = original
