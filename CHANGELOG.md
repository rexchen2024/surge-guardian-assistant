# Changelog

[简体中文](https://github.com/rexchen2024/surge-sentry/blob/main/CHANGELOG.zh-CN.md) | [繁體中文](https://github.com/rexchen2024/surge-sentry/blob/main/CHANGELOG.zh-TW.md)

## 0.2.0

- Add local-only configurable recurring maintenance windows for DNS, DIRECT-domain, and proxy transient noise; no personal window is enabled by default.
- Detect repeated same-weekday/time-bucket noise and report it as a candidate router, ISP, or upstream maintenance pattern before the user chooses to suppress it.
- Coalesce repeated suppressed sentry events by key so the local state keeps counts without growing noisy duplicate entries.
- Document the stricter Hermes delivery contract: only an exact `[SILENT]` response suppresses notification; explanatory text plus `[SILENT]` is delivered.
- Add 24-hour retention for high-frequency silent Surge Sentry cron outputs in the live Hermes job.
- Strengthen Codex path docs: Codex can be an independent client for open-source users, covering install checks, Surge config diagnostics, incident review, traffic-monitor interpretation, and safe change proposals.
- Add focused traffic monitor commands for F1, World Cup Fox, Apple TV, or similar start/status/end scenario reports.
- Validation: repo `scripts/check` passed, live script syntax check passed, temporary-HOME smoke test returned `{"wakeAgent": false}`, and Hermes cron scheduler tests passed.

## 0.1.1

- Treat CloudKit and Microsoft hosts as cautious DIRECT traffic so the sentry avoids temporary proxy rules for those system services.
- Record repeated background Surge noise for unknown VIF virtual IPs and DIRECT IP connection failures without waking Hermes.
- Tighten the Hermes prompt so handled minor incidents must return only `[SILENT]`.

## 0.1.0

First complete release.

- Quiet monitoring for Surge logs, events, policies, and external resources.
- Healthy runs emit only `{"wakeAgent": false}` to avoid unnecessary AI calls and notifications.
- Runtime checks and low-risk self-healing through Surge's official runtime capabilities and `surge-cli`.
- Automatic retry for failed external resources and Surge DNS cache flush after repeated DNS problems.
- Policy retests before notification to reduce noise from temporary failures.
- Narrow temporary runtime rules for repeated DIRECT failures, with periodic cleanup.
- Hermes Edition for always-on monitoring, incident notification, memory, and AI analysis when useful.
- Codex Edition for install checks, config diagnostics, incident review, and project maintenance.
- One-command install, first-run setup, automatic updates, and manual update commands.
- `version`, `update`, `doctor`, `feedback`, and `redact-check` commands.
- Private permissions for local `.env` and state files; no automatic log or usage upload.
- Sanitized feedback reports that users review before sharing.
- User confirmation required for permanent profile edits, certificates, DNS records, servers, MITM, Rewrite, Scripting, Replica, reload, restart, profile selection, and policy-group selection.
