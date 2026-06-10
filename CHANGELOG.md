# Changelog

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.zh-CN.md)

## 0.3.0

- Automatic updates are on by default during normal `tick` runs.
- Added `AUTO_UPDATE` and `AUTO_UPDATE_INTERVAL_SECONDS`.
- Kept updates safe: local tracked edits stop the update.
- Simplified README and update docs.

## 0.2.0

- Renamed the public project to Surge Guardian Assistant.
- Added Hermes Edition and Codex Edition documentation.
- Added `scripts/surge-guardian-assistant` as the only public CLI entrypoint.
- Added `version` and `update` commands.
- Added `install.sh` for one-command Git-based installation.
- Kept local `.env` and state files private with `0600` permissions.

## 0.1.0

- Initial guardian loop for Surge logs and events.
- Hermes cron-friendly `{"wakeAgent": false}` healthy output.
- External resource retry, DNS flush, policy retest, temporary rule handling,
  privacy scan, and bilingual documentation.
