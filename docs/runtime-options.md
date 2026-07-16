# Runtime Options

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/runtime-options.zh-CN.md) | [繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/runtime-options.zh-TW.md)

Surge Sentry has one core loop and three practical ways to run it.

## 1. Choose A Runtime

**1. Terminal**

Best when you only want to check Surge from the local terminal. This is the lightest path: local scripts plus `surge-cli`.

**2. Hermes Agent**

Best for always-on monitoring, incident notifications, and learning from repeated patterns. Healthy checks stay silent; important issues can wake AI.

[Read Hermes setup](hermes-edition.md)

**3. Codex**

Best for open-source project-style use: install checks, Surge config diagnostics, incident review, traffic-monitor interpretation, and project maintenance. Healthy checks still run through local scripts so every check does not start a model task.

[Read Codex setup](codex-edition.md)

## 2. Common One-Command Install

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

The installer puts the project in `~/.surge-sentry`, checks the Surge environment, and starts first-run setup.

## 3. Verify It Works

```bash
cd ~/.surge-sentry
scripts/surge-sentry doctor
scripts/surge-sentry tick
```

`doctor` checks the Surge command, logs, and local config. `tick` performs one real check. Healthy output is:

```json
{"wakeAgent": false}
```

## 4. Run Local-only Mode

Local-only mode can be scheduled with launchd, cron, or another local scheduler:

```bash
/path/to/surge-sentry/scripts/surge-sentry tick >> "$HOME/Library/Logs/surge-sentry.log" 2>&1
```

It still supports:

1. Log and event checks.
2. External resource retry.
3. DNS flush.
4. Policy retest.
5. Narrow temporary runtime rules.
6. Temporary rule cleanup and state reconciliation.

It does not automatically provide:

1. Model analysis.
2. Chat-style explanation.
3. Cross-session learning through Hermes memory.
4. Telegram, Discord, Matrix, Weixin, Feishu, Signal, or other Hermes delivery channels.

## 5. Automatic Updates

As long as the install path remains a Git checkout, it can keep receiving updates from GitHub. See [Updating](updating.md).

## 6. Recurring Noise Windows

Surge Sentry does not ship with personal maintenance windows. Instead, it records repeated DNS, DIRECT-domain, and proxy noise that appears in the same weekday/time bucket. When a pattern repeats enough times, it reports the pattern as a candidate and asks the user to confirm whether it is caused by router reboot, ISP maintenance, or another fixed schedule.

After confirmation, configure a local-only `.env` value:

```bash
MAINTENANCE_WINDOWS="thu 05:00-05:10:dns,direct_domain_failure,proxy"
```

This suppresses only the selected transient kinds inside that window. Keep this setting local; do not commit personal schedules to the public repo.

## 7. Traffic Analysis And Event Monitors

Surge Sentry has two traffic features. Both read local Surge traffic SQLite files only; they do not packet-capture or save request bodies.

The first is low-overhead daily risk analysis. It can warn when a monitored policy is far above the conservative daily budget for the current billing cycle, or when direct-preferred media traffic appears to be using a proxy policy.

The second is a focused event monitor. Use it when you want to know how much traffic one real scenario consumed: an F1 race, a World Cup Fox stream, an Apple TV movie, a remote sync, or a large download.

Start before the event:

```bash
scripts/surge-sentry traffic start f1-race --note "Apple TV F1 race"
```

Check while it is running:

```bash
scripts/surge-sentry traffic status f1-race
```

Finish and archive the final report:

```bash
scripts/surge-sentry traffic end f1-race
```

The report includes new traffic for the monitored period, policy totals, top hosts, download/upload split, and request counts. It does not replace Surge's traffic UI; it saves a start baseline and compares against it so the final answer is clear for the exact scenario.

Example names:

```bash
scripts/surge-sentry traffic start world-cup-fox --note "Fox World Cup stream"
scripts/surge-sentry traffic start apple-tv-movie --note "Apple TV movie"
```

To focus on selected policies:

```bash
scripts/surge-sentry traffic start f1-race --policy-patterns "%US%,%Proxy%"
```

## 8. Real Playback CDN Health

`cdn-watch` is separate from cumulative traffic analysis. It adaptively samples only Surge active requests (10 seconds while idle, 2 seconds during matching playback) and stores only redacted host, policy, CDN class, and throughput summaries. It does not keep a high-memory CLI child, packet-capture, save request bodies, or download recent-request history.

Copy the example and enable it locally:

```bash
cp config/cdn-watch.example.json config/cdn-watch.local.json
# Set CDN_WATCH_ENABLED=1 and CDN_WATCH_CONFIG in .env
scripts/surge-sentry cdn-watch ensure
scripts/surge-sentry cdn-watch status
```

The example is observation-only by default. The initial thresholds are: `>=20 Mbps` healthy, `10-20 Mbps` usable, sustained `<10 Mbps` degraded, and sustained `<3 Mbps` for 20 seconds critical. An idle zero-speed HLS connection is not treated as a stall.

Locally verified exact hosts may opt into allowlisted repair. The local config must be a current-user-owned, non-symlink `0600` file; repair resolvers must be literal IP addresses. The fixed workflow is: backup the profile, edit exact `[Host]` entries only, validate, reload, confirm the override is active at runtime, flush DNS, notify that repair is complete, and verify later connections on the expected CDN at usable speed. Reopening the app is optional advice only when playback still has trouble; repair never waits for that action. Mutation checks fail closed and roll back immediately, while post-repair failures are accepted only from a connection created after the safety grace window. Large media traffic is never moved to a costly proxy automatically.

Escalated events remain inflight until Hermes successfully handles them. Silent resolutions use `scripts/surge-sentry cdn-watch ack <event-id>`. User-facing resolutions pipe the message to `scripts/surge-sentry cdn-watch resolve <event-id> --file -`; delivery must succeed before the event is acknowledged. Unacknowledged events are retried.

## 9. Safety Boundary

Regardless of runtime, the assistant only performs low-risk actions by default: reading state, updating external resources, flushing the Surge DNS cache, retesting policies, and adding or removing temporary runtime rules.

Permanent profile edits, certificates, DNS records, servers, MITM, Rewrite, Scripting, Replica, reload, restart, profile selection, and policy-group selection require user confirmation. The only exception is an exact-host allowlist explicitly enabled by the user in local `cdn-watch.local.json`; backup, validation, verification, and rollback still remain mandatory.
