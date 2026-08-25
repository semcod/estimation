# Ticket 007: Use plain governed pytest in CI

- **ID**: ticket-007
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
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

## Closure evidence

- Trusted local integration SHA: `a4dba00efb3d84b43df37458a2c9d469b5a7b0e4`.
- Plain governed pytest passed `8/8` tests.
- Explicit governance check passed with no findings.
