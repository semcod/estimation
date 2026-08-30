from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import re
from typing import Any, Sequence
from urllib.parse import urlsplit, urlunsplit
import uuid

import psutil


SAMPLE_SCHEMA = "semcod.estimation.sample/v2"
SUPPORTED_SAMPLE_SCHEMAS = {"semcod.estimation.sample/v1", SAMPLE_SCHEMA}
PROCESS_REVISION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/+\-]{0,127}$")


def unavailable_energy() -> dict[str, Any]:
    return {
        "joules": None,
        "method": "unavailable",
        "confidence": "none",
        "domains": 0,
    }


def unavailable_kernel_observation() -> dict[str, Any]:
    return {
        "cgroup_id": None,
        "attribution": "unavailable",
        "cpu_seconds": None,
        "memory_peak_bytes": None,
        "read_bytes": None,
        "write_bytes": None,
        "pids_peak": None,
        "pressure": {
            "cpu_some_seconds": None,
            "io_some_seconds": None,
            "memory_some_seconds": None,
        },
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_process_uri(value: str) -> str:
    raw = str(value or "").strip()
    parsed = urlsplit(raw)
    if not parsed.scheme:
        raise ValueError("process URI must include a scheme")
    canonical = urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path, "", ""))
    if len(canonical) < 3:
        raise ValueError("process URI is too short")
    return canonical[:320]


def canonical_process_revision(value: str | None) -> str | None:
    revision = str(value or "").strip()
    if not revision:
        return None
    if not PROCESS_REVISION.fullmatch(revision):
        raise ValueError("process revision contains unsupported characters")
    return revision


def argv_sha256(argv: Sequence[str]) -> str:
    encoded = json.dumps(list(argv), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def host_profile() -> dict[str, Any]:
    node = platform.node() or "unknown"
    host_id = hashlib.sha256(node.encode("utf-8")).hexdigest()[:16]
    return {
        "host_id": f"host:{host_id}",
        "system": platform.system()[:32],
        "machine": platform.machine()[:32],
        "cpu_count": int(psutil.cpu_count(logical=True) or os.cpu_count() or 1),
        "memory_bytes": int(psutil.virtual_memory().total),
    }


@dataclass(frozen=True)
class Sample:
    schema: str
    sample_id: str
    process_uri: str
    process_key: str
    ticket_id: str | None
    correlation_id: str
    started_at: str
    finished_at: str
    duration_seconds: float
    cpu_user_seconds: float
    cpu_system_seconds: float
    effective_cpu_cores: float
    peak_rss_bytes: int
    read_bytes: int
    write_bytes: int
    max_processes: int
    sample_count: int
    exit_code: int | None
    outcome: str
    program: str
    argv_sha256: str
    host_profile: dict[str, Any]
    raw_output_included: bool = False
    secret_material_included: bool = False
    energy: dict[str, Any] | None = None
    kernel: dict[str, Any] | None = None
    process_revision: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Sample":
        if payload.get("schema") not in SUPPORTED_SAMPLE_SCHEMAS:
            raise ValueError("unsupported estimation sample schema")
        normalized = dict(payload)
        normalized.setdefault("energy", unavailable_energy())
        normalized.setdefault("kernel", unavailable_kernel_observation())
        return cls(**normalized)


def build_sample(
    *,
    process_uri: str,
    process_key: str | None,
    ticket_id: str | None,
    correlation_id: str | None,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    cpu_user_seconds: float,
    cpu_system_seconds: float,
    peak_rss_bytes: int,
    read_bytes: int,
    write_bytes: int,
    max_processes: int,
    sample_count: int,
    exit_code: int | None,
    outcome: str,
    program: str,
    argv: Sequence[str],
    energy: dict[str, Any] | None = None,
    kernel: dict[str, Any] | None = None,
    process_revision: str | None = None,
) -> Sample:
    canonical = canonical_process_uri(process_uri)
    duration = max(0.0, float(duration_seconds))
    cpu_total = max(0.0, float(cpu_user_seconds) + float(cpu_system_seconds))
    sample_hex = uuid.uuid4().hex
    return Sample(
        schema=SAMPLE_SCHEMA,
        sample_id=f"sample:{sample_hex}",
        process_uri=canonical,
        process_key=str(process_key or canonical)[:320],
        ticket_id=str(ticket_id)[:128] if ticket_id else None,
        correlation_id=str(correlation_id or f"corr:{sample_hex}")[:128],
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=round(duration, 6),
        cpu_user_seconds=round(max(0.0, float(cpu_user_seconds)), 6),
        cpu_system_seconds=round(max(0.0, float(cpu_system_seconds)), 6),
        effective_cpu_cores=round(cpu_total / duration, 6) if duration else 0.0,
        peak_rss_bytes=max(0, int(peak_rss_bytes)),
        read_bytes=max(0, int(read_bytes)),
        write_bytes=max(0, int(write_bytes)),
        max_processes=max(0, int(max_processes)),
        sample_count=max(1, int(sample_count)),
        exit_code=exit_code,
        outcome=outcome,
        program=os.path.basename(program)[:128] or "unknown",
        argv_sha256=argv_sha256(argv),
        host_profile=host_profile(),
        energy=energy or unavailable_energy(),
        kernel=kernel or unavailable_kernel_observation(),
        process_revision=canonical_process_revision(process_revision),
    )
