# Contributing

Thanks for improving Surge Sentry.

This project is small on purpose. Changes should keep the assistant quiet on healthy runs, safe around permanent Surge configuration, and careful with private network data.

## Before Opening A PR

Run:

```bash
scripts/check
```

Also check that your change does not include:

- `.env`
- Surge profiles
- subscription URLs
- proxy node credentials
- request logs
- raw DNS or event dumps
- real domains, IPs, paths, or notification targets

## Good Changes

- Fix a real issue with a focused patch.
- Improve install, update, feedback, or recovery paths.
- Add tests for behavior that can regress.
- Improve documentation without adding unnecessary complexity.

## Safety Rules

- Do not add automatic telemetry.
- Do not upload logs or device data.
- Do not make permanent Surge profile changes without user confirmation.
- Keep Hermes as the recommended always-on runtime.
- Keep Codex as the lower-frequency maintenance path.

## Pull Requests

Please include:

- what changed
- how you tested it
- whether the change touches Surge runtime behavior, privacy, or updates
