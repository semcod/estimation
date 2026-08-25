# Ticket 004: Continuous integration for estimation package

- **ID**: ticket-004
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-25

## Goal and scope

Add the repository workflow required by the adopted governance contract. Keep
the published job names aligned with both required-check declarations.

## Acceptance criteria

- [x] AC-01: The session request authorizes implementation.
- [x] AC-02: Linux installs the package and runs its functional tests.
- [x] AC-03: Windows runs the generated governance gate.
- [x] AC-04: Job names are exactly `test` and `windows-governance`.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Closure evidence

- Trusted local integration SHA: `200982061c31e54e147843e3d29602d26e32baf9`.
- Post-merge check: `GOV-PASS` with 0 errors and 0 warnings.
