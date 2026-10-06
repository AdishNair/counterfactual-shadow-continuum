"""Owned FIFO executor with physical item and serialized-request bounds."""
from collections import deque
from concurrent.futures import Future
import threading
import time


class ExecutorCapacityError(RuntimeError):
    """A bounded executor refused an assignment before queue admission."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class BoundedExecutor:
    def __init__(self, max_workers, capacity, byte_capacity=None):
        self.capacity = capacity
        self.byte_capacity = byte_capacity if byte_capacity is not None else 2**63 - 1
        self.condition = threading.Condition()
        self.items = deque()
        self.inflight = 0
        self.running = 0
        self.inflight_bytes = 0
        self.running_bytes = 0
        self.high_water_inflight = 0
        self.high_water_queue = 0
        self.high_water_inflight_bytes = 0
        self.high_water_queue_bytes = 0
        self.item_rejections = 0
        self.byte_rejections = 0
        self.closed_rejections = 0
        self.closed = False
        self.threads = [threading.Thread(target=self._consume, daemon=True, name=f"csc-dispatch-{i}")
                        for i in range(max_workers)]
        for thread in self.threads:
            thread.start()

    def state(self):
        with self.condition:
            queued_bytes = self.inflight_bytes - self.running_bytes
            return {"physical_queue_depth": len(self.items), "physical_inflight_tasks": self.inflight,
                    "physical_running_tasks": self.running,
                    "physical_queue_bytes": queued_bytes,
                    "physical_inflight_bytes": self.inflight_bytes,
                    "physical_running_bytes": self.running_bytes,
                    "physical_task_capacity": self.capacity,
                    "physical_byte_capacity": self.byte_capacity,
                    "physical_available_capacity": 0 if self.closed else self.capacity - self.inflight,
                    "physical_available_bytes": 0 if self.closed else self.byte_capacity - self.inflight_bytes,
                    "physical_high_water_inflight_tasks": self.high_water_inflight,
                    "physical_high_water_queue_depth": self.high_water_queue,
                    "physical_high_water_inflight_bytes": self.high_water_inflight_bytes,
                    "physical_high_water_queue_bytes": self.high_water_queue_bytes,
                    "physical_item_rejections": self.item_rejections,
                    "physical_byte_rejections": self.byte_rejections,
                    "physical_closed_rejections": self.closed_rejections}

    def submit(self, function, *args, _resident_bytes=0, **kwargs):
        if type(_resident_bytes) is not int or _resident_bytes < 0:
            raise ValueError("resident byte estimate must be a nonnegative integer")
        with self.condition:
            if self.closed:
                self.closed_rejections += 1
                raise ExecutorCapacityError("executor_closed")
            if self.inflight >= self.capacity:
                self.item_rejections += 1
                raise ExecutorCapacityError("physical_item_capacity")
            if _resident_bytes > self.byte_capacity - self.inflight_bytes:
                self.byte_rejections += 1
                raise ExecutorCapacityError("physical_byte_capacity")
            future = Future()
            self.items.append((future, function, args, kwargs, _resident_bytes))
            self.inflight += 1
            self.inflight_bytes += _resident_bytes
            self.high_water_inflight = max(self.high_water_inflight, self.inflight)
            self.high_water_queue = max(self.high_water_queue, len(self.items))
            self.high_water_inflight_bytes = max(self.high_water_inflight_bytes, self.inflight_bytes)
            self.high_water_queue_bytes = max(
                self.high_water_queue_bytes, self.inflight_bytes - self.running_bytes)
            self.condition.notify()
            return future

    def _consume(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.items or self.closed)
                if not self.items:
                    return
                future, function, args, kwargs, resident_bytes = self.items.popleft()
                self.running += 1
                self.running_bytes += resident_bytes
            try:
                # Cancellation alone never frees the physical work item permit.
                if future.set_running_or_notify_cancel():
                    try:
                        result = function(*args, **kwargs)
                    except BaseException as exc:
                        future.set_exception(exc)
                    else:
                        future.set_result(result)
                        del result
            finally:
                del function, args, kwargs, future
                with self.condition:
                    self.running -= 1
                    self.inflight -= 1
                    self.running_bytes -= resident_bytes
                    self.inflight_bytes -= resident_bytes
                    self.condition.notify_all()

    def shutdown(self, wait=True, cancel_futures=True, timeout=None):
        with self.condition:
            self.closed = True
            if cancel_futures:
                while self.items:
                    future, _, _, _, resident_bytes = self.items.popleft()
                    future.cancel()
                    self.inflight -= 1
                    self.inflight_bytes -= resident_bytes
            self.condition.notify_all()
        if wait:
            deadline = None if timeout is None else time.monotonic() + timeout
            for thread in self.threads:
                thread.join(None if deadline is None else max(0, deadline - time.monotonic()))
            if any(thread.is_alive() for thread in self.threads):
                raise TimeoutError("executor transport failed to settle after shutdown")
