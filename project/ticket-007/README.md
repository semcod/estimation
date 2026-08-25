# Ticket 007: Use plain governed pytest in CI

- **ID**: ticket-007
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-25

## Goal and scope

Remove the CI override that disabled pytest addopts. The package-local bridge
from ticket-006 now makes plain pytest both functional and governed.

## Acceptance criteria

- [x] AC-01: The session request authorizes the corrective change.
- [x] AC-02: CI runs plain `python -m pytest -q`.
- [x] AC-03: Governance remains fail-closed through the pytest plugin.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
