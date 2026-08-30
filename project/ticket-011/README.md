# Ticket 011: Implement energy telemetry and URI Process opportunity ranking

- **ID**: ticket-011
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-30

## Goal and scope

Implement the v2 measurement contract declared by ticket-010. Observe optional
RAPL, cgroup v2 and PSI counters without controlling the process. Rank recurring
Process URIs independently by CPU, wall time, energy or I/O savings potential.
Accept an explicit process revision for version-over-version regression analysis.

## Acceptance criteria

- [x] AC-01: Scope is approved by the originating user request.
- [x] AC-02: Existing v1 samples remain readable and v2 telemetry discloses
  method, attribution and confidence.
- [x] AC-03: Ranking requires twelve comparable samples by default and never
  combines unlike resource units into an implicit score.
- [x] AC-04: CLI tests cover the opportunity query.
- [x] AC-05: Fourteen functional tests, a v2 schema instance check, a live
  smoke test and governance pass.

## Validation evidence

- `/usr/bin/python3 -m pytest -q`: 14 passed.
- A generated v2 sample validates with Draft 2020-12 JSON Schema.
- A live `sleep` measurement and CPU opportunity query completed successfully.
- The live host exposed shared cgroup/PSI evidence but no readable RAPL domain;
  energy was correctly marked unavailable.

## Participants

- Human participant: user:tom; authorization is recorded by the originating
  request and no synthesized user file was created.
- Agent participant: [ai-codex.md](ai-codex.md)
