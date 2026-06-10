# Changelog

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.zh-CN.md)

## 0.1.0

First complete release.

- Quiet monitoring for Surge logs, events, policies, and external resources.
- Healthy runs emit only `{"wakeAgent": false}` to avoid unnecessary AI calls and notifications.
- Runtime checks and low-risk self-healing through Surge's official Agent Skill / `surge-cli`.
- Automatic retry for failed external resources and Surge DNS cache flush after repeated DNS problems.
- Policy retests before notification to reduce noise from temporary failures.
- Narrow temporary runtime rules for repeated DIRECT failures, with periodic cleanup.
- Hermes Edition for always-on monitoring, incident notification, memory, and AI analysis when useful.
- Codex Edition for lower-frequency repository checks, incident review, and project maintenance.
- One-command install, first-run setup, automatic updates, and manual update commands.
- `version`, `update`, `doctor`, `feedback`, and `redact-check` commands.
- Private permissions for local `.env` and state files; no automatic log or usage upload.
- Sanitized feedback reports that users review before sharing.
- User confirmation required for permanent profile edits, certificates, DNS records, servers, MITM, Rewrite, Scripting, Replica, reload, restart, profile selection, and policy-group selection.
- Simplified Chinese homepage by default, with Traditional Chinese and English entry points.
- Install docs are available in Simplified Chinese, Traditional Chinese, and English, with language-switch links.
