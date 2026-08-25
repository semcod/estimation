# Ticket 003: Repository hygiene and usage documentation

- **ID**: ticket-003
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-25

## Goal and scope

Publish the operator and integration documentation, prevent generated Python
artifacts from entering changesets, and materialize the adopted host/check
configuration required by `wellmanifest/new-project`.

## Acceptance criteria

- [x] AC-01: The session request authorizes implementation.
- [x] AC-02: README documents measurement, observation, reporting and workload
  estimation without granting execution authority.
- [x] AC-03: Generated Python artifacts are ignored.
- [x] AC-04: Required checks have a repository-local exported declaration.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
