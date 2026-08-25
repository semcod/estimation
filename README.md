# estimation

Empirical resource estimation for ticket-bound URI processes. The package
measures real process trees and learns conservative scheduling envelopes from
append-only history. Runtime ownership remains in `semcod`; Subactor retains
authority to decide whether a Process URI may execute.

## What is measured

- wall-clock duration and exit outcome;
- user/system CPU time and effective CPU cores;
- peak aggregate RSS for the process tree;
- read/write bytes where the operating system permits access;
- maximum process count, host capacity profile and sample count.

Raw command arguments, environment values, stdout, stderr and secret material
are never persisted. URI query strings and fragments are removed before a URI
is stored or used as the statistical key. Only the program name and an argv
SHA-256 fingerprint are retained.

## Install

```bash
python -m pip install -e .
```

## Measure a caller-authorized command

```bash
estimation run \
  --process-uri 'testql://project/suite/query/run' \
  --ticket PLF-1234 \
  --store ~/.local/state/semcod-estimation/process-samples.jsonl \
  --events ~/.local/state/semcod-estimation/process-events.jsonl \
  -- python -m pytest -q
```

The command's exit code is returned by `estimation`. Failed runs remain in
history and affect `success_rate`, but resource percentiles are based on
successful samples so an immediate startup failure does not look artificially
cheap.

## Observe an existing process tree

```bash
estimation observe \
  --pid 12345 \
  --duration 30 \
  --process-uri 'control://automation/watchdog/command/run' \
  --ticket PLF-1234
```

Observation is bounded by duration and does not signal, restart or otherwise
control the target process.

## Report and estimate

```bash
estimation validate --store ~/.local/state/semcod-estimation/process-samples.jsonl
estimation report --store ~/.local/state/semcod-estimation/process-samples.jsonl
estimation estimate \
  --store ~/.local/state/semcod-estimation/process-samples.jsonl \
  --process-uri 'testql://project/suite/query/run' \
  --quantity 20 \
  --parallelism 4
```

Reports expose p50, p90, mean, standard deviation, success rate and confidence.
Confidence is `none`, `low`, `medium` or `high` based on successful sample
count. Workload estimates multiply conservative p90 values by quantity and
parallelism to support queue admission and host-capacity planning.

## Subactor integration

1. Subactor resolves a ticket and authorized Process URI.
2. The executor wraps the actual command with `estimation run`, or observes a
   service PID with `estimation observe`.
3. Samples are appended to the node-local state store; a parallel hash-chained
   `wellmanifest.logs/event/v1` stream records the measurement outcome.
4. The scheduler queries `estimation://history/query/estimate` before admitting
   similar work and compares p90 CPU, RSS and duration with host capacity.
5. Missing or low-confidence history is a planning uncertainty, never implicit
   authorization to run a process.

The package adopts `wellmanifest/new-project` and `wellmanifest/logs`.
