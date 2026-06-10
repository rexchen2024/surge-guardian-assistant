# Codex Automation Option

[English](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/codex-automation.md) | [简体中文](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/codex-automation.zh-CN.md)

Codex can be an optional analysis and maintenance layer for this project. It is
not the primary runtime path.

## Recommended Boundary

Keep Hermes as the production guardian runtime:

- Hermes cron runs the minute-level `tick`.
- `{"wakeAgent": false}` skips model work on healthy checks.
- Non-silent output wakes Hermes for model analysis and delivery.

Use Codex automation for lower-frequency work:

- daily or weekly repository review
- `scripts/check` verification
- privacy/redaction audits
- reviewing non-silent incident packages
- suggesting code or documentation improvements after repeated patterns

This keeps the cheap path cheap. A Codex cron job is useful, but it still starts
a Codex task, so it should not replace Hermes' lightweight gate for every
minute-level healthy check.

## Codex + Surge Variant

A Codex + Surge variant is viable when a user already relies on Codex
automations and wants project maintenance or incident analysis in Codex.

Good fit:

- the machine has Surge and Codex access to the local workspace
- the user wants periodic project or incident review
- the cadence is hourly, daily, or weekly
- model analysis is acceptable for each scheduled run

Poor fit:

- strict minute-level always-on monitoring
- very low power or low bandwidth machines
- users who want no model invocation during healthy checks
- notification routing that already works better through Hermes

## Automation Prompt

Use `codex/automation-prompts/surge-guardian-review.md` as the starting prompt
for a Codex workspace automation. Point the automation at the repository root.

The prompt intentionally asks Codex to treat Hermes as the default runtime and
to avoid permanent Surge changes unless the user explicitly confirms them.

## Safety Rules

- Do not paste raw Surge profiles, subscriptions, request bodies, or private
  logs into Codex prompts.
- Prefer `scripts/check`, `doctor`, summarized state, and non-silent incident
  packages.
- Do not let a Codex automation edit Surge profiles directly.
- Keep permanent routing, DNS, certificate, server, MITM, Rewrite, Scripting,
  Replica, reload, and restart changes behind explicit user confirmation.
- If a run finds no actionable issue, the final answer should be short and
  avoid notification noise.
