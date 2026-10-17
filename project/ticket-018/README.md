# Ticket 018: Remediate PERF-AUDIT findings and adopt Wellmanifest standards

- **ID**: ticket-018
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-17

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: Explicit user request in active session to fix all `PERF-AUDIT-*` findings (`PERF-AUDIT-KWARG-001` in `src/estimation/monitor.py`) and adopt `wellmanifest/wellman` baseline standards in `.governance/standard-adoption.json`.

## Acceptance criteria

- [x] AC-01: `audit_repository` from `wellmanifest/performance` reports `0` findings across `semcod/estimation`.
- [x] AC-02: `.governance/standard-adoption.json` satisfies `python3 .governance/standard_pack_check.py --root .` with `findings=0`.
- [x] AC-03: `./project/governance-check.sh` and `pytest -q` pass.
