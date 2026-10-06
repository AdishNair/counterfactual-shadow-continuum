"""Fixed bounded Cycle6 helper duties; scratch space is reused, never exhausted."""
import argparse
import json
import os
from pathlib import Path
import time
from csc.os_metrics import process_metrics

MIB = 1024 * 1024


def pressure(kind, directory):
    directory = Path(directory)
    allocation = bytearray(128 * MIB) if kind == "memory" else None
    if allocation is not None:
        for offset in range(0, len(allocation), 4096):
            allocation[offset] = 1
    block = b"6" * (8 * MIB) if kind == "storage" else None
    started, cpu_start = time.perf_counter(), time.process_time()
    iterations, written, operations, checksum = 0, 0, 0, 1
    ready = dict(pid=os.getpid(), kind=kind, allocated_bytes=len(allocation) if allocation else 0,
                 initial_page_touch_complete=allocation is not None)
    (directory / "ready.json").write_text(json.dumps(ready), encoding="utf-8")
    next_sample = started
    exit_state = "FAILED"
    with (directory / "pressure.jsonl").open("x", encoding="utf-8") as log:
        try:
            while not (directory / "stop").exists():
                if kind == "cpu":
                    for _ in range(100000):
                        checksum = (checksum * 1664525 + 1013904223) & 0xffffffff
                    operations += 100000
                elif kind == "memory":
                    for offset in range(0, len(allocation), 4096):
                        allocation[offset] = (allocation[offset] + 1) % 256
                    iterations += 1
                    time.sleep(.005)
                elif kind == "storage":
                    with (directory / "scratch.bin").open("wb") as stream:
                        written += stream.write(block)
                        stream.flush()
                    iterations += 1
                    time.sleep(.005)
                else:
                    raise ValueError(kind)
                now = time.perf_counter()
                if now >= next_sample:
                    log.write(json.dumps(dict(elapsed_s=now-started, cpu_s=time.process_time()-cpu_start,
                                              resident_bytes=process_metrics()["rss_bytes"], iterations=iterations,
                                              written_bytes=written, operations=operations)) + "\n")
                    log.flush()
                    next_sample = now + 1
            exit_state = "COOPERATIVE_STOP"
        finally:
            final = dict(**ready, elapsed_duty_s=time.perf_counter()-started,
                         cpu_s=time.process_time()-cpu_start, resident_bytes=process_metrics()["rss_bytes"],
                         iterations=iterations, written_bytes=written, operations=operations,
                         checksum=checksum, exit_state=exit_state,
                         scratch_file_bytes=(directory / "scratch.bin").stat().st_size if kind == "storage" else 0,
                         flush="stream.flush; no fsync")
            (directory / "final.json").write_text(json.dumps(final, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("cpu", "memory", "storage"))
    parser.add_argument("directory")
    args = parser.parse_args()
    pressure(args.kind, args.directory)
