from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Sequence

from estimation.model import Sample
from estimation.monitor import measure_command, observe_pid
from estimation.stats import aggregate_samples, estimate_workload
from estimation.store import append_sample, load_samples


DEFAULT_STORE = os.getenv("ESTIMATION_STORE", "data/samples.jsonl")
DEFAULT_EVENTS = os.getenv("ESTIMATION_EVENTS", "logs/estimation.jsonl")


def _context(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--process-uri", default=os.getenv("SUBACTOR_PROCESS_URI"))
    parser.add_argument("--process-key")
    parser.add_argument("--ticket", default=os.getenv("SUBACTOR_TICKET_ID"))
    parser.add_argument("--correlation-id", default=os.getenv("SUBACTOR_CORRELATION_ID"))
    parser.add_argument("--store", default=DEFAULT_STORE)
    parser.add_argument("--events", default=DEFAULT_EVENTS)
    parser.add_argument("--interval", type=float, default=1.0)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="estimation")
    parser.add_argument("--version", action="version", version="estimation 0.1.0")
    commands = parser.add_subparsers(dest="command_name", required=True)

    run = commands.add_parser("run", help="measure a caller-authorized command")
    _context(run)
    run.add_argument("command", nargs=argparse.REMAINDER)

    observe = commands.add_parser("observe", help="observe an existing PID tree")
    _context(observe)
    observe.add_argument("--pid", required=True, type=int)
    observe.add_argument("--duration", type=float, default=10.0)

    report = commands.add_parser("report", help="aggregate historical samples")
    report.add_argument("--store", default=DEFAULT_STORE)

    estimate = commands.add_parser("estimate", help="estimate a future workload")
    estimate.add_argument("--store", default=DEFAULT_STORE)
    estimate.add_argument("--process-uri", required=True)
    estimate.add_argument("--quantity", type=int, default=1)
    estimate.add_argument("--parallelism", type=int, default=1)

    validate = commands.add_parser("validate", help="validate all stored samples")
    validate.add_argument("--store", default=DEFAULT_STORE)
    return parser


def _require_process_uri(value: str | None) -> str:
    if not value:
        raise ValueError("--process-uri or SUBACTOR_PROCESS_URI is required")
    return value


def _write_sample(sample: Sample, args: argparse.Namespace) -> None:
    append_sample(sample, Path(args.store), Path(args.events))
    print(json.dumps(sample.to_dict(), ensure_ascii=False, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    try:
        if args.command_name == "run":
            command = list(args.command)
            if command and command[0] == "--":
                command = command[1:]
            sample = measure_command(
                command,
                process_uri=_require_process_uri(args.process_uri),
                process_key=args.process_key,
                ticket_id=args.ticket,
                correlation_id=args.correlation_id,
                interval_seconds=args.interval,
            )
            _write_sample(sample, args)
            return int(sample.exit_code or 0)
        if args.command_name == "observe":
            sample = observe_pid(
                args.pid,
                process_uri=_require_process_uri(args.process_uri),
                process_key=args.process_key,
                ticket_id=args.ticket,
                correlation_id=args.correlation_id,
                interval_seconds=args.interval,
                duration_seconds=args.duration,
            )
            _write_sample(sample, args)
            return 0
        samples = load_samples(args.store)
        if args.command_name == "report":
            print(json.dumps(aggregate_samples(samples), indent=2, sort_keys=True))
            return 0
        if args.command_name == "estimate":
            result = estimate_workload(
                samples,
                args.process_uri,
                quantity=args.quantity,
                parallelism=args.parallelism,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.command_name == "validate":
            print(json.dumps({"ok": True, "samples": len(samples), "store": str(args.store)}))
            return 0
    except (OSError, ValueError) as error:
        print(f"estimation: {error}", file=sys.stderr)
        return 2
    return 2
