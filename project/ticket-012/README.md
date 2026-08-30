# Ticket 012: Add URI Process revision to sample v2 contract

- **ID**: ticket-012
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
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

- Human participant: user:tom; no synthesized user file was created.
- Agent participant: [ai-codex.md](ai-codex.md)

## Closure evidence

- Trusted implementation SHA: `c43e1eaac0a600c8a52d73a6639756353e00369c`.
- Protected Validator approved and explicitly merged PR #9.
- Main integration SHA: `4fbc1477fee93d72f14b13164b5f85a308a359b2`.
