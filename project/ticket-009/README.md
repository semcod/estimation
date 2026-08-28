# Ticket 009: Make governed estimation CI reproducible

- **ID**: ticket-009
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-25

## Goal and scope

Make governed CI reproduce the repository contract on Linux and Windows:
activate the managed Git hook before invoking pytest/governance and normalize
the Windows worktree to LF before validating hash-bound standard files.

## Acceptance criteria

- [x] AC-01: Scope is approved by the user's request to test and repair
  autonomy and publish all changes.
- [ ] AC-02: Linux functional CI activates the managed hook.
- [ ] AC-03: Windows governance preserves LF and activates the managed hook.
- [ ] AC-04: Local pytest and governance pass.

## Participants

- Human participant: user:tom; authorization is recorded by the originating
  request and no synthesized user file was created.
- Agent participant: [ai-codex.md](ai-codex.md)
