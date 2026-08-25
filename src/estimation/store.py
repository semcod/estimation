from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

from estimation.model import Sample, utc_now


ZERO_HASH = "0" * 64


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@contextmanager
def _locked_file(path: Path) -> Iterator[Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield handle
        finally:
            handle.flush()
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _append_line(path: Path, payload: dict[str, Any]) -> None:
    with _locked_file(path) as handle:
        handle.seek(0, 2)
        handle.write(_canonical_json(payload) + "\n")


def _last_event(handle: Any) -> tuple[int, str]:
    handle.seek(0)
    last: dict[str, Any] | None = None
    for raw_line in handle:
        line = raw_line.strip()
        if line:
            last = json.loads(line)
    if last is None:
        return 0, ZERO_HASH
    return int(last["sequence"]), str(last["eventHash"])


def _append_event(sample: Sample, path: Path) -> dict[str, Any]:
    with _locked_file(path) as handle:
        sequence, previous_hash = _last_event(handle)
        sample_hex = sample.sample_id.removeprefix("sample:")
        succeeded = sample.outcome in {"succeeded", "observed"}
        event: dict[str, Any] = {
            "schema": "wellmanifest.logs/event/v1",
            "eventId": f"event:estimation:{sample_hex}",
            "stream": "estimation.resources",
            "sequence": sequence + 1,
            "eventType": "estimation.sample_recorded",
            "severity": "INFO" if succeeded else "ERROR",
            "mode": "APPLY",
            "occurredAt": utc_now(),
            "correlationId": sample.correlation_id,
            "causationId": sample.ticket_id,
            "producer": "service:semcod.estimation",
            "source": "semcod.estimation",
            "code": None if succeeded else "ESTIMATION-PROCESS-001",
            "subjectRef": f"estimation:sample/{sample_hex}",
            "outcome": "SUCCEEDED" if succeeded else "FAILED",
            "subjectState": sample.outcome,
            "evidence": [],
            "inputHash": sample.argv_sha256,
            "receiptRef": f"receipt://estimation/sample/{sample_hex}",
            "previousHash": previous_hash,
            "rawOutputIncluded": False,
            "secretMaterialIncluded": False,
        }
        event["eventHash"] = hashlib.sha256(_canonical_json(event).encode("utf-8")).hexdigest()
        handle.seek(0, 2)
        handle.write(_canonical_json(event) + "\n")
        return event


def append_sample(sample: Sample, store_path: str | Path, events_path: str | Path) -> dict[str, Any]:
    _append_line(Path(store_path), sample.to_dict())
    return _append_event(sample, Path(events_path))


def load_samples(path: str | Path) -> list[Sample]:
    source = Path(path)
    if not source.exists():
        return []
    samples: list[Sample] = []
    for line_number, raw_line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            samples.append(Sample.from_dict(json.loads(line)))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid sample at line {line_number}: {error}") from error
    return samples
