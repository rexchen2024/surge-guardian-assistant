# Surge Guardian Assistant

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.zh-CN.md)

Current version: **0.1.0**

Surge Guardian Assistant watches Surge for you. It stays quiet when things are fine, tries safe fixes first, and asks before risky changes.

Project:

```text
https://github.com/rexchen2024/surge-guardian-assistant
```

## What These Tools Are

- [Surge](https://nssurge.com/) is a network and proxy tool for macOS and iOS. This project watches Surge.
- [Hermes](https://github.com/NousResearch/hermes-agent) runs scheduled jobs, analyzes incidents, and sends messages. It is the recommended always-on runtime.
- [Codex](https://openai.com/codex/) is OpenAI's coding assistant. It is useful for lower-frequency project checks, incident review, and maintenance.

## One-Command Install

Default install path: `~/.surge-guardian-assistant`

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

If the repository is still private, use Git:

```bash
git clone https://github.com/rexchen2024/surge-guardian-assistant.git ~/.surge-guardian-assistant
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant setup --print-hermes-command
```

Prompt for Hermes:

```text
Install Surge Guardian Assistant from https://github.com/rexchen2024/surge-guardian-assistant, run setup, and show me the generated Hermes cron command. Do not edit Surge profiles or make permanent network changes without asking me first.
```

Prompt for Codex:

```text
Install https://github.com/rexchen2024/surge-guardian-assistant locally as my Surge Guardian Assistant project, run doctor and scripts/check, then create or suggest a safe Codex automation. Do not edit Surge profiles without asking me first.
```

## Pick An Edition

**Hermes Edition** is recommended. It is good for minute-level monitoring, stays silent on healthy runs, and notifies you only when needed.

[Install Hermes Edition](docs/hermes-edition.md)

**Codex Edition** is optional. It is good for daily or weekly repository checks, incident review, and ongoing project maintenance.

[Install Codex Edition](docs/codex-edition.md)

## Core Features

- Reads Surge logs and events.
- Retries external resources when they fail.
- Flushes DNS after repeated DNS problems.
- Retests policies before bothering you.
- Adds small temporary runtime rules for repeated DIRECT failures.
- Emits `{"wakeAgent": false}` on healthy runs to avoid noise.
- Pulls updates from GitHub automatically.
- Keeps local `.env` and state files private.
- Provides privacy scanning and sanitized feedback reports.
- Never edits permanent Surge configuration without asking.

## Automatic Updates

Automatic updates work when the install path is a Git checkout and Hermes, Codex, or another scheduler keeps running `tick`.

The assistant checks GitHub once a day by default. If new code is available, it pulls the update and runs `scripts/check`. If local tracked files were changed, it skips the update instead of overwriting anything.

Check manually:

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant update --check
```

Update manually:

```bash
scripts/surge-guardian-assistant update
```

Turn off automatic updates in `.env`:

```bash
AUTO_UPDATE=0
```

## Send Feedback

The project does not upload logs or usage data by itself. A user can create a sanitized report, review it, and decide whether to send it:

```bash
scripts/surge-guardian-assistant feedback --github-url
```

Preview it in the terminal:

```bash
scripts/surge-guardian-assistant feedback --print
```

## Useful Commands

```bash
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
scripts/surge-guardian-assistant version
scripts/surge-guardian-assistant update
scripts/surge-guardian-assistant feedback
scripts/surge-guardian-assistant redact-check
```

## Docs

- [Hermes Edition](docs/hermes-edition.md)
- [Codex Edition](docs/codex-edition.md)
- [Updating](docs/updating.md)
- [Autonomy model](docs/autonomy.md)
- [Privacy notes](docs/privacy.md)
- [Changelog](CHANGELOG.md)

## Project Rules

- License: [MIT](LICENSE)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)
