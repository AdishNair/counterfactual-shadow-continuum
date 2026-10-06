"""Machine-readable invariants, legal transitions and two guard mutations."""
import io
from pathlib import Path
import unittest
from unittest.mock import patch

from csc.contracts import canonical
from csc.pending import PendingShadowLedger, LEGAL, TERMINAL, transition
from tests.test_async import AsyncTests


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args):
        super().__init__(*args)
        self.records = []
    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append(dict(test=test.id(), status="PASS"))
    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.records.append(dict(test=test.id(), status="FAIL"))
    def addError(self, test, error):
        super().addError(test, error)
        self.records.append(dict(test=test.id(), status="ERROR"))


def audit(output):
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, resultclass=RecordingResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(AsyncTests))
    transitions = []
    for previous in {"QUEUED", "RUNNING"} | TERMINAL:
        for target in {"QUEUED", "RUNNING"} | TERMINAL:
            expected = target in LEGAL.get(previous, set()) or (previous == target == "COMPLETED")
            try:
                observed = transition(previous, target)
                legal = True
            except ValueError:
                observed, legal = "REJECTED_ILLEGAL", False
            transitions.append(dict(previous=previous, target=target, legal=legal, expected=expected, status="PASS" if legal == expected else "FAIL"))
    mutations = []
    # Removing identity validation must cause the same negative invariant test to fail.
    with patch.object(PendingShadowLedger, "valid_identity", return_value=True):
        mutated = unittest.TextTestRunner(stream=io.StringIO()).run(AsyncTests("test_bad_epoch_anchor_action_window_input_provenance"))
        mutations.append(dict(mutation="accept forged identity", detected=not mutated.wasSuccessful()))
    # Retiring expired packages as evidence-complete would fabricate comparisons.
    original_expire = PendingShadowLedger.expire
    def unsafe_expire(ledger, package, reason="deadline"):
        original_expire(ledger, package, reason)
        for bid in package["states"]:
            package["states"][bid] = "COMPLETED"
    with patch.object(PendingShadowLedger, "expire", unsafe_expire):
        mutated = unittest.TextTestRunner(stream=io.StringIO()).run(AsyncTests("test_expiry_cannot_resurrect_or_actuate"))
        mutations.append(dict(mutation="expired evidence terminal changed to completed", detected=not mutated.wasSuccessful()))
    report = dict(status="PASS" if result.wasSuccessful() and all(t["status"] == "PASS" for t in transitions) and all(m["detected"] for m in mutations) else "FAIL",
                  tests=result.records, tests_run=result.testsRun, transitions=transitions, mutation_tests=mutations,
                  scope="local ledger, restart as new run, single writer; no durable distributed recovery")
    Path(output).write_bytes(canonical(report))
    print(report["status"], result.testsRun, "tests", len(transitions), "transitions", mutations)
    if report["status"] != "PASS":
        print(stream.getvalue())
        raise SystemExit(1)


if __name__ == "__main__":
    audit("research/tables/cycle4_async_transition_tests.json")
