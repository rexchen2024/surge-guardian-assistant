# Codex Edition

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-edition.zh-CN.md) | [繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-edition.zh-TW.md)

Codex Edition is for lower-frequency checks, incident review, and repository maintenance. Do not use it for minute-level monitoring.

## 1. Easiest: Paste This Into Codex

If you already use Codex, send it this prompt:

```text
Install https://github.com/rexchen2024/surge-guardian-assistant locally as my Surge Guardian Assistant project. Run doctor and scripts/check, then create or suggest a safe Codex automation using codex/automation-prompts/surge-guardian-review.md. Do not edit Surge profiles, certificates, DNS, servers, MITM, Rewrite, Scripting, or Replica, and do not run reload or restart without asking me first.
```

Codex should do three things:

1. Install the project locally.
2. Run the basic checks.
3. Suggest or create a low-frequency Codex automation.

## 2. Terminal One-Command Install

If you prefer doing it yourself in Terminal, run:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

The project installs to `~/.surge-guardian-assistant`.

## 3. Verify The Project

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant doctor
scripts/check
```

`doctor` checks the local Surge environment. `scripts/check` checks tests, baseline safety, and redaction rules.

## 4. Create A Codex Automation

Use this repository as the automation workspace:

```text
~/.surge-guardian-assistant
```

Prompt template:

```text
codex/automation-prompts/surge-guardian-review.md
```

Recommended cadence:

1. Daily for repository health and privacy risk.
2. Weekly for docs and tests.
3. Ad hoc when a non-silent incident package needs review.

## 5. Automatic Updates

A Codex automation can run this every day:

```bash
scripts/surge-guardian-assistant update --check
scripts/check
```

If you want it to upgrade directly, have the automation run:

```bash
scripts/surge-guardian-assistant update
```

If local tracked files were changed, the update skips instead of overwriting them.

## 6. Safety Boundary

Codex should not directly edit Surge profiles, certificates, DNS records, servers, MITM, Rewrite, Scripting, Replica, profile selection, policy group selection, reload, or restart.

If any of those actions looks necessary, ask the user first.
