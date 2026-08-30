from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
import sys

import pytest

from estimation.cli import main
from estimation.model import Sample, build_sample, canonical_process_revision, canonical_process_uri, utc_now
from estimation.monitor import measure_command, observe_pid
from estimation.stats import aggregate_samples, estimate_workload, rank_opportunities
from estimation.store import append_sample, load_samples
import estimation.store as store_module


def _sample(duration: float, memory: int, *, outcome: str = "succeeded", process_uri: str = "diagit://fleet/worktrees", energy_joules: float | None = None):
    return build_sample(
        process_uri=process_uri + "?root=/private/path",
        process_key=None,
        ticket_id="PLF-TEST",
        correlation_id=None,
        started_at=utc_now(),
        finished_at=utc_now(),
        duration_seconds=duration,
        cpu_user_seconds=duration / 2,
        cpu_system_seconds=duration / 10,
        peak_rss_bytes=memory,
        read_bytes=100,
        write_bytes=50,
        max_processes=2,
        sample_count=3,
        exit_code=0 if outcome == "succeeded" else 1,
        outcome=outcome,
        program="diagit",
        argv=["diagit", "--secret-value", "never-store-me"],
        energy={
            "joules": energy_joules,
            "method": "rapl_cpu_share" if energy_joules is not None else "unavailable",
            "confidence": "low" if energy_joules is not None else "none",
            "domains": 1 if energy_joules is not None else 0,
        },
    )


def test_canonical_uri_removes_query_and_fragment() -> None:
    assert canonical_process_uri("Diagit://fleet/worktrees?root=/tmp#x") == "diagit://fleet/worktrees"


def test_process_revision_is_explicit_and_bounded() -> None:
    assert canonical_process_revision("git:abc123") == "git:abc123"
    assert canonical_process_revision("") is None
    with pytest.raises(ValueError, match="unsupported characters"):
        canonical_process_revision("revision with spaces")


def test_measure_command_and_store_do_not_persist_arguments(tmp_path: Path) -> None:
    sample = measure_command(
        [sys.executable, "-c", "sum(i*i for i in range(10000))", "secret-marker"],
        process_uri="python://local/command/benchmark?token=hidden",
        ticket_id="PLF-TEST",
        interval_seconds=0.01,
    )
    store = tmp_path / "samples.jsonl"
    events = tmp_path / "events.jsonl"
    append_sample(sample, store, events)

    assert sample.outcome == "succeeded"
    assert sample.duration_seconds > 0
    assert sample.sample_count >= 1
    assert "secret-marker" not in store.read_text(encoding="utf-8")
    assert "token=hidden" not in sample.process_key
    assert "token=hidden" not in store.read_text(encoding="utf-8")
    assert load_samples(store)[0].argv_sha256 == sample.argv_sha256
    assert sample.schema == "semcod.estimation.sample/v2"
    assert sample.energy is not None
    assert sample.kernel is not None
    assert sample.kernel["attribution"] in {"shared", "unavailable"}


def test_v1_sample_remains_readable() -> None:
    payload = _sample(1.0, 100).to_dict()
    payload["schema"] = "semcod.estimation.sample/v1"
    payload.pop("energy")
    payload.pop("kernel")
    restored = Sample.from_dict(payload)
    assert restored.schema == "semcod.estimation.sample/v1"
    assert restored.energy["method"] == "unavailable"
    assert restored.kernel["attribution"] == "unavailable"


def test_event_store_builds_a_hash_chain(tmp_path: Path) -> None:
    store = tmp_path / "samples.jsonl"
    events = tmp_path / "events.jsonl"
    append_sample(_sample(1.0, 100), store, events)
    append_sample(_sample(2.0, 200), store, events)
    rows = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]

    assert [row["sequence"] for row in rows] == [1, 2]
    assert rows[1]["previousHash"] == rows[0]["eventHash"]
    assert all(row["rawOutputIncluded"] is False for row in rows)
    assert all(row["secretMaterialIncluded"] is False for row in rows)


def test_monitor_defaults_to_one_hertz() -> None:
    assert inspect.signature(measure_command).parameters["interval_seconds"].default == 1.0
    assert inspect.signature(observe_pid).parameters["interval_seconds"].default == 1.0


