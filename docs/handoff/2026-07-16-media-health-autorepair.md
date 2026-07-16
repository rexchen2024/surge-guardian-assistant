# Media health detection and allowlisted auto-repair

Task ID: `media-health-autorepair`
Branch: `codex/media-health-autorepair`
Base: `main`
Generated: 2026-07-16

## What Changed

- Added a generic `cdn-watch` service model for real media throughput, CDN classification, policy-group filtering, and per-service thresholds.
- Replaced the high-memory persistent Surge CLI stream with adaptive `dump active` sampling: 10 seconds while idle and 2 seconds during matching playback.
- Added the Apple TV local template and exact-host Fastly-to-Apple DNS repair loop with backup, profile validation, runtime verification retries, DNS flush, silent background connection verification, grace-window rollback, and optional restart advice only when playback still has trouble.
- Each incident repairs only the exact host that triggered it, allowing VOD and F1 replay to be exercised and verified independently.
- Cooldowns are scoped to the exact failing host, so a recent ordinary Apple TV repair cannot suppress an independent F1 replay incident in the same service group.
- Added direct Hermes lifecycle notifications without model usage; unresolved events now use event IDs, inflight retry, explicit ack, delivery-confirmed `resolve`, processed archive, and quarantine.
- Added watcher heartbeat/controller health, code/config signatures, safe restart, private file permissions, bounded logs/history/backups, sanitized status, and per-event exception isolation.
- Synced English, Simplified Chinese, and Traditional Chinese documentation and the Hermes job prompt.

## Files Changed

```text
.gitignore
README.en.md
README.md
README.zh-CN.md
README.zh-TW.md
config/cdn-watch.example.json
config/example.env
docs/autonomy.md
docs/autonomy.zh-CN.md
docs/autonomy.zh-TW.md
docs/runtime-options.md
docs/runtime-options.zh-CN.md
docs/runtime-options.zh-TW.md
hermes/job-prompts/sentry.md
surge_sentry/cdn_watch.py
surge_sentry/cli.py
surge_sentry/config.py
surge_sentry/redact.py
surge_sentry/sentry.py
surge_sentry/surge.py
tests/test_sentry.py
```

## Verification

- `scripts/check`: 55 tests passed; `redact-check: ok`.
- `scripts/surge-sentry doctor`: Surge environment, policy dump, and both configured profiles passed.
- `scripts/surge-sentry tick`: healthy result remained `{"wakeAgent": false}`.
- Forced Hermes cron job `3ff8679091b1`: succeeded with `wakeAgent=false`; repository and inline prompt hashes matched.
- Live daemon: running, controller response 18–34ms, zero event errors, about 18–22MB RSS, near-zero CPU, and no persistent child process.
- The ordinary Apple TV live replay reproduced Fastly at about 0.x Mbps, triggered exact-host repair, then verified Apple CDN at usable speed up to about 19.5 Mbps without requiring a manual restart.
- The independent F1 replay reproduced Fastly at about 0.55 Mbps, exposed and fixed a service-wide cooldown bug, triggered only the F1 exact-host repair, then verified Apple CDN at healthy speed above 30 Mbps without requiring a manual restart.
- Active Surge profile identity matched `MAC_PROFILE`; both exact Host overrides are now present because each one independently triggered and passed its own live replay.
- Apple and Apple TV policy-group runtime selections remained DIRECT.
- `git diff --check` passed.

## Known Risks Or Gaps

- Live F1 `linear-*` behavior is still unverified; the completed F1 replay test covers `hls-amt.itunes.apple.com`, not the live-event path.
- Only Apple TV is enabled in the private local service config. The engine is generic, but every additional service needs real media domains and calibrated thresholds.
- Automatic RN takeover and all BWG switching remain intentionally disabled.

## Intentionally Not Changed

- Did not degrade or remove the currently working Apple TV DNS overrides.
- Did not change the Apple or Apple TV policy-group selection or candidate list.
- Did not add broad Apple-domain DNS overrides, fixed CDN IPs, global DNS changes, packet capture, MITM, Rewrite, or Scripting changes.
- Did not auto-enable other media services or expensive proxy takeovers.

## Recommended Next Action

Let the normal Mac-to-mobile profile sync propagate the final F1 Host override, then review the Draft PR. Test `linear-*` independently during a future live F1 event before enabling any live-path repair.
