# Ticket 008: Reduce Process URI estimation overhead

- **ID**: ticket-008
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-25

## Goal and scope

Reduce the observer effect of Process URI estimation while preserving bounded,
append-only evidence. Use a one-second default sample interval and read only
the tail of the event log when extending its hash chain.

## Acceptance criteria

- [x] AC-01: Scope is approved by the user's request to measure and reduce
  Subactor resource consumption.
- [x] AC-02: Command and PID observation default to one sample per second.
- [x] AC-03: Appending an event does not scan the full historical JSONL file.
- [x] AC-04: Tests prove the new defaults and bounded tail read.
- [x] AC-05: Pytest and governance checks pass.

## Participants

- Human participant: user:tom; authorization is recorded by the originating
  request and no synthesized user file was created.
- Agent participant: [ai-codex.md](ai-codex.md)

## Closure evidence

- Trusted implementation SHA: `53cf54cf5cd0e3214191de4ef0d931beeda6c590`.
- Protected Validator run `33160630219` approved and explicitly merged PR #3.
- Main integration SHA: `a60f6b4ad89b79dab842db45ce8a469664bc3513`.
- Ten functional tests and governance with no findings passed before publication.
