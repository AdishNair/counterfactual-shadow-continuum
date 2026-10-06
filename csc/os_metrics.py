"""OS process measurements; missing fields remain unavailable, never zero-filled."""
import os
import sys


def process_metrics(pid=None):
    pid = os.getpid() if pid is None else pid
    result = {"rss_bytes": None, "handle_count": None, "process_cpu_s": None}
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.GetProcessHandleCount.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        handle = kernel.OpenProcess(0x0400 | 0x0010, False, pid)
        if handle:
            try:
                counters = Counters()
                counters.cb = ctypes.sizeof(counters)
                if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                    result["rss_bytes"] = counters.WorkingSetSize
                count = wintypes.DWORD()
                if kernel.GetProcessHandleCount(handle, ctypes.byref(count)):
                    result["handle_count"] = count.value
                times = [wintypes.FILETIME() for _ in range(4)]
                if kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                    result["process_cpu_s"] = sum((t.dwHighDateTime << 32) + t.dwLowDateTime for t in times[2:]) / 1e7
            finally:
                kernel.CloseHandle(handle)
    else:
        try:
            from pathlib import Path
            fields = (Path("/proc") / str(pid) / "stat").read_text().split()
            result["rss_bytes"] = int(fields[23]) * os.sysconf("SC_PAGE_SIZE")
            result["process_cpu_s"] = (int(fields[13]) + int(fields[14])) / os.sysconf("SC_CLK_TCK")
            result["handle_count"] = len(list((Path("/proc") / str(pid) / "fd").iterdir()))
        except (OSError, ValueError):
            pass
    return result
