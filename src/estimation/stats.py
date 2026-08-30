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

OPPORTUNITY_OBJECTIVES = {
    "cpu": "CPU seconds",
    "wall": "wall seconds",
    "energy": "joules",
    "io": "I/O bytes",
}


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
        energy_values = [
            float(item.energy["joules"])
            for item in successful
            if item.energy and isinstance(item.energy.get("joules"), (int, float))
        ]
        processes[key] = {
            "samples": len(group),
            "successful_samples": len(successful),
            "success_rate": len(successful) / len(group),
            "confidence": _confidence(len(successful)),
            "hosts": len({item.host_profile["host_id"] for item in group}),
            "metrics": metrics,
            "energy": {
                "samples": len(energy_values),
                "coverage": len(energy_values) / len(successful) if successful else 0.0,
                "joules": _metric_summary(energy_values) if energy_values else {},
            },
        }
    return {
        "schema": "semcod.estimation.report/v2",
        "processes": processes,
        "total_samples": sum(len(group) for group in groups.values()),
    }


def _objective_value(sample: Sample, objective: str) -> float | None:
    if objective == "cpu":
        return float(sample.cpu_user_seconds + sample.cpu_system_seconds)
    if objective == "wall":
        return float(sample.duration_seconds)
    if objective == "io":
        return float(sample.read_bytes + sample.write_bytes)
    if objective == "energy":
        value = sample.energy.get("joules") if sample.energy else None
        return float(value) if isinstance(value, (int, float)) else None
    raise ValueError(f"unsupported objective {objective!r}; choose from {', '.join(OPPORTUNITY_OBJECTIVES)}")


def rank_opportunities(
    samples: Iterable[Sample],
    *,
    objective: str = "cpu",
    minimum_samples: int = 12,
    reduction_fraction: float = 0.30,
) -> dict[str, Any]:
    if objective not in OPPORTUNITY_OBJECTIVES:
        raise ValueError(f"unsupported objective {objective!r}; choose from {', '.join(OPPORTUNITY_OBJECTIVES)}")
    if minimum_samples < 1:
        raise ValueError("minimum_samples must be positive")
    if not 0 < reduction_fraction <= 1:
        raise ValueError("reduction_fraction must be greater than zero and at most one")

    groups: dict[str, list[Sample]] = defaultdict(list)
    for sample in samples:
        if sample.outcome in {"succeeded", "observed"}:
            groups[sample.process_key].append(sample)

    ranked: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for key, group in sorted(groups.items()):
        values = [value for item in group if (value := _objective_value(item, objective)) is not None]
        record = {
            "process_key": key,
            "successful_samples": len(group),
            "objective_samples": len(values),
            "coverage": len(values) / len(group),
            "confidence": _confidence(len(values)),
        }
        if len(values) < minimum_samples:
            excluded.append({**record, "reason": "insufficient_objective_samples"})
            continue
        total = sum(values)
        ranked.append({
            **record,
            "observed_total": round(total, 6),
            "p90_per_execution": round(_percentile(values, 0.90), 6),
            "potential_saving": round(total * reduction_fraction, 6),
        })

    ranked.sort(key=lambda item: (-item["potential_saving"], item["process_key"]))
    for position, item in enumerate(ranked, 1):
        item["rank"] = position
    return {
        "schema": "semcod.estimation.opportunities/v1",
        "objective": objective,
        "unit": OPPORTUNITY_OBJECTIVES[objective],
        "minimum_samples": minimum_samples,
        "reduction_fraction": reduction_fraction,
        "ranking": ranked,
        "excluded": excluded,
        "advisory_only": True,
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
