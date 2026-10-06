"""Append-only research records and run provenance."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import uuid
import threading
import time
from collections import deque

from . import __version__
from .contracts import canonical, digest


class KnowledgeStore:
    def __init__(self, root, config, experiment_id=None):
        self.experiment_id = experiment_id or f"{config.experiment_name}-{uuid.uuid4().hex[:12]}"
        # IDs are metadata; never permit paths to escape the output directory.
        if not self.experiment_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for c in self.experiment_id) or self.experiment_id in (".", ".."):
            raise ValueError("experiment_id must be a safe directory name")
        self.path = Path(root) / self.experiment_id
        self.path.mkdir(parents=True, exist_ok=False)
        self.streams = {}
        self.writer_thread = threading.get_ident()
        self.evidence_condition = threading.Condition()
        self.evidence_queue = deque()
        self.evidence_queue_bytes = 0
        self.evidence_high_water_items = 0
        self.evidence_high_water_bytes = 0
        self.evidence_dispositions = {key: 0 for key in
                                      ("PERSISTED", "PENDING", "FAILED", "DROPPED", "UNAVAILABLE")}
        self.evidence_transition_counts = {key: 0 for key in self.evidence_dispositions}
        self.evidence_streams = {}
        self.evidence_closed = False
        self.evidence_config = config
        source_root = Path(__file__).resolve().parent.parent
        source_hashes = {str(p.relative_to(source_root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in sorted((source_root / "csc").glob("*.py"))}
        if config.execution_mode == "asynchronous" or config.experiment_name.startswith("cycle4-async"):
            # Explicit dependency closure excludes concurrently developed trust modules.
            names = ("__init__", "contracts", "branches", "world", "safety", "sync", "compare", "store", "runner", "pending", "async_runner", "worker", "warm", "os_metrics", "executor")
            source_hashes = {f"csc/{name}.py": hashlib.sha256((source_root / "csc" / (name + ".py")).read_bytes()).hexdigest() for name in names}
        try:
            git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source_root, capture_output=True, text=True)
            git_sha = git.stdout.strip() if git.returncode == 0 else None
        except FileNotFoundError:
            git_sha = None  # Minimal runtime images do not need the Git executable.
        self.manifest = {"schema_version": 1, "experiment_id": self.experiment_id,
                         "timestamp_utc": datetime.now(timezone.utc).isoformat(), "status": "RUNNING",
                         "software_version": __version__, "git_sha": git_sha,
                         "source_hashes": source_hashes, "config": asdict(config), "config_hash": digest(asdict(config)),
                         "environment": {"python": platform.python_version(), "platform": platform.platform(),
                                         "cpu_count": os.cpu_count(), "backend": config.backend},
                         "limitations": ["software traffic environment", "no physical observations",
                                          "local subprocesses are not a hostile-code sandbox"],
                         "outputs": ["anchors.jsonl", "events.jsonl", "branch_metrics.jsonl", "cfr.jsonl",
                                     "resource_metrics.jsonl", "safety_events.jsonl", "environment_audit.jsonl",
                                     "lifecycle.jsonl", "logs.jsonl", "summary.json", "metrics.prom"]}
        self.write_json("manifest.json", self.manifest)
        self.evidence_thread = threading.Thread(target=self._evidence_loop, daemon=True,
                                                name="csc-evidence-writer")
        self.evidence_thread.start()

    def append(self, name, value):
        if threading.get_ident() != self.writer_thread:
            raise RuntimeError("artifact store requires coordinator single writer")
        if name not in self.streams:
            self.streams[name] = (self.path / name).open("x", encoding="utf-8", newline="\n")
        self.streams[name].write(canonical(value).decode() + "\n")
        self.streams[name].flush()

    def append_evidence(self, name, value, record_id, origin_monotonic_s=None):
        """Admit optional evidence without performing storage I/O on production."""
        if threading.get_ident() != self.writer_thread:
            raise RuntimeError("evidence admission requires coordinator single writer")
        line = canonical(value) + b"\n"
        with self.evidence_condition:
            if (self.evidence_closed or
                    len(self.evidence_queue) >= self.evidence_config.evidence_spool_max_items or
                    len(line) > self.evidence_config.evidence_spool_max_bytes - self.evidence_queue_bytes):
                self.evidence_dispositions["DROPPED"] += 1
                self.evidence_transition_counts["DROPPED"] += 1
                return "DROPPED"
            self.evidence_queue.append({"name": name, "line": line, "record_id": str(record_id),
                                        "attempts": 0, "admitted_monotonic_s": time.perf_counter(),
                                        "origin_monotonic_s": origin_monotonic_s})
            self.evidence_queue_bytes += len(line)
            self.evidence_dispositions["PENDING"] += 1
            self.evidence_transition_counts["PENDING"] += 1
            self.evidence_high_water_items = max(self.evidence_high_water_items, len(self.evidence_queue))
            self.evidence_high_water_bytes = max(self.evidence_high_water_bytes, self.evidence_queue_bytes)
            self.evidence_condition.notify()
        return "PENDING"

    def _open_evidence_stream(self, name):
        if name not in self.evidence_streams:
            path = self.path / name
            stream = path.open("a+b")
            stream.seek(0, 2)
            size = stream.tell()
            if size:
                stream.seek(-1, 2)
                if stream.read(1) != b"\n":
                    stream.seek(0)
                    data = stream.read()
                    boundary = data.rfind(b"\n") + 1
                    stream.seek(boundary)
                    stream.truncate()
                    stream.flush()
            self.evidence_streams[name] = stream
        return self.evidence_streams[name]

    def _write_optional(self, name, line):
        """One recoverable append attempt; fault studies may patch this seam."""
        stream = self._open_evidence_stream(name)
        stream.seek(0, 2)
        offset = stream.tell()
        try:
            stream.write(line)
            stream.flush()
        except BaseException:
            try:
                stream.seek(offset)
                stream.truncate()
                stream.flush()
            except BaseException:
                try:
                    stream.close()
                finally:
                    self.evidence_streams.pop(name, None)
            raise

    def _write_delivery(self, item, disposition):
        """Record terminal optional-write status outside the injected sink seam."""
        terminal = time.perf_counter()
        value = {"record_id": item["record_id"], "stream": item["name"],
                 "status": disposition, "attempts": item["attempts"] + (disposition == "PERSISTED"),
                 "serialized_bytes": len(item["line"]),
                 "admitted_monotonic_s": item["admitted_monotonic_s"],
                 "terminal_monotonic_s": terminal,
                 "persistence_latency_ms": (terminal - item["origin_monotonic_s"]) * 1000
                 if item["origin_monotonic_s"] is not None else None}
        stream = self._open_evidence_stream("evidence_delivery.jsonl")
        stream.seek(0, 2)
        stream.write(canonical(value) + b"\n")
        stream.flush()

    def _evidence_loop(self):
        while True:
            with self.evidence_condition:
                self.evidence_condition.wait_for(lambda: self.evidence_queue or self.evidence_closed)
                if not self.evidence_queue:
                    return
                item = self.evidence_queue[0]
            disposition = None
            try:
                self._write_optional(item["name"], item["line"])
                disposition = "PERSISTED"
            except OSError:
                item["attempts"] += 1
                if item["attempts"] >= self.evidence_config.evidence_spool_max_attempts:
                    disposition = "FAILED"
                else:
                    time.sleep(.01)
            except BaseException:
                disposition = "FAILED"
            if disposition:
                try:
                    self._write_delivery(item, disposition)
                except OSError:
                    # Aggregate manifest accounting remains authoritative for a
                    # delivery-journal failure; whole-disk resilience is unclaimed.
                    pass
                with self.evidence_condition:
                    if self.evidence_queue and self.evidence_queue[0] is item:
                        self.evidence_queue.popleft()
                        self.evidence_queue_bytes -= len(item["line"])
                        self.evidence_dispositions["PENDING"] -= 1
                        self.evidence_dispositions[disposition] += 1
                        self.evidence_transition_counts[disposition] += 1
                        self.evidence_condition.notify_all()

    def evidence_state(self):
        with self.evidence_condition:
            return {"evidence_spool_items": len(self.evidence_queue),
                    "evidence_spool_bytes": self.evidence_queue_bytes,
                    "evidence_spool_high_water_items": self.evidence_high_water_items,
                    "evidence_spool_high_water_bytes": self.evidence_high_water_bytes,
                    "evidence_dispositions": dict(self.evidence_dispositions),
                    "evidence_transition_counts": dict(self.evidence_transition_counts)}

    def drain_evidence(self, timeout=None):
        deadline = time.monotonic() + (self.evidence_config.evidence_spool_drain_s
                                      if timeout is None else timeout)
        with self.evidence_condition:
            while self.evidence_queue and time.monotonic() < deadline:
                self.evidence_condition.wait(max(0, deadline - time.monotonic()))
            return not self.evidence_queue

    def write_json(self, name, value):
        if threading.get_ident() != self.writer_thread:
            raise RuntimeError("artifact store requires coordinator single writer")
        temporary = self.path / (name + ".tmp")
        temporary.write_bytes(canonical(value))
        temporary.replace(self.path / name)

    def close(self, status="COMPLETE", error=None):
        self.drain_evidence()
        with self.evidence_condition:
            self.evidence_closed = True
            if self.evidence_queue:
                count = len(self.evidence_queue)
                self.evidence_dispositions["PENDING"] -= count
                self.evidence_dispositions["UNAVAILABLE"] += count
                self.evidence_transition_counts["UNAVAILABLE"] += count
                self.evidence_queue.clear()
                self.evidence_queue_bytes = 0
            self.evidence_condition.notify_all()
        self.evidence_thread.join(timeout=max(.1, self.evidence_config.evidence_spool_drain_s))
        for stream in self.streams.values():
            stream.close()
        for stream in self.evidence_streams.values():
            stream.close()
        self.manifest.update(status=status, error=error)
        self.manifest["evidence_persistence"] = self.evidence_state()
        self.manifest["artifact_hashes"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                            for p in self.path.iterdir() if p.is_file() and p.name != "manifest.json"}
        self.write_json("manifest.json", self.manifest)
