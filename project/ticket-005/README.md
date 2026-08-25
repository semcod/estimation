# Ticket 005: Remove unavailable pytest governance plugin

- **ID**: ticket-005
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-25

## Goal and scope

Remove the generated pytest `addopts` reference to a plugin that is not
distributed by the adopted standard. Governance remains enforced by the
repository gate and CI; ordinary package tests must run in a clean venv.

## Acceptance criteria

- [x] AC-01: The session request authorizes the corrective change.
- [x] AC-02: Plain `python -m pytest -q` works without an undeclared plugin.
- [x] AC-03: The independent governance gate still passes.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
