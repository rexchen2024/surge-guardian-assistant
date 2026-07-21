# Onboarding

[简体中文](https://github.com/rexchen2024/surge-sentry/blob/main/docs/onboarding.zh-CN.md) | [繁體中文](https://github.com/rexchen2024/surge-sentry/blob/main/docs/onboarding.zh-TW.md)

This guide assumes Surge for macOS is already installed. Hermes is recommended
for scheduled model-assisted operation, but the local `doctor` and `tick`
commands can run without Hermes.

## 1. Get The Project

```bash
git clone https://github.com/rexchen2024/surge-sentry.git ~/.surge-sentry
cd ~/.surge-sentry
```

## 2. Run Setup

```bash
scripts/surge-sentry setup --print-hermes-command
```

Setup discovers:

- `surge-cli`
- Surge log directory
- profile candidates
- runtime policy candidates

It writes `.env` in the repository root. It does not edit Surge profiles.

## 3. Verify Locally

```bash
scripts/surge-sentry doctor
scripts/surge-sentry tick
```

Healthy `tick` output is:

```json
{"wakeAgent": false}
```

## 4. Choose A Runtime

For the recommended Hermes workflow, review the command printed by setup, then
run it. The recommended schedule is once per minute.

Hermes handles delivery according to the user's existing Hermes configuration.
If no delivery target is configured, set up a Hermes-supported platform first.
The sentry does not require Telegram specifically.

For a Surge-only machine without Hermes, run `tick` from launchd or another
local scheduler and review any output that is not `{"wakeAgent": false}`. See
[Runtime options](runtime-options.md).

## 5. Operate

- Use `doctor` for a manual sanitized status check.
- Use `update --check` to check GitHub for newer code.
- Use `feedback` to create a sanitized feedback report.
- Use `redact-check` or `scripts/check` before committing changes.
- Keep `.env`, logs, state, profiles, and real infrastructure identifiers out of Git.
