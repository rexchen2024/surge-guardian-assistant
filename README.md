# Surge Hermes Guardian

[English](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/README.md) | [简体中文](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/README.zh-CN.md)

Surge Hermes Guardian is a lightweight autonomous operations agent for people
who already run [Surge](https://nssurge.com/) on macOS and use Hermes for
scheduled agent work. It watches Surge continuously through Hermes cron, handles
safe fixes by itself, and wakes a model only when the evidence deserves
analysis.

The goal is not to produce more alerts. The goal is to keep Surge healthy,
reduce repeated network errors, learn from recurring patterns, and notify the
user only when something was meaningfully handled or when a risky decision needs
confirmation.

## Why Use It

- **Fast to start**: run one setup command, review the generated Hermes command,
  and schedule the guardian.
- **Quiet by default**: healthy runs return `{"wakeAgent": false}`, so Hermes
  skips the model and sends nothing.
- **Autonomous where safe**: the guardian can update external resources, flush
  DNS, retest policies, and add narrow temporary runtime rules.
- **Model-assisted when needed**: non-silent incidents wake Hermes, which uses
  the user's configured model and delivery channel.
- **Privacy-first**: real domains, IPs, profile paths, policy names, logs, and
  state stay in local `.env` and local state files.

## Recommended Setup

Prerequisites:

- Surge for macOS is installed and running.
- Hermes is installed and its gateway/cron system works.
- Hermes already has a delivery target if you want notifications. This can be
  Telegram, Discord, Matrix, Weixin, Feishu, Signal, or another platform your
  Hermes installation supports. The guardian does not require a specific social
  channel.

Install:

```bash
git clone <repo-url>
cd surge-hermes-guardian
scripts/surge-hermes-guardian setup --print-hermes-command
```

The setup wizard discovers `surge-cli`, Surge logs, profile candidates, and
runtime policy candidates, then writes a local `.env`. It does not edit Surge
profiles.

Next, run a local check:

```bash
scripts/surge-hermes-guardian doctor
scripts/surge-hermes-guardian tick
```

Healthy `tick` output is:

```json
{"wakeAgent": false}
```

Finally, review and run the Hermes cron command printed by setup. The
recommended schedule is once per minute.

## Commands

- `setup`: interactive first-run setup; writes local `.env` only.
- `tick`: one lightweight guardian run for Hermes cron.
- `doctor`: sanitized manual diagnostic summary.
- `redact-check`: repository scan before commit or GitHub push.

## How Hermes Is Used

The guardian script handles deterministic work locally. When there is nothing
important, it returns `{"wakeAgent": false}` and Hermes does not call a model.

When the script emits an incident package, Hermes wakes the configured model and
uses `hermes/job-prompts/guardian.md` to decide whether to stay silent, report
that an issue was handled, or ask the user to confirm a risky action. Delivery is
handled by Hermes according to the user's current Hermes configuration.

## Autonomy Boundary

Automatically allowed:

- external resource updates
- DNS flush
- policy and group retests
- narrow temporary runtime rules
- repeated-error counters and suppression
- later review/removal of temporary rules

Requires user confirmation:

- writing permanent profiles
- editing `.conf` or `.sgmodule`
- restarting, stopping, reloading, or switching Surge profiles
- long-term policy-group changes
- MITM, Rewrite, Scripting, Replica, or capture changes
- certificate, DNS record, server, or account changes
- broad temp-rule deletion

## Privacy And Publishing

Never commit:

- `.env`
- state or log files
- Surge profiles
- subscription URLs
- node credentials
- real domains or IPs
- notification targets

Run this before every commit:

```bash
scripts/check
```

More docs:

- [Onboarding](docs/onboarding.md)
- [Autonomy model](docs/autonomy.md)
- [Privacy notes](docs/privacy.md)
- [Sync workflow](docs/sync-workflow.md)
