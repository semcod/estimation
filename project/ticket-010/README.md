# Ticket 010: Measure energy and rank URI Process optimization opportunities

- **ID**: ticket-010
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-30

## Goal and scope

Version the package contract for optional, bounded Linux energy, cgroup v2 and
pressure evidence. Declare a read-only opportunity Process URI while keeping
the runtime implementation in the dependent application workstream.

## Acceptance criteria

- [x] AC-01: Scope is approved by the user's request to monitor local cost,
  energy and execution time and optimize the highest-cost URI Processes first.
- [x] AC-02: The closed v2 schema defines optional energy/cgroup/PSI evidence
  with explicit method, confidence and attribution.
- [x] AC-03: The operation catalog declares the bounded, read-only opportunity
  query with no authority to apply changes.
- [x] AC-04: Package metadata is versioned to 0.2.0.
- [x] AC-05: JSON validation and governance pass.

## Closure evidence

- Both JSON contracts parse successfully with Python's strict JSON parser.
- Repository governance reports `GOV-PASS` with no errors or warnings.
- Trusted implementation SHA: `a059d7a9e00498db7f60d449b213ab4a7ec4cbd0`.
- Protected Validator run `33309674658` approved and explicitly merged PR #7.
- Main integration SHA: `5ed903d4c8332a0ccbc6a5e4468ee898b7f448b0`.

## Participants

- Human participant: user:tom; authorization is recorded by the originating
  request and no synthesized user file was created.
- Agent participant: [ai-codex.md](ai-codex.md)
