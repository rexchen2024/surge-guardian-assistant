# Surge Hermes Healthcheck

Silent-on-success Surge health checks designed for Hermes cron jobs.

The project keeps the monitoring rule simple: normal runs produce no alert; only actionable failures print output for Hermes or another scheduler to send onward.

## What It Checks

- Surge profile syntax with `surge-cli --check`
- Runtime policy availability through `surge-cli --raw dump policy`
- Policy connectivity through `surge-cli --raw test-policy`
- Public DNS for the configured domain and IP
- Port 80 reachability for certificate renewal
- TLS certificate SAN and expiry window
- Optional realtime Surge log/event monitoring with low-risk automatic cleanup

## Setup

1. Copy the example config:

```bash
cp config/example.env .env
```

2. Edit `.env` with your real profile paths, domain, IP, and policy names.

3. Run a one-off check:

```bash
scripts/surge-health-check.sh
```

No output means healthy.

## Hermes Usage

Use the scripts from a Hermes cron job or any scheduler. Keep the job output-based: if the script exits cleanly and prints nothing, do not notify.

For a daily check:

```bash
/path/to/surge-hermes-healthcheck/scripts/surge-health-check.sh
```

For realtime monitoring:

```bash
/path/to/surge-hermes-healthcheck/scripts/surge-realtime-guardian.sh
```

The realtime guardian prints `{"wakeAgent": false}` when it has nothing worth escalating. Your scheduler can treat that as silent.

## Privacy

Do not commit `.env`, state files, Surge profiles, logs, subscription URLs, node credentials, cookies, request bodies, or raw `surge-cli` dumps.

Public examples should use documentation IPs such as `203.0.113.10` and placeholder domains such as `edge.example.com`.

## Project Boundary

This repository is for lightweight local checks and reversible runtime mitigation. It is not a second routing table. Keep ACL4SSR or your active Surge profile as the routing source of truth, and use temporary rules only when real failures appear before upstream rules catch up.

