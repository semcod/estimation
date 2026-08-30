# Ticket 012: Add URI Process revision to sample v2 contract

- **ID**: ticket-012
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-30

## Goal and scope

Allow an explicit optional `process_revision` in v2 samples so Observability
can compare the current implementation with its previous revision. Never infer
revision identity from payload-bearing argv hashes.

## Acceptance criteria

- [x] AC-01: Scope is approved by the user's request to continue the version
  regression dashboard implementation.
- [x] AC-02: The closed v2 schema accepts a bounded revision and still accepts
  existing v2 records without it.

## Participants

- Human participant: user:tom; no synthesized user file was created.
- Agent participant: [ai-codex.md](ai-codex.md)
