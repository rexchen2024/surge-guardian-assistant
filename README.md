# Surge Guardian Assistant

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.zh-CN.md)

Current version: **0.2.0**

Surge Guardian Assistant is a lightweight autonomous operations assistant for
people who run [Surge](https://nssurge.com/) on macOS. It watches Surge signals,
handles safe recovery steps, keeps healthy checks quiet, and asks for user
confirmation before risky changes.

Project URL:

```text
https://github.com/rexchen2024/surge-guardian-assistant
```

Repository slug and public product name are aligned as
`surge-guardian-assistant`.

## Quick Start

One-command install:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)"
```

Private repository users can use Git directly:

```bash
git clone https://github.com/rexchen2024/surge-guardian-assistant.git
cd surge-guardian-assistant
scripts/surge-guardian-assistant setup --print-hermes-command
```

Update later:

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant update
```

## Choose A Version

### Hermes Edition

Best for production use. Hermes runs the minute-level guardian loop, skips model
work on healthy checks with `{"wakeAgent": false}`, and wakes the configured
model only when the script emits an incident package.

- Recommended for always-on monitoring.
- Lowest noise and lowest routine model usage.
- Uses Hermes cron, memory, model reasoning, and delivery channels.
- Best fit when the user already has Hermes and Surge.

[Install Hermes Edition](docs/hermes-edition.md)

### Codex Edition

Best for scheduled review, project maintenance, and incident analysis. Codex can
run lower-frequency workspace automations against this repository and use the
provided prompt to review non-silent incidents or propose improvements.

- Optional, not the default production runtime.
- Good for daily/weekly review, privacy scans, and code/documentation upkeep.
- Useful for users who already rely on Codex automations.
- Not recommended as a replacement for Hermes minute-level quiet checks.

[Install Codex Edition](docs/codex-edition.md)

## Shared Capabilities

- Reads Surge event and log signals locally.
- Retries external resources when safe.
- Flushes DNS after repeated DNS failures.
- Retests policies before escalating.
- Adds narrow temporary runtime rules for repeated DIRECT failures.
- Reviews and removes temporary runtime rules later.
- Keeps local `.env` and state files private with `0600` permissions.
- Refuses permanent Surge profile, DNS, certificate, server, MITM, Rewrite,
  Scripting, Replica, reload, or restart changes without user confirmation.

## Commands

- `setup`: interactive first-run setup; writes local `.env` only.
- `tick`: one lightweight guardian run.
- `doctor`: sanitized manual diagnostic summary.
- `version`: print installed version.
- `update`: pull the latest GitHub version and run checks.
- `redact-check`: repository scan before commit or GitHub push.

```bash
scripts/surge-guardian-assistant setup --print-hermes-command
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
scripts/surge-guardian-assistant update --check
```

Healthy `tick` output is:

```json
{"wakeAgent": false}
```

## Privacy

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

## More Docs

- [Hermes Edition](docs/hermes-edition.md)
- [Codex Edition](docs/codex-edition.md)
- [Runtime options](docs/runtime-options.md)
- [Updating](docs/updating.md)
- [Autonomy model](docs/autonomy.md)
- [Privacy notes](docs/privacy.md)
- [Sync workflow](docs/sync-workflow.md)
- [Changelog](CHANGELOG.md)
