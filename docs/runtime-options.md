# Runtime Options

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/runtime-options.zh-CN.md)

Surge Guardian Assistant has one core loop and three practical ways to run it.

## Recommended: Surge + Hermes

Use this when you want autonomous checks, model analysis, and delivery through
your existing Hermes channels.

- `scripts/surge-guardian-assistant tick` performs the deterministic local check.
- Healthy output is exactly `{"wakeAgent": false}`.
- Non-silent output becomes the evidence package for Hermes.
- Hermes decides whether to stay silent, report an already-handled issue, or ask
  for confirmation before a risky action.

This is the strongest mode because Hermes supplies scheduling, model reasoning,
memory, and notification delivery without adding those responsibilities to the
guardian core.

For production use, keep this as the default deployment path. The guardian's
`{"wakeAgent": false}` contract is designed for Hermes cron: healthy checks can
complete without a model call, while incident packages wake the agent only when
evidence justifies it.

For installation steps, see [Hermes Edition](hermes-edition.md).

## Local-Only: Surge Without Hermes

Use this when the machine has Surge but does not run Hermes.

What still works:

- log and event inspection
- repeated-error counters
- external resource retry
- DNS flush
- policy retest
- narrow temporary runtime rules
- temp-rule cleanup and state reconciliation
- `doctor`, `tick`, and `redact-check`

What does not happen automatically:

- model analysis
- chat-style explanation
- cross-session learning through Hermes memory
- delivery through Telegram, Discord, Matrix, Weixin, Feishu, Signal, or other
  Hermes channels

Run it from launchd, cron, or another local scheduler. A minimal launchd job can
call:

```bash
/path/to/surge-guardian-assistant/scripts/surge-guardian-assistant tick >> "$HOME/Library/Logs/surge-guardian-assistant.log" 2>&1
```

In local-only mode, monitor the log for any line that is not:

```json
{"wakeAgent": false}
```

This mode is deliberately simple. It keeps the deterministic safety behavior but
does not pretend to replace an agent runtime.

## Codex-Assisted

Codex can help inspect the repository, review local state, and analyze incident
logs when a person asks it to. Codex is useful for maintenance and deeper
debugging, but it should not be treated as the default always-on scheduler.

If you want Codex involved, keep the scheduler local and hand Codex the
non-silent incident log or repository state when analysis is needed. This keeps
the routine path lightweight and avoids turning every minute-level check into a
model task.

Codex automations can also run scheduled workspace jobs. Use them for lower
frequency review work, such as daily repository checks, weekly privacy scans, or
non-silent incident analysis. For installation steps, see
[Codex Edition](codex-edition.md).

## Rule Of Thumb

- Use Surge-only local mode for deterministic self-healing and manual review.
- Use Hermes when you want quiet scheduled automation plus notifications.
- Use Codex for interactive improvement, debugging, and project maintenance.
