# Privacy Notes

[简体中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/privacy.zh-CN.md) | [繁體中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/privacy.zh-TW.md)

Treat these as sensitive:

- Surge profile files
- Subscription URLs
- Proxy node server names, ports, passwords, and tokens
- Controller credentials
- Request logs, DNS dumps, and raw event dumps
- Real domains and IPs that identify private infrastructure

Before publishing:

- Keep `.env` out of Git.
- Replace real domains and IPs with examples.
- Review screenshots and terminal logs before sharing.
- Prefer summarized results over raw dumps.
- Run `scripts/surge-sentry redact-check` before every commit.

## Feedback Reports

The project does not upload logs, usage data, or device data by itself.

Users can create a sanitized report:

```bash
scripts/surge-sentry feedback
```

The report is written to the local state directory with `0600` permissions. Review it before sharing.

To copy it into a GitHub issue:

```bash
scripts/surge-sentry feedback --github-url
```

This only creates a link. It does not submit anything.

The report itself does not require a real identity. If submitted through GitHub, GitHub account visibility is controlled by GitHub.
