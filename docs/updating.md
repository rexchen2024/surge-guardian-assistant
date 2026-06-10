# Updating

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/updating.zh-CN.md)

Updates come from GitHub.

Automatic updates do not run in the background by themselves. Hermes, Codex, or another scheduler must keep running `tick`.

## Default Behavior

```bash
AUTO_UPDATE=1
AUTO_UPDATE_INTERVAL_SECONDS=86400
```

That means: check at most once a day.

If new code is available, the assistant pulls it and runs `scripts/check`.

If local tracked files were changed, the update skips instead of overwriting anything.

## Manual Commands

Show the version:

```bash
scripts/surge-guardian-assistant version
```

Check only:

```bash
scripts/surge-guardian-assistant update --check
```

Update now:

```bash
scripts/surge-guardian-assistant update
```

Turn automatic updates off:

```bash
AUTO_UPDATE=0
```

## Notes

- `.env` stays local.
- State files stay local.
- Updates use `git pull --ff-only`.
- Non-Git installs cannot auto-update.
- Release notes are in [Changelog](../CHANGELOG.md).
