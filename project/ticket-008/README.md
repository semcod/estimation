# Ticket 008: Reduce Process URI estimation overhead

- **ID**: ticket-008
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-25

## Goal and scope

Reduce the observer effect of Process URI estimation while preserving bounded,
append-only evidence. Use a one-second default sample interval and read only
the tail of the event log when extending its hash chain.

## Acceptance criteria

- [x] AC-01: Scope is approved by the user's request to measure and reduce
  Subactor resource consumption.
- [ ] AC-02: Command and PID observation default to one sample per second.
- [ ] AC-03: Appending an event does not scan the full historical JSONL file.
- [ ] AC-04: Tests prove the new defaults and bounded tail read.
- [ ] AC-05: Pytest and governance checks pass.

## Participants

- Human participant: user:tom; authorization is recorded by the originating
  request and no synthesized user file was created.
- Agent participant: [ai-codex.md](ai-codex.md)
