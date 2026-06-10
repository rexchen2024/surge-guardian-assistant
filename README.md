# Surge Guardian Assistant

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.zh-CN.md)

Current version: **0.3.0**

Surge Guardian Assistant keeps an eye on Surge for you. When everything is fine,
it stays quiet. When something looks wrong, it tries the safe fixes first and
only asks you before risky changes.

Project:

```text
https://github.com/rexchen2024/surge-guardian-assistant
```

## Install

One command:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)"
```

If the repo is private, use Git:

```bash
git clone https://github.com/rexchen2024/surge-guardian-assistant.git
cd surge-guardian-assistant
scripts/surge-guardian-assistant setup --print-hermes-command
```

## What It Does

- Watches Surge logs and events.
- Retries external resources when they fail.
- Flushes DNS after repeated DNS problems.
- Retests policies before bothering you.
- Adds small temporary runtime rules for repeated DIRECT failures.
- Keeps `.env` and state files private.
- Never edits permanent Surge profiles without asking.

Healthy output is:

```json
{"wakeAgent": false}
```

## Pick A Version

**Hermes Edition** is the normal choice. It runs often, stays quiet when healthy,
and uses Hermes for messages.

[Install Hermes Edition](docs/hermes-edition.md)

**Codex Edition** is for lower-frequency review and maintenance. It is useful if
you already use Codex automations.

[Install Codex Edition](docs/codex-edition.md)

## Updates

Installed copies check GitHub automatically once a day during normal runs.
Nothing is overwritten if the user changed tracked files locally.

Manual update:

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant update
```

Check only:

```bash
scripts/surge-guardian-assistant update --check
```

Turn off automatic updates by setting this in `.env`:

```bash
AUTO_UPDATE=0
```

## Useful Commands

```bash
scripts/surge-guardian-assistant setup --print-hermes-command
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
scripts/surge-guardian-assistant version
scripts/surge-guardian-assistant update
```

## Privacy

Do not commit `.env`, logs, state files, Surge profiles, subscription URLs, node
credentials, real domains, real IPs, or notification targets.

Before publishing changes:

```bash
scripts/check
```

## Docs

- [Hermes Edition](docs/hermes-edition.md)
- [Codex Edition](docs/codex-edition.md)
- [Updating](docs/updating.md)
- [Autonomy model](docs/autonomy.md)
- [Privacy notes](docs/privacy.md)
- [Changelog](CHANGELOG.md)
