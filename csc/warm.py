"""First-party reusable process transport; not a hostile-code sandbox."""
from collections import deque
import json
import os
from pathlib import Path
import queue
import random
import subprocess
import sys
import tempfile
import threading
import time

from .contracts import Anchor, Branch, canonical


class WarmSession:
    """Only versioned assignment metadata survives task-local model execution."""
    def __init__(self):
        self.version = 1
        self.seen = deque(maxlen=128)
        self.last_epoch = -1
        self.experiment_id = None
        self.completed_tasks = 0
        self.buffers = []
        self.baseline_environment = dict(os.environ)

    def evaluate(self, request):
        from .branches import execute_shadow
        if request.get("fault") == "worker_contamination":
            self.buffers.append("injected previous-epoch input")
        allowed = {"version", "seen", "last_epoch", "experiment_id", "completed_tasks", "buffers", "baseline_environment"}
        metadata_valid = (set(self.__dict__) == allowed and self.version == 1 and
                          type(self.seen) is deque and self.seen.maxlen == 128 and
                          all(type(value) is str for value in self.seen) and
                          type(self.last_epoch) is int and self.last_epoch >= -1 and
                          (self.experiment_id is None or type(self.experiment_id) is str) and
                          type(self.completed_tasks) is int and self.completed_tasks >= 0 and
                          type(self.buffers) is list and type(self.baseline_environment) is dict)
        if not metadata_valid or self.buffers or dict(os.environ) != self.baseline_environment:
            raise RuntimeError("reset integrity violated")
        branch = Branch(**request["branch"])
        anchor = Anchor.from_envelope(request["anchor"])
        if self.experiment_id is not None and branch.experiment_id != self.experiment_id:
            raise ValueError("foreign worker experiment")
        if branch.branch_id in self.seen:
            raise ValueError("duplicate assignment")
        if branch.epoch < self.last_epoch:
            raise ValueError("stale assignment")
        self.experiment_id = branch.experiment_id
        self.last_epoch = branch.epoch
        self.seen.append(branch.branch_id)
        # Model RNG is keyed by anchor seed and sequence; reset global RNG too.
        random.seed(anchor.hydrate().rng_seed)
        try:
            result = execute_shadow(request)
            self.completed_tasks += 1
            result["runtime"].update(worker_metadata_version=self.version,
                                     worker_completed_tasks=self.completed_tasks,
                                     reset_verified=True)
            return result
        finally:
            self.buffers.clear()
            random.seed(0)
            if dict(os.environ) != self.baseline_environment:
                raise RuntimeError("task changed worker environment")


def worker_environment():
    env = {k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP") if k in os.environ}
    env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


class WarmProcess:
    def __init__(self, config, on_spawn=None):
        self.config, self.tasks, self.born = config, 0, time.monotonic()
        self.scratch = tempfile.TemporaryDirectory(prefix="csc-warm-")
        self.responses = queue.Queue(maxsize=1)
        self.closed = threading.Event()
        self.close_lock = threading.Lock()
        self.cleaned = False
        self.writes = queue.Queue(maxsize=1)
        self.process = self.reader = self.writer = None
        started = time.perf_counter()
        try:
            self.process = subprocess.Popen([sys.executable, "-m", "csc.worker", "--warm"],
                                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=subprocess.DEVNULL, cwd=self.scratch.name,
                                            env=worker_environment(), bufsize=0)
            if on_spawn is not None:
                on_spawn(self)  # Manager owns the child before helper/readiness work.
            self.reader = threading.Thread(target=self._read, daemon=True)
            self.reader.start()
            self.writer = threading.Thread(target=self._write, daemon=True)
            self.writer.start()
            # Readiness is a separate bounded pre-task contract, not an evidence
            # deadline extension. Replacement consumes executor capacity.
            if self._receive(5).get("status") != "READY":
                raise ValueError("warm handshake failed")
            self.startup_ms = (time.perf_counter() - started) * 1000
        except BaseException:
            self.close()
            raise

    def _read(self):
        try:
            while not self.closed.is_set():
                line = self.process.stdout.readline(self.config.max_result_bytes + 1)
                if not line:
                    value = RuntimeError("worker died before acknowledgment")
                elif len(line) > self.config.max_result_bytes or not line.endswith(b"\n"):
                    value = ValueError("worker result exceeds body bound")
                else:
                    value = json.loads(line)
                    if isinstance(value, dict) and isinstance(value.get("runtime"), dict):
                        value["runtime"]["result_received_monotonic_s"] = time.perf_counter()
                try:
                    self.responses.put(value, timeout=.1)
                except queue.Full:
                    break
                terminal = isinstance(value, BaseException)
                del line, value  # Reader holds no preceding task response while idle.
                if terminal:
                    break
        except BaseException as exc:
            try:
                self.responses.put_nowait(exc)
            except queue.Full:
                pass

    def _receive(self, timeout):
        try:
            value = self.responses.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError("warm worker execution timeout")
        if isinstance(value, BaseException):
            raise value
        return value

    def _write(self):
        while not self.closed.is_set():
            try:
                body, completion, errors = self.writes.get(timeout=.05)
            except queue.Empty:
                continue
            try:
                view = memoryview(body)
                while view and not self.closed.is_set():
                    written = self.process.stdin.write(view)
                    if not written:
                        raise BrokenPipeError("worker request pipe closed")
                    view = view[written:]
                if self.closed.is_set():
                    raise BrokenPipeError("worker transport aborted")
                self.process.stdin.flush()
            except BaseException as exc:
                errors.append(exc)
            finally:
                completion.set()
                del body, completion, errors, view

    def abort(self):
        self.closed.set()
        if self.process is not None and self.process.poll() is None:
            try:
                self.process.kill()
            except ProcessLookupError:
                pass

    def evaluate(self, request):
        body = canonical(request)
        if len(body) > self.config.max_result_bytes:
            raise ValueError("worker assignment exceeds body bound")
        deadline = time.monotonic() + self.config.shadow_timeout_s
        completion, errors = threading.Event(), []
        try:
            self.writes.put_nowait((body + b"\n", completion, errors))
            if not completion.wait(max(0, deadline - time.monotonic())):
                raise TimeoutError("warm worker request write timeout")
            if errors:
                raise errors[0]
            result = self._receive(max(0, deadline - time.monotonic()))
        except BaseException:
            self.abort()
            raise
        self.tasks += 1
        if result.get("status") == "WORKER_ERROR":
            raise RuntimeError(result.get("error", "worker error"))
        result["runtime"]["worker_startup_ms"] = self.startup_ms if self.tasks == 1 else 0
        return result

    def expired(self):
        return self.tasks >= self.config.worker_max_tasks or time.monotonic() - self.born >= self.config.worker_max_lifetime_s

    def close(self):
        with self.close_lock:
            if self.cleaned:
                return
            self.abort()
            if self.process is not None:
                self.process.wait(timeout=5)
            for helper in (self.writer, self.reader):
                if helper is not None and helper.ident is not None:
                    helper.join(timeout=1)
            if any(helper is not None and helper.is_alive() for helper in (self.writer, self.reader)):
                raise TimeoutError("worker I/O helper failed to stop after process death")
            if self.process is not None:
                for stream in (self.process.stdin, self.process.stdout):
                    stream.close()
            self.scratch.cleanup()
            self.cleaned = True
