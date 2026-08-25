# Ticket 005: Remove unavailable pytest governance plugin

- **ID**: ticket-005
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-25

## Goal and scope

Retain the governance-required pytest `addopts` and declare a local
`wellmanifest_governance` module. A dependent application ticket implements
the plugin so ordinary package tests run in a clean venv.

## Acceptance criteria

- [x] AC-01: The session request authorizes the corrective change.
- [x] AC-02: Package metadata declares the local plugin module.
- [x] AC-03: Pytest retains the governance-required plugin binding.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Closure evidence

- Trusted local integration SHA: `16844aa8c277e8b96f4cca8aca57f4d42ec2a4eb`.
- Post-merge governance: `GOV-PASS` with no findings.
