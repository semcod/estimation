# Ticket 006: Implement pytest governance bridge

- **ID**: ticket-006
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-25

## Goal and scope

Implement the package-local `wellmanifest_governance` pytest plugin declared by
ticket-005. The plugin must run the configured governance gate exactly once,
fail closed and avoid recursive invocation.

## Acceptance criteria

- [x] AC-01: The session request authorizes the corrective change.
- [x] AC-02: Plain pytest loads the package-local plugin.
- [x] AC-03: The configured gate runs before tests and failures stop the run.
- [x] AC-04: A recursion guard prevents nested governance invocation.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
