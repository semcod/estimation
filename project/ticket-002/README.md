# Ticket 002: Measure and estimate URI process resources

- **ID**: ticket-002
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-25

## Goal and scope

Implement the application layer of the Process URI estimation contract from
ticket-001: process-tree sampling, append-only storage, wellmanifest log
events, aggregation and conservative scheduling estimates.

## Acceptance criteria

- [x] AC-01: The session request authorizes bounded implementation.
- [x] AC-02: A command and an existing PID can be sampled without storing raw
  output, environment values or argument text.
- [x] AC-03: Concurrent appends create an ordered logs-compatible hash chain.
- [x] AC-04: Reports expose p50/p90, success rate and confidence by canonical
  Process URI.
- [x] AC-05: Workload estimates account for quantity and parallelism.
- [x] AC-06: Unit and real-process baseline tests pass.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Closure evidence

- Trusted local integration SHA: `507229bf802ad039033b47d362d4a8439ecef783`.
- Post-merge functional tests: `6 passed`.
- Historical store validation: 15 valid samples.
- Governance: `GOV-PASS` with 0 errors and 0 warnings.
