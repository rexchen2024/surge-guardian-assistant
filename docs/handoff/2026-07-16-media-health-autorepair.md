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

- `scripts/check`: 54 tests passed; `redact-check: ok`.
- `scripts/surge-sentry doctor`: Surge environment, policy dump, and both configured profiles passed.
- `scripts/surge-sentry tick`: healthy result remained `{"wakeAgent": false}`.
- Forced Hermes cron job `3ff8679091b1`: succeeded with `wakeAgent=false`; repository and inline prompt hashes matched.
- Live daemon: running, controller response 18–34ms, zero event errors, about 18–22MB RSS, near-zero CPU, and no persistent child process.
- The ordinary Apple TV live replay reproduced Fastly at about 0.x Mbps, triggered exact-host repair, then verified Apple CDN at usable speed up to about 19.5 Mbps without requiring a manual restart.
- Active Surge profile identity matched `MAC_PROFILE`; only the triggering ordinary Apple TV Host override was added, while the F1 replay Host remained unchanged for its independent replay.
- Apple and Apple TV policy-group runtime selections remained DIRECT.
- `git diff --check` passed.

## Known Risks Or Gaps

- The F1 replay fault loop still needs its independent live replay; ordinary Apple TV has passed.
- Only Apple TV is enabled in the private local service config. The engine is generic, but every additional service needs real media domains and calibrated thresholds.
- Live F1 `linear-*` behavior is still unverified; F1 replay evidence does not prove the live path.
- Automatic RN takeover and all BWG switching remain intentionally disabled.

## Intentionally Not Changed

- Did not degrade or remove the currently working Apple TV DNS overrides.
- Did not change the Apple or Apple TV policy-group selection or candidate list.
- Did not add broad Apple-domain DNS overrides, fixed CDN IPs, global DNS changes, packet capture, MITM, Rewrite, or Scripting changes.
- Did not auto-enable other media services or expensive proxy takeovers.

## Recommended Next Action

Continue with the coordinated Apple TV fault replay while Rex is available. If the full notification, repair, reopen, and verification sequence passes, review and merge the PR; otherwise keep the branch open for the smallest correction.
