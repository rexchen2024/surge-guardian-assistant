# Updating

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/updating.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/updating.zh-CN.md)

Surge Guardian Assistant is installed as a Git checkout. GitHub is the update
source.

This keeps updates simple:

- users keep the same local `.env`
- code updates come from `main`
- local private state stays outside Git
- the update command validates the new code before reporting success

## Check The Installed Version

```bash
scripts/surge-guardian-assistant version
```

## Check For Updates

```bash
scripts/surge-guardian-assistant update --check
```

## Apply Updates

```bash
scripts/surge-guardian-assistant update
```

The update command runs:

1. `git fetch --prune origin`
2. a local-change safety check
3. `git pull --ff-only`
4. `scripts/check`

If tracked files were edited locally, the command stops instead of overwriting
them. Commit, stash, or reset those local edits before updating.

## Release Notes

See [Changelog](../CHANGELOG.md).
