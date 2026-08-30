# Ticket 011: Implement energy telemetry and URI Process opportunity ranking

- **ID**: ticket-011
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
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
- [x] AC-05: Functional tests, a v2 schema instance check, a live
  smoke test and governance pass.

## Validation evidence

- `/usr/bin/python3 -m pytest -q`: 14 passed.
- A generated v2 sample validates with Draft 2020-12 JSON Schema.
- A live `sleep` measurement and CPU opportunity query completed successfully.
- Runtime and CLI versions are regression-tested against package metadata.
- The live host exposed shared cgroup/PSI evidence but no readable RAPL domain;
  energy was correctly marked unavailable.

## Closure evidence

- Trusted implementation SHA: `0a6260977b8e75de64e491b549c6d611995e037d`.
- Protected Validator approved and explicitly merged PR #6.
- Main integration SHA: `e207b5182d289bd2db2b33b2b6d7cd105551cf30`.

## Participants

- Human participant: user:tom; authorization is recorded by the originating
  request and no synthesized user file was created.
- Agent participant: [ai-codex.md](ai-codex.md)
