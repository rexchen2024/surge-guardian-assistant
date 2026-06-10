# Codex Edition

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-edition.zh-CN.md)

Codex Edition is optional. Use it for lower-frequency checks, incident review, and repository maintenance. Do not use it for minute-level monitoring.

## One-Command Install

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

If the repository is still private:

```bash
git clone https://github.com/rexchen2024/surge-guardian-assistant.git ~/.surge-guardian-assistant
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant setup
scripts/surge-guardian-assistant doctor
```

## Prompt For Codex

```text
Install https://github.com/rexchen2024/surge-guardian-assistant locally as my Surge Guardian Assistant project. Run doctor and scripts/check, then create or suggest a safe Codex automation using codex/automation-prompts/surge-guardian-review.md. Do not edit Surge profiles or make permanent network changes without asking me first.
```

## Create A Codex Automation

Use this repository as the automation workspace:

```text
~/.surge-guardian-assistant
```

Prompt template:

```text
codex/automation-prompts/surge-guardian-review.md
```

Recommended cadence:

- daily for repository health and privacy risk
- weekly for docs and tests
- ad hoc when a non-silent incident package needs review

## Automatic Updates

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

## Safety Boundary

Codex should not directly edit Surge profiles, certificates, DNS, MITM, Rewrite, Scripting, Replica, profile selection, policy group selection, reload, or restart.

If any of those actions looks necessary, ask the user first.
