from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from estimation.cli import main
from estimation.model import build_sample, canonical_process_uri, utc_now
from estimation.monitor import measure_command, observe_pid
from estimation.stats import aggregate_samples, estimate_workload
from estimation.store import append_sample, load_samples


def _sample(duration: float, memory: int, *, outcome: str = "succeeded"):
    return build_sample(
        process_uri="diagit://fleet/worktrees?root=/private/path",
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
    )


def test_canonical_uri_removes_query_and_fragment() -> None:
    assert canonical_process_uri("Diagit://fleet/worktrees?root=/tmp#x") == "diagit://fleet/worktrees"


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
