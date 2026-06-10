# Privacy Notes

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/privacy.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/privacy.zh-CN.md)

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
- Run `scripts/surge-guardian-assistant redact-check` before every commit.