def test_event_append_reads_only_bounded_tail(tmp_path: Path, monkeypatch) -> None:
    store = tmp_path / "samples.jsonl"
    events = tmp_path / "events.jsonl"
    for index in range(1000):
        append_sample(_sample(float(index + 1), index + 1), store, events)

    original_pread = store_module.os.pread
    bytes_read = 0

    def measured_pread(fd: int, size: int, offset: int) -> bytes:
        nonlocal bytes_read
        chunk = original_pread(fd, size, offset)
        bytes_read += len(chunk)
        return chunk

    monkeypatch.setattr(store_module.os, "pread", measured_pread)
    append_sample(_sample(1001.0, 1001), store, events)
    assert bytes_read <= 4096


def test_report_and_workload_estimate_use_successful_p90() -> None:
    samples = [_sample(1.0, 100), _sample(2.0, 200), _sample(3.0, 300), _sample(20.0, 999, outcome="failed")]
    report = aggregate_samples(samples)
    process = report["processes"]["diagit://fleet/worktrees"]

    assert process["samples"] == 4
    assert process["successful_samples"] == 3
    assert process["confidence"] == "medium"
    estimate = estimate_workload(samples, "diagit://fleet/worktrees", quantity=8, parallelism=2)
    assert estimate["estimated_wall_seconds_p90"] == 11.2
    assert estimate["memory_bytes_p90_concurrent"] == 560
    assert estimate["low_confidence"] is False


def test_opportunities_rank_absolute_savings_for_explicit_objective() -> None:
    samples = [
        *[_sample(10.0, 100, process_uri="task://slow/work") for _ in range(12)],
        *[_sample(2.0, 100, process_uri="task://fast/work") for _ in range(12)],
        *[_sample(100.0, 100, process_uri="task://one-off/work") for _ in range(2)],
    ]
    result = rank_opportunities(samples, objective="cpu", reduction_fraction=0.25)
    assert [item["process_key"] for item in result["ranking"]] == ["task://slow/work", "task://fast/work"]
    assert result["ranking"][0]["potential_saving"] == 18.0
    assert result["excluded"][0]["process_key"] == "task://one-off/work"
    assert result["advisory_only"] is True


def test_energy_opportunities_disclose_coverage_and_ignore_missing_values() -> None:
    samples = [
        *[_sample(1.0, 100, process_uri="task://energy/a", energy_joules=5.0) for _ in range(12)],
        *[_sample(1.0, 100, process_uri="task://energy/b") for _ in range(12)],
    ]
    result = rank_opportunities(samples, objective="energy")
    assert result["ranking"][0]["potential_saving"] == 18.0
    assert result["ranking"][0]["coverage"] == 1.0
    assert result["excluded"][0]["objective_samples"] == 0


def test_cli_prints_opportunity_ranking(tmp_path: Path, capsys) -> None:
    store = tmp_path / "samples.jsonl"
    events = tmp_path / "events.jsonl"
    for _ in range(12):
        append_sample(_sample(1.0, 100), store, events)
    assert main(["opportunities", "--store", str(store), "--objective", "wall"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ranking"][0]["process_key"] == "diagit://fleet/worktrees"


def test_cli_quiet_run_persists_without_mixing_sample_into_stdout(tmp_path: Path, capfd) -> None:
    store = tmp_path / "samples.jsonl"
    events = tmp_path / "events.jsonl"
    assert main([
        "run", "--process-uri", "test://quiet/run", "--store", str(store),
        "--events", str(events), "--interval", "0.01", "--process-revision", "git:abc123", "--quiet", "--",
        sys.executable, "-c", "print('handler-output')",
    ]) == 0
    assert capfd.readouterr().out.strip() == "handler-output"
    assert load_samples(store)[0].process_key == "test://quiet/run"
    assert load_samples(store)[0].process_revision == "git:abc123"


def test_observe_current_process_is_bounded() -> None:
    sample = observe_pid(
        os.getpid(),
        process_uri="process://local/query/observe",
        duration_seconds=0.03,
        interval_seconds=0.01,
    )
    assert sample.outcome == "observed"
    assert sample.sample_count >= 1
    assert sample.peak_rss_bytes > 0


def test_cli_validates_written_store(tmp_path: Path) -> None:
    store = tmp_path / "samples.jsonl"
    events = tmp_path / "events.jsonl"
    append_sample(_sample(1.0, 100), store, events)
    assert main(["validate", "--store", str(store)]) == 0
