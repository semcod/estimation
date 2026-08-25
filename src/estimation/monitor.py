from __future__ import annotations

from dataclasses import dataclass, field
import os
import signal
import subprocess
import time
from typing import Sequence

import psutil

from estimation.model import Sample, build_sample, utc_now


@dataclass
class ResourceAccumulator:
    cpu_by_pid: dict[int, tuple[float, float]] = field(default_factory=dict)
    io_by_pid: dict[int, tuple[int, int]] = field(default_factory=dict)
    cpu_user_seconds: float = 0.0
    cpu_system_seconds: float = 0.0
    read_bytes: int = 0
    write_bytes: int = 0
    peak_rss_bytes: int = 0
    max_processes: int = 0
    sample_count: int = 0

    def sample(self, root: psutil.Process) -> None:
        processes: list[psutil.Process] = [root]
        try:
            processes.extend(root.children(recursive=True))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        rss = 0
        alive = 0
        for process in processes:
            try:
                pid = process.pid
                cpu = process.cpu_times()
                current_cpu = (float(cpu.user), float(cpu.system))
                previous_cpu = self.cpu_by_pid.get(pid, (0.0, 0.0))
                self.cpu_user_seconds += max(0.0, current_cpu[0] - previous_cpu[0])
                self.cpu_system_seconds += max(0.0, current_cpu[1] - previous_cpu[1])
                self.cpu_by_pid[pid] = current_cpu

                try:
                    io = process.io_counters()
                    current_io = (int(io.read_bytes), int(io.write_bytes))
                    previous_io = self.io_by_pid.get(pid, (0, 0))
                    self.read_bytes += max(0, current_io[0] - previous_io[0])
                    self.write_bytes += max(0, current_io[1] - previous_io[1])
                    self.io_by_pid[pid] = current_io
                except (AttributeError, psutil.AccessDenied, NotImplementedError):
                    pass

                rss += int(process.memory_info().rss)
                alive += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
                continue

        self.peak_rss_bytes = max(self.peak_rss_bytes, rss)
        self.max_processes = max(self.max_processes, alive)
        self.sample_count += 1


def _finish_sample(
    accumulator: ResourceAccumulator,
    *,
    process_uri: str,
    process_key: str | None,
    ticket_id: str | None,
    correlation_id: str | None,
    started_at: str,
    started_monotonic: float,
    exit_code: int | None,
    outcome: str,
    program: str,
    argv: Sequence[str],
) -> Sample:
    return build_sample(
        process_uri=process_uri,
        process_key=process_key,
        ticket_id=ticket_id,
        correlation_id=correlation_id,
        started_at=started_at,
        finished_at=utc_now(),
        duration_seconds=time.monotonic() - started_monotonic,
        cpu_user_seconds=accumulator.cpu_user_seconds,
        cpu_system_seconds=accumulator.cpu_system_seconds,
        peak_rss_bytes=accumulator.peak_rss_bytes,
        read_bytes=accumulator.read_bytes,
        write_bytes=accumulator.write_bytes,
        max_processes=accumulator.max_processes,
        sample_count=accumulator.sample_count,
        exit_code=exit_code,
        outcome=outcome,
        program=program,
        argv=argv,
    )


def measure_command(
    command: Sequence[str],
    *,
    process_uri: str,
    process_key: str | None = None,
    ticket_id: str | None = None,
    correlation_id: str | None = None,
    interval_seconds: float = 0.1,
) -> Sample:
    argv = [str(item) for item in command]
    if not argv:
        raise ValueError("command must not be empty")
    interval = max(0.01, float(interval_seconds))
    started_at = utc_now()
    started_monotonic = time.monotonic()
    child = subprocess.Popen(argv)
    root = psutil.Process(child.pid)
    accumulator = ResourceAccumulator()
    interrupted = False

    try:
        while child.poll() is None:
            accumulator.sample(root)
            time.sleep(interval)
        accumulator.sample(root)
    except KeyboardInterrupt:
        interrupted = True
        try:
            child.send_signal(signal.SIGINT)
            child.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            child.terminate()
            child.wait(timeout=5)

    exit_code = child.wait()
    outcome = "interrupted" if interrupted else ("succeeded" if exit_code == 0 else "failed")
    return _finish_sample(
        accumulator,
        process_uri=process_uri,
        process_key=process_key,
        ticket_id=ticket_id,
        correlation_id=correlation_id,
        started_at=started_at,
        started_monotonic=started_monotonic,
        exit_code=exit_code,
        outcome=outcome,
        program=os.path.basename(argv[0]),
        argv=argv,
    )


def observe_pid(
    pid: int,
    *,
    process_uri: str,
    process_key: str | None = None,
    ticket_id: str | None = None,
    correlation_id: str | None = None,
    interval_seconds: float = 0.1,
    duration_seconds: float = 10.0,
) -> Sample:
    root = psutil.Process(int(pid))
    interval = max(0.01, float(interval_seconds))
    duration_limit = max(interval, float(duration_seconds))
    started_at = utc_now()
    started_monotonic = time.monotonic()
    accumulator = ResourceAccumulator()

    while time.monotonic() - started_monotonic < duration_limit:
        try:
            accumulator.sample(root)
            if not root.is_running() or root.status() == psutil.STATUS_ZOMBIE:
                break
        except psutil.NoSuchProcess:
            break
        time.sleep(interval)

    try:
        program = root.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        program = "observed-process"
    return _finish_sample(
        accumulator,
        process_uri=process_uri,
        process_key=process_key,
        ticket_id=ticket_id,
        correlation_id=correlation_id,
        started_at=started_at,
        started_monotonic=started_monotonic,
        exit_code=None,
        outcome="observed",
        program=program,
        argv=[program, f"pid:{int(pid)}"],
    )
