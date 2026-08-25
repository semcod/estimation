---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-002
---
# Participant: codex (AI agent)

## Understanding

Static ETA values are insufficient. The scheduler needs empirical wall time,
CPU, peak RSS, I/O and process count bound to the same Process URI used by the
ticket. Samples must remain useful without leaking command arguments, output,
environment data, hostname or secrets.

## Execution plan

1. Measure a command or existing PID tree at a bounded interval.
2. Append a domain sample and a wellmanifest-compatible hash-chained event.
3. Aggregate successful history into p50/p90 and confidence.
4. Estimate quantity/parallelism resource envelopes.
5. Run unit tests and representative real processes.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Bound application implementation to integration ticket-001 and base
  `33ffdcdfcc702d720eb12e6aec84bf6c9dbe9ce3`.

## Blockers

- Control on port 8091 was unavailable during discovery, so baseline runs use
  local read-only repository processes rather than live production effects.
- New authority remains required for destructive action, secret access, new
  external coordination or material objective expansion. Protected delivery
  may be invoked without another prompt when publication is in scope; its
  exact-head trusted approval remains independent evidence.
