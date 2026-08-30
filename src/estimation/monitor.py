from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Sequence

import psutil

from estimation.model import Sample, build_sample, utc_now


POWER_CAP_ROOT = Path("/sys/class/powercap")
CGROUP_ROOT = Path("/sys/fs/cgroup")


def _read_number(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _rapl_snapshot(root: Path = POWER_CAP_ROOT) -> dict[str, tuple[int, int | None]]:
    result: dict[str, tuple[int, int | None]] = {}
    try:
        domains = [item for item in root.iterdir() if (item / "energy_uj").is_file()]
    except OSError:
        return result
    for domain in domains:
        energy = _read_number(domain / "energy_uj")
        if energy is not None:
            key = hashlib.sha256(domain.name.encode("utf-8")).hexdigest()[:16]
            result[key] = (energy, _read_number(domain / "max_energy_range_uj"))
    return result


def _rapl_delta(start: dict[str, tuple[int, int | None]], end: dict[str, tuple[int, int | None]]) -> tuple[float | None, int]:
    delta = 0
    domains = 0
    for key, (before, maximum) in start.items():
        if key not in end:
            continue
        after = end[key][0]
        change = after - before
        if change < 0 and maximum:
            change += maximum
        if change >= 0:
            delta += change
            domains += 1
    return (delta / 1_000_000.0, domains) if domains else (None, 0)


def _host_cpu_seconds(path: Path = Path("/proc/stat")) -> float | None:
    try:
        fields = path.read_text(encoding="utf-8").splitlines()[0].split()[1:]
        return sum(int(value) for value in fields) / float(os.sysconf("SC_CLK_TCK"))
    except (OSError, ValueError, IndexError):
        return None


def _cgroup_directory(pid: int, root: Path = CGROUP_ROOT) -> Path | None:
    try:
        rows = Path(f"/proc/{pid}/cgroup").read_text(encoding="utf-8").splitlines()
        relative = next(row.split("::", 1)[1] for row in rows if "::" in row)
        candidate = (root / relative.lstrip("/")).resolve()
        candidate.relative_to(root.resolve())
        return candidate
    except (OSError, StopIteration, ValueError):
        return None


def _key_values(path: Path) -> dict[str, int]:
    try:
        return {
            fields[0]: int(fields[1])
            for line in path.read_text(encoding="utf-8").splitlines()
            if len(fields := line.split()) >= 2 and fields[1].isdigit()
        }
    except OSError:
        return {}


def _io_values(path: Path) -> tuple[int, int] | None:
    try:
        reads = writes = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            values = {key: int(value) for token in line.split()[1:] for key, value in [token.split("=", 1)]}
            reads += values.get("rbytes", 0)
            writes += values.get("wbytes", 0)
        return reads, writes
    except (OSError, ValueError):
        return None


def _pressure_total(path: Path) -> int | None:
    try:
        line = next(row for row in path.read_text(encoding="utf-8").splitlines() if row.startswith("some "))
        return int(next(token.split("=", 1)[1] for token in line.split() if token.startswith("total=")))
    except (OSError, StopIteration, ValueError):
        return None


def _cgroup_snapshot(directory: Path | None) -> dict[str, int | str | None]:
    if directory is None:
        return {}
    cpu = _key_values(directory / "cpu.stat")
    io = _io_values(directory / "io.stat")
    return {
        "cgroup_id": "cgroup:" + hashlib.sha256(str(directory).encode("utf-8")).hexdigest()[:16],
        "cpu_usec": cpu.get("usage_usec"),
        "memory_peak": _read_number(directory / "memory.peak"),
        "read_bytes": io[0] if io else None,
        "write_bytes": io[1] if io else None,
        "pids_peak": _read_number(directory / "pids.peak"),
        "psi_cpu": _pressure_total(directory / "cpu.pressure"),
        "psi_io": _pressure_total(directory / "io.pressure"),
        "psi_memory": _pressure_total(directory / "memory.pressure"),
    }


def _counter_delta(before: int | str | None, after: int | str | None, scale: float = 1.0) -> float | int | None:
    if not isinstance(before, int) or not isinstance(after, int):
        return None
    return max(0, after - before) / scale


@dataclass
class LinuxObservation:
    pid: int
    rapl: dict[str, tuple[int, int | None]] = field(default_factory=_rapl_snapshot)
    host_cpu_seconds: float | None = field(default_factory=_host_cpu_seconds)
    cgroup_directory: Path | None = None
    cgroup: dict[str, int | str | None] = field(default_factory=dict)

    @classmethod
    def start(cls, pid: int) -> "LinuxObservation":
        directory = _cgroup_directory(pid)
        return cls(pid=pid, cgroup_directory=directory, cgroup=_cgroup_snapshot(directory))

    def finish(self, process_cpu_seconds: float) -> tuple[dict[str, object], dict[str, object]]:
        package_joules, domains = _rapl_delta(self.rapl, _rapl_snapshot())
        host_end = _host_cpu_seconds()
        host_delta = None if self.host_cpu_seconds is None or host_end is None else max(0.0, host_end - self.host_cpu_seconds)
        if package_joules is not None and host_delta and process_cpu_seconds >= 0:
            energy = {
                "joules": round(package_joules * min(1.0, process_cpu_seconds / host_delta), 6),
                "method": "rapl_cpu_share",
                "confidence": "low",
                "domains": domains,
            }
        else:
            energy = {"joules": None, "method": "unavailable", "confidence": "none", "domains": domains}

        end = _cgroup_snapshot(self.cgroup_directory)
        same_cgroup = bool(self.cgroup) and self.cgroup.get("cgroup_id") == end.get("cgroup_id")
        def delta(name: str, scale: float = 1.0):
            return _counter_delta(self.cgroup.get(name), end.get(name), scale) if same_cgroup else None
        kernel = {
            "cgroup_id": end.get("cgroup_id") if same_cgroup else None,
            "attribution": "shared" if same_cgroup else "unavailable",
            "cpu_seconds": delta("cpu_usec", 1_000_000.0),
            "memory_peak_bytes": end.get("memory_peak") if same_cgroup else None,
            "read_bytes": delta("read_bytes"),
            "write_bytes": delta("write_bytes"),
            "pids_peak": end.get("pids_peak") if same_cgroup else None,
            "pressure": {
                "cpu_some_seconds": delta("psi_cpu", 1_000_000.0),
                "io_some_seconds": delta("psi_io", 1_000_000.0),
                "memory_some_seconds": delta("psi_memory", 1_000_000.0),
            },
        }
        return energy, kernel


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
    observation: LinuxObservation,
) -> Sample:
    process_cpu_seconds = accumulator.cpu_user_seconds + accumulator.cpu_system_seconds
    energy, kernel = observation.finish(process_cpu_seconds)
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
        energy=energy,
        kernel=kernel,
    )


def measure_command(
    command: Sequence[str],
    *,
    process_uri: str,
    process_key: str | None = None,
    ticket_id: str | None = None,
    correlation_id: str | None = None,
    interval_seconds: float = 1.0,
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
    observation = LinuxObservation.start(child.pid)
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
        observation=observation,
    )


def observe_pid(
    pid: int,
    *,
    process_uri: str,
    process_key: str | None = None,
    ticket_id: str | None = None,
    correlation_id: str | None = None,
    interval_seconds: float = 1.0,
    duration_seconds: float = 10.0,
) -> Sample:
    root = psutil.Process(int(pid))
    interval = max(0.01, float(interval_seconds))
    duration_limit = max(interval, float(duration_seconds))
    started_at = utc_now()
    started_monotonic = time.monotonic()
    accumulator = ResourceAccumulator()
    observation = LinuxObservation.start(root.pid)

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
        observation=observation,
    )
