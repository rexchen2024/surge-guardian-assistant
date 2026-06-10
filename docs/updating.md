# Updating

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/updating.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/updating.zh-CN.md)

Updates come from GitHub.

After setup, normal `tick` runs check for updates once a day. If new code is
available, the assistant pulls it and runs `scripts/check`. If local tracked
files were changed, it skips the update instead of overwriting anything.

## Automatic Updates

Automatic updates are on by default:

```bash
AUTO_UPDATE=1
AUTO_UPDATE_INTERVAL_SECONDS=86400
```

Turn them off in `.env`:

```bash
AUTO_UPDATE=0
```

## Manual Commands

Show the installed version:

```bash
scripts/surge-guardian-assistant version
```

Check for updates:

```bash
scripts/surge-guardian-assistant update --check
```

Update now:

```bash
scripts/surge-guardian-assistant update
```

## Notes

- `.env` stays local.
- State files stay local.
- Updates use `git pull --ff-only`.
- Local tracked edits stop the update.
- Release notes are in [Changelog](../CHANGELOG.md).
