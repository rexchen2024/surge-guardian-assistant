# Codex Edition

[简体中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/codex-edition.zh-CN.md) | [繁體中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/codex-edition.zh-TW.md)

Codex is an important Surge Sentry client for open-source users and local workspaces. It is useful for install checks, Surge config diagnostics, incident review, traffic-monitor interpretation, privacy checks, docs maintenance, and safe change proposals.

It does not need to replace the minute-level health gate. Keep the healthy path lightweight on local scripts or Hermes; bring Codex in when the task needs judgment, explanation, cleanup, or improvement.

## 1. Easiest: Paste This Into Codex

If you already use Codex, send it this prompt:

```text
Install https://github.com/rexchen1803/surge-sentry locally as my Surge Sentry project. Run doctor and scripts/check, then create or suggest a safe Codex automation using codex/automation-prompts/surge-sentry-review.md. Do not edit Surge profiles, certificates, DNS, servers, MITM, Rewrite, Scripting, or Replica, and do not run reload or restart without asking me first.
```

Codex should do four things:

1. Install the project locally.
2. Run the basic checks.
3. Check local Surge Sentry config, privacy boundaries, and runtime docs.
4. Suggest or create a safe Codex automation.

## 2. Terminal One-Command Install

If you prefer doing it yourself in Terminal, run:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen1803/surge-sentry/main/install.sh)" -- --setup
```

The project installs to `~/.surge-sentry`.

## 3. Verify The Project

```bash
cd ~/.surge-sentry
scripts/surge-sentry doctor
scripts/check
```

`doctor` checks the local Surge environment. `scripts/check` checks tests, baseline safety, and redaction rules.

## 4. Create A Codex Automation

Use this repository as the automation workspace:

```text
~/.surge-sentry
```

Prompt template:

```text
codex/automation-prompts/surge-sentry-review.md
```

Recommended uses:

1. Daily for repository health and privacy risk.
2. Weekly for docs, tests, and example-config review.
3. Ad hoc when a non-silent incident package needs review.
4. Interpret F1, World Cup Fox, Apple TV, or similar traffic-monitor results.
5. When Surge config changes look useful, propose the change and risks without directly editing permanent profiles.

## 5. Automatic Updates

A Codex automation can run this every day:

```bash
scripts/surge-sentry update --check
scripts/check
```

If you want it to upgrade directly, have the automation run:

```bash
scripts/surge-sentry update
```

If local tracked files were changed, the update skips instead of overwriting them.

## 6. Safety Boundary

Codex should not directly edit Surge profiles, certificates, DNS records, servers, MITM, Rewrite, Scripting, Replica, profile selection, policy group selection, reload, or restart.

If any of those actions looks necessary, ask the user first.
