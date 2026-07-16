# Routing contracts and low-noise policy probes

## What changed

- Added a local routing-contract audit for profile rule ownership.
- Added a rotating, low-frequency `test-policy` probe with repeated-failure gating.
- Added example configuration for both mechanisms.

## Files changed

- `surge_sentry/contracts.py`
- `surge_sentry/config.py`
- `surge_sentry/sentry.py`
- `tests/test_sentry.py`
- `config/example.env`
- `config/routing-contracts.example.json`

## Verified

- Unit tests pass.
- `scripts/check` and redact check pass.
- The local 游戏平台 contract passes against the active `Rex-Mac mini.conf`.

## Known gaps

- Contracts verify configured rule ownership, not arbitrary future shared-CDN domains.
- Policy probes prove transport availability only; service-specific playback and storefront behavior still require real requests.

## Intentionally not changed

- No Surge policy selection, DNS, profile reload behavior, or mobile profile behavior was changed.
- The minute Sentry job remains event-gated through `wakeAgent: false`; it was not converted to a blind no-agent job.

## Recommended next action

Merge after reviewing the local contract list, then add contracts only for services with verified ownership expectations.
