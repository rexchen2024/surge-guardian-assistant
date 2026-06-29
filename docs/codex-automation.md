# Codex Automation Notes

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-automation.zh-CN.md) | [繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-automation.zh-TW.md)

Codex can be an independent Surge Sentry path for install, checks, explanation, review, and maintenance. Healthy checks still run through local scripts; Codex joins when the work needs judgment or improvement.

For installation steps, see [Codex Edition](codex-edition.md).

## Recommended Boundary

If you choose the Hermes path:

- Hermes cron runs the minute-level `tick`.
- `{"wakeAgent": false}` skips model work on healthy checks.
- Non-silent output wakes Hermes for model analysis and delivery.

If you choose the Codex path:

- daily or weekly repository review
- `scripts/check` verification
- privacy/redaction audits
- reviewing non-silent incident packages
- interpreting F1, World Cup Fox, Apple TV, or similar traffic-monitor reports
- diagnosing Surge config risks and proposing changes
- suggesting code or documentation improvements after repeated patterns

This keeps the healthy path lightweight while letting Codex do the judgment, explanation, and project maintenance work it is good at.

## Codex + Surge Variant

A Codex + Surge variant is viable when a user already relies on Codex automations, or wants to manage Surge Sentry through an open-source project and local workspace.

Usage guidance:

- the machine has Surge and Codex access to the local workspace
- the user wants periodic project or incident review
- the cadence is hourly, daily, or weekly
- model analysis is acceptable for each scheduled run
- minute-level health checks still run through local scripts such as `scripts/surge-sentry tick`

## Automation Prompt

Use `codex/automation-prompts/surge-sentry-review.md` as the starting prompt
for a Codex workspace automation. Point the automation at the repository root.

The prompt intentionally asks Codex to keep Surge config safety boundaries and avoid permanent Surge changes unless the user explicitly confirms them.

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
