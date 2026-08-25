# Ticket 001: Process URI estimation package contract

- **ID**: ticket-001
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-25

## Goal and scope

Define a standalone Semcod package contract for measuring and estimating the
resource envelope of ticket-bound Process URI executions. Adopt
`wellmanifest/new-project` and `wellmanifest/logs`; do not move execution
authority out of Subactor.

## Acceptance criteria

- [x] AC-01: The session request authorizes implementation without a redundant
  confirmation.
- [x] AC-02: Package metadata exposes the `estimation` CLI.
- [x] AC-03: A versioned, privacy-preserving sample schema is published.
- [x] AC-04: Command and query Process URIs are explicitly classified.
- [x] AC-05: A separate application workstream implements and tests this contract.

## Closure evidence

- Trusted local integration SHA: `33ffdcdfcc702d720eb12e6aec84bf6c9dbe9ce3`.
- Post-merge checks: package metadata and both JSON contracts were parsed;
  application tests passed `6/6` on 2026-08-25.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
