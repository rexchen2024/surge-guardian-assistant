# Hermes Edition

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/hermes-edition.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/hermes-edition.zh-CN.md)

Hermes Edition is the recommended production deployment for Surge Guardian
Assistant.

## What It Does

- Runs `tick` from Hermes cron, usually once per minute.
- Keeps healthy runs silent with `{"wakeAgent": false}`.
- Wakes the configured Hermes model only for non-silent incident packages.
- Uses Hermes delivery channels for handled summaries or confirmation requests.
- Keeps permanent Surge changes behind user confirmation.

## Requirements

- Surge for macOS is installed and running.
- Hermes is installed.
- Hermes cron works.
- Hermes has a delivery target if notifications are desired.

The delivery target can be Telegram, Discord, Matrix, Weixin, Feishu, Signal, or
another platform supported by the user's Hermes setup.

## Install

```bash
git clone https://github.com/rexchen2024/surge-guardian-assistant.git
cd surge-guardian-assistant
scripts/surge-guardian-assistant setup --print-hermes-command
```

Setup discovers:

- `surge-cli`
- Surge log directory
- profile candidates
- runtime policy candidates

It writes local `.env` only. It does not edit Surge profiles.

## Verify

```bash
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
```

Healthy output:

```json
{"wakeAgent": false}
```

## Create The Hermes Job

Review the Hermes cron command printed by setup, then run it. The recommended
schedule is once per minute.

Use `hermes/job-prompts/guardian.md` as the model-analysis prompt. It tells
Hermes to stay silent for minor already-handled issues and to request
confirmation before risky Surge changes.

## Operate

- Run `doctor` for a sanitized status check.
- Run `scripts/check` before publishing changes.
- Keep `.env`, logs, state, profiles, and real infrastructure identifiers out of
  Git.
- Treat Hermes Edition as the default path for always-on monitoring.
