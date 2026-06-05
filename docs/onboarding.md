# Onboarding

[English](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/onboarding.md) | [简体中文](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/onboarding.zh-CN.md)

This guide assumes Surge for macOS and Hermes are already installed.

## 1. Clone

```bash
git clone <repo-url>
cd surge-hermes-guardian
```

## 2. Run Setup

```bash
scripts/surge-hermes-guardian setup --print-hermes-command
```

Setup discovers:

- `surge-cli`
- Surge log directory
- profile candidates
- runtime policy candidates

It writes `.env` in the repository root. It does not edit Surge profiles.

## 3. Verify Locally

```bash
scripts/surge-hermes-guardian doctor
scripts/surge-hermes-guardian tick
```

Healthy `tick` output is:

```json
{"wakeAgent": false}
```

## 4. Install Hermes Cron

Review the command printed by setup, then run it. The recommended schedule is
once per minute.

Hermes handles delivery according to the user's existing Hermes configuration.
If no delivery target is configured, set up a Hermes-supported platform first.
The guardian does not require Telegram specifically.

## 5. Operate

- Use `doctor` for a manual sanitized status check.
- Use `redact-check` or `scripts/check` before committing changes.
- Keep `.env`, logs, state, profiles, and real infrastructure identifiers out of Git.
