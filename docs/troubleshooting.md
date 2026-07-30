# Troubleshooting

[简体中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/troubleshooting.zh-CN.md) | [繁體中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/troubleshooting.zh-TW.md)

Start with:

```bash
cd ~/.surge-sentry
scripts/surge-sentry doctor
```

## `missing .env`

Setup has not been completed.

```bash
scripts/surge-sentry setup --print-hermes-command
```

## `surge-cli: not found`

Confirm that Surge for macOS is installed and that the `surge-cli` path is correct.

Default path:

```text
/Applications/Surge.app/Contents/Applications/surge-cli
```

If your path is different, run setup again.

## `expected policies: missing`

The assistant needs the policy groups it should retest.

Run setup again, or set this in `.env`:

```bash
EXPECTED_POLICIES=Proxy,ProxyMedia
```

Use the real policy group names from Surge.

## It Keeps Printing `{"wakeAgent": false}`

That is normal. It means there is no incident that needs Hermes or Codex attention.

## Automatic Updates Do Not Happen

Check three things:

- the install path must be a Git checkout
- Hermes, Codex, or another scheduler must keep running `tick`
- `.env` must not set `AUTO_UPDATE=0`

Check manually:

```bash
scripts/surge-sentry update --check
```

## Update Was Skipped

If local tracked files were changed, automatic updates skip instead of overwriting them.

Check status:

```bash
git status --short
```

## Report A Problem

Create a sanitized report:

```bash
scripts/surge-sentry feedback --github-url
```

Review the report before sending it. Do not paste raw Surge profiles, subscription URLs, node credentials, request logs, real domains, or real IPs.
