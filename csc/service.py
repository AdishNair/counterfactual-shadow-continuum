"""Bounded HTTP transport for remote shadow evaluation; no actuation endpoint.

Deploy behind the supplied NetworkPolicy. This is an internal test service,
not an Internet API. Each evaluation gets a fresh subprocess and hard timeout.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .contracts import canonical

MAX_BODY = 2 * 1024 * 1024


class ShadowServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 8

    def __init__(self, address, timeout=5):
        super().__init__(address, Handler)
        self.evaluation_timeout = timeout
        self.slots = threading.BoundedSemaphore(4)
        self.completed = 0
        self.counter_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def send(self, status, obj):
        body = canonical(obj)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/healthz", "/readyz"):
            self.send(200, {"status": "ready", "role": "SHADOW_ONLY"})
        elif self.path == "/metrics":
            body = f"# TYPE csc_shadow_requests_total counter\ncsc_shadow_requests_total {self.server.completed}\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send(404, {"error": "unknown endpoint"})

    def do_POST(self):
        if self.path != "/v1/evaluate":
            self.send(403, {"error": "shadow service has no mutation API"})
            return
        if not self.server.slots.acquire(blocking=False):
            self.send(503, {"error": "shadow resource budget exhausted"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= MAX_BODY:
                self.send(413, {"error": "request size outside budget"})
                return
            request = json.loads(self.rfile.read(size))
            if request.get("branch", {}).get("role") not in ("SHADOW", "MIRROR"):
                self.send(403, {"error": "non-shadow identity"})
                return
            env = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP") if k in os.environ}
            env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            with tempfile.TemporaryDirectory(prefix="csc-remote-") as scratch:
                completed = subprocess.run([sys.executable, "-m", "csc.worker"], input=canonical(request),
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=scratch, env=env,
                                           timeout=self.server.evaluation_timeout, check=True)
            self.send(200, json.loads(completed.stdout))
            with self.server.counter_lock:
                self.server.completed += 1
        except subprocess.TimeoutExpired:
            self.send(504, {"error": "worker deadline exceeded"})
        except (ValueError, KeyError, TypeError, AttributeError, subprocess.CalledProcessError):
            self.send(400, {"error": "invalid or faulted shadow request"})
        finally:
            self.server.slots.release()

    def log_message(self, fmt, *args):
        # HTTP operational log; epoch/branch records are persisted by coordinator.
        sys.stderr.write(json.dumps({"component": "shadow_http", "message": fmt % args}) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args()
    with ShadowServer((args.host, args.port), args.timeout) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
