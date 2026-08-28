# Ticket 009: Make governed estimation CI reproducible

- **ID**: ticket-009
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-25

## Goal and scope

Make governed CI reproduce the repository contract on Linux and Windows:
activate the managed Git hook before invoking pytest/governance and normalize
the Windows worktree to LF before validating hash-bound standard files.

## Acceptance criteria

- [x] AC-01: Scope is approved by the user's request to test and repair
  autonomy and publish all changes.
- [x] AC-02: Linux functional CI activates the managed hook.
- [x] AC-03: Windows governance preserves LF and activates the managed hook.
- [x] AC-04: Local pytest and governance pass.

## Participants

- Human participant: user:tom; authorization is recorded by the originating
  request and no synthesized user file was created.
- Agent participant: [ai-codex.md](ai-codex.md)

## Closure evidence

- Trusted implementation SHA: `e5c0eb612908780c9dd2b4a102e885d945a797c3`.
- Protected Validator run `33160322142` approved and explicitly merged PR #2.
- Main integration SHA: `4ff7e4d6e288697bac10e2008524f65c0e8280de`.
- Linux, Windows and governance checks were green on the frozen head.
