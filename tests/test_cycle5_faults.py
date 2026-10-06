"""Regression checks for terminal fault accounting, eviction and sustained backpressure."""
import unittest

from experiments.cycle5_faults import synthetic_cases


class Cycle5FaultTests(unittest.TestCase):
    def test_deterministic_fault_campaign_invariants(self):
        rows, _ = synthetic_cases()
        self.assertEqual(len(rows), 8)
        for row in rows:
            with self.subTest(case=row["case"]):
                self.assertTrue(row["passed"], row["checks"])


if __name__ == "__main__":
    unittest.main()
