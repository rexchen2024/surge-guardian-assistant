# Security Policy

## Supported Versions

The latest release is supported.

## Reporting A Security Issue

Please do not open a public issue with secrets, Surge profiles, subscription URLs, node credentials, raw request logs, DNS dumps, or event dumps.

Use GitHub's private vulnerability reporting if it is enabled for this repository. If it is not enabled, open a public issue with only a short summary and no sensitive data.

Useful safe details:

- installed version
- operating system
- whether Hermes Edition or Codex Edition is used
- sanitized output from `scripts/surge-sentry feedback --print`
- what action you expected
- what action actually happened

## Project Security Boundaries

Surge Sentry should:

- keep healthy checks silent
- avoid automatic telemetry
- avoid uploading logs or device data
- keep `.env` and state files private
- avoid permanent Surge profile changes without user confirmation
- skip automatic updates when local tracked files have changed
