# Codex Edition

[English](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/codex-edition.md) | [简体中文](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/codex-edition.zh-CN.md)

Codex Edition is an optional deployment style for users who want Codex to review
the project, inspect non-silent incidents, and suggest improvements.

It is not the default production runtime. Hermes Edition remains better for
minute-level quiet monitoring.

## What It Does

- Runs lower-frequency Codex workspace automations.
- Reviews repository health and privacy risk.
- Runs `scripts/check`.
- Analyzes non-silent incident packages when provided.
- Suggests code or documentation improvements after repeated patterns.

## Requirements

- Surge for macOS is installed and running.
- Codex can access the local repository workspace.
- The user has Codex automations available.
- Model-backed scheduled analysis is acceptable for the chosen cadence.

## Install

```bash
git clone https://github.com/rexchen2024/surge-hermes-guardian.git
cd surge-hermes-guardian
scripts/surge-hermes-guardian setup --print-hermes-command
scripts/surge-hermes-guardian doctor
```

The setup command still writes the same local `.env`, because the deterministic
guardian logic is shared by both editions.

## Create A Codex Automation

Create a Codex workspace automation pointed at this repository root. Use the
prompt template:

```text
codex/automation-prompts/surge-guardian-review.md
```

Recommended cadence:

- daily for repository health review
- weekly for privacy and documentation review
- ad hoc when a non-silent incident package needs analysis

Avoid minute-level Codex automations for healthy checks. A Codex automation
starts a Codex task, while Hermes can skip model work entirely on healthy runs.

## Safety Boundary

Codex automations should not directly edit Surge profiles, `.conf`, `.sgmodule`,
certificates, DNS records, server settings, MITM, Rewrite, Scripting, Replica,
profile selection, policy group selections, reload, or restart behavior.

If any of those actions looks necessary, Codex should ask the user for
confirmation instead of performing it.
