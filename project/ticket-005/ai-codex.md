---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-005
---
# Participant: codex (AI agent)

## Understanding

Functional tests pass only when overriding generated pytest addopts because
`wellmanifest_governance` is absent from both the standard and environments;
the package therefore needs to provide the bounded plugin locally.

## Execution plan

1. Retain the governance-required pytest addopts.
2. Declare the local plugin module in package metadata.
3. Implement the plugin in a dependent application ticket.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Declared a package-local governance plugin contract.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination or material objective expansion. Protected delivery
  may be invoked without another prompt when publication is in scope; its
  exact-head trusted approval remains independent evidence.
