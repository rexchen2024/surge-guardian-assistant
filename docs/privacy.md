# Privacy Notes

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
- Run `scripts/surge-hermes-guardian redact-check` before every commit.
