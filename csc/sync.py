"""Ordered input validation with measured anomalies; invalid windows are excluded."""
import time
from .contracts import digest


class InputSynchronizationLayer:
    def deliver(self, events, branch, enabled=True, fault="none", delay_s=0):
        started = time.perf_counter()
        delivery = list(events)
        if fault == "drop" and delivery:
            delivery.pop(len(delivery) // 2)
        elif fault == "duplicate" and delivery:
            delivery.insert(1, delivery[0])
        elif fault == "reorder" and len(delivery) >= 2:
            delivery[0], delivery[1] = delivery[1], delivery[0]
        elif fault == "delay":
            time.sleep(delay_s)
        seen, duplicates, out_of_order = set(), 0, 0
        previous = branch.start_sequence - 1
        for e in delivery:
            e.validate()
            if e.experiment_id != branch.experiment_id or e.epoch != branch.epoch:
                raise ValueError("foreign experiment/epoch event")
            seq = e.sequence_number
            if seq in seen:
                duplicates += 1
            if seq <= previous:
                out_of_order += 1
            seen.add(seq)
            previous = seq
        expected = set(range(branch.start_sequence, branch.end_sequence + 1))
        missing = len(expected - seen)
        unexpected = len(seen - expected)
        # Enabled sync deduplicates/reorders but never invents a missing input.
        if enabled:
            delivery = sorted({e.sequence_number: e for e in delivery}.values(), key=lambda e: e.sequence_number)
        sequence = [e.sequence_number for e in delivery]
        comparable = sequence == list(range(branch.start_sequence, branch.end_sequence + 1))
        metrics = {"missing_events": missing, "duplicate_events": duplicates,
                   "out_of_order_events": out_of_order, "unexpected_events": unexpected,
                   "synchronization_ms": (time.perf_counter() - started) * 1000,
                   "consumed_sequence": sequence, "input_hash": digest([e.__dict__ for e in delivery]),
                   "comparable": comparable}
        return delivery, metrics
