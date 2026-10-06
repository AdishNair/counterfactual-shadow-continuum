"""Bounded cooperative local contention helpers; never host exhaustion."""
import argparse
import json
import os
from pathlib import Path
import time


def pressure(kind, directory):
    directory = Path(directory)
    ready, stop = directory / "ready.json", directory / "stop"
    allocation = bytearray(64 * 1024 * 1024) if kind == "memory" else None
    block = b"C5pressure" * (1024 * 1024 // 10) if kind == "storage" else None
    started, cpu_started = time.perf_counter(), time.process_time()
    operations, written, rounds, checksum = 0, 0, 0, 1
    ready.write_text(json.dumps(dict(pid=os.getpid(), kind=kind, allocated_bytes=len(allocation) if allocation else 0)), encoding="utf-8")
    log = (directory / "pressure.jsonl").open("a", encoding="utf-8")
    next_sample = started
    try:
        while not stop.exists():
            if kind == "cpu":
                for _ in range(100000):
                    checksum = (checksum * 1664525 + 1013904223) & 0xffffffff
                operations += 100000
            elif kind == "memory":
                for offset in range(0, len(allocation), 4096):
                    allocation[offset] = (allocation[offset] + 1) % 256
                rounds += 1
                time.sleep(.005)
            elif kind == "storage":
                # One bounded 4 MiB scratch file rewritten; flush != fsync/durable transaction.
                with (directory / "scratch.bin").open("wb") as stream:
                    for _ in range(4):
                        written += stream.write(block)
                    stream.flush()
                rounds += 1
                time.sleep(.005)
            else:
                raise ValueError(kind)
            now = time.perf_counter()
            if now >= next_sample:
                log.write(json.dumps(dict(elapsed_s=now-started, cpu_s=time.process_time()-cpu_started,
                                           operations=operations, memory_touch_rounds=rounds if allocation else 0,
                                           written_bytes=written, allocated_bytes=len(allocation) if allocation else 0)) + "\n")
                log.flush()
                next_sample = now + 1
    finally:
        final = dict(kind=kind, pid=os.getpid(), duration_s=time.perf_counter()-started,
                     cpu_s=time.process_time()-cpu_started, operations=operations,
                     memory_touch_rounds=rounds if allocation else 0, written_bytes=written,
                     allocated_bytes=len(allocation) if allocation else 0,
                     storage_peak_file_bytes=(directory / "scratch.bin").stat().st_size if kind == "storage" else 0,
                     flush="Python stream.flush; no fsync", checksum=checksum)
        (directory / "final.json").write_text(json.dumps(final, sort_keys=True), encoding="utf-8")
        log.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("cpu", "memory", "storage"))
    parser.add_argument("directory")
    args = parser.parse_args()
    pressure(args.kind, args.directory)
