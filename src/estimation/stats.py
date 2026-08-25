from __future__ import annotations

from collections import defaultdict
import math
import statistics
from typing import Any, Iterable

from estimation.model import Sample, canonical_process_uri


METRICS = (
    "duration_seconds",
    "cpu_user_seconds",
    "cpu_system_seconds",
    "effective_cpu_cores",
    "peak_rss_bytes",
    "read_bytes",
    "write_bytes",
    "max_processes",
)


def _percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _confidence(successful_samples: int) -> str:
    if successful_samples == 0:
        return "none"
    if successful_samples < 3:
        return "low"
    if successful_samples < 10:
        return "medium"
    return "high"


def _metric_summary(values: list[float]) -> dict[str, float]:
    return {
        "min": min(values),
        "mean": statistics.fmean(values),
        "p50": _percentile(values, 0.50),
        "p90": _percentile(values, 0.90),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def aggregate_samples(samples: Iterable[Sample]) -> dict[str, Any]:
    groups: dict[str, list[Sample]] = defaultdict(list)
    for sample in samples:
        groups[sample.process_key].append(sample)

    processes: dict[str, Any] = {}
    for key, group in sorted(groups.items()):
        successful = [item for item in group if item.outcome in {"succeeded", "observed"}]
        metrics = {
            name: _metric_summary([float(getattr(item, name)) for item in successful])
            for name in METRICS
        } if successful else {}
        processes[key] = {
            "samples": len(group),
            "successful_samples": len(successful),
            "success_rate": len(successful) / len(group),
            "confidence": _confidence(len(successful)),
            "hosts": len({item.host_profile["host_id"] for item in group}),
            "metrics": metrics,
        }
    return {
        "schema": "semcod.estimation.report/v1",
        "processes": processes,
        "total_samples": sum(len(group) for group in groups.values()),
    }


def estimate_workload(
    samples: Iterable[Sample],
    process_uri: str,
    *,
    quantity: int = 1,
    parallelism: int = 1,
) -> dict[str, Any]:
    if quantity < 1 or parallelism < 1:
        raise ValueError("quantity and parallelism must be positive")
    key = canonical_process_uri(process_uri)
    report = aggregate_samples(samples)
    process = report["processes"].get(key)
    if not process or not process["metrics"]:
        raise ValueError(f"no successful samples for process {key}")
    metrics = process["metrics"]
    active_parallelism = min(quantity, parallelism)
    batches = math.ceil(quantity / active_parallelism)
    cpu_p90 = metrics["cpu_user_seconds"]["p90"] + metrics["cpu_system_seconds"]["p90"]
    return {
        "schema": "semcod.estimation.workload-estimate/v1",
        "process_key": key,
        "quantity": quantity,
        "parallelism": active_parallelism,
        "samples": process["samples"],
        "successful_samples": process["successful_samples"],
        "confidence": process["confidence"],
        "success_rate": process["success_rate"],
        "estimated_wall_seconds_p90": round(
            batches * metrics["duration_seconds"]["p90"], 6
        ),
        "cpu_seconds_p90_total": quantity * cpu_p90,
        "cpu_cores_p90_concurrent": active_parallelism * metrics["effective_cpu_cores"]["p90"],
        "memory_bytes_p90_concurrent": int(active_parallelism * metrics["peak_rss_bytes"]["p90"]),
        "read_bytes_p90_total": int(quantity * metrics["read_bytes"]["p90"]),
        "write_bytes_p90_total": int(quantity * metrics["write_bytes"]["p90"]),
        "max_processes_p90_concurrent": int(math.ceil(active_parallelism * metrics["max_processes"]["p90"])),
        "low_confidence": process["confidence"] in {"none", "low"},
    }
