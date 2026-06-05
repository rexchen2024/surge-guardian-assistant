# Surge Hermes Guardian

Surge Hermes Guardian is a lightweight autonomous guardian for Surge on macOS.
It is designed to run from Hermes cron every minute, stay silent when healthy,
and wake a model only when the local deterministic checks find something worth
analysis.

The operating rule is simple: keep Surge healthy, reduce recurring errors, and
avoid bothering the user unless the issue is fixed and worth mentioning or is
too risky to handle automatically.

## What It Does

- Reads new Surge log lines and `surge-cli --raw dump event`.
- Classifies external resource, DNS, policy, runtime, and repeated DIRECT failures.
- Runs low-risk remediation automatically:
  - `external-resource update all`
  - `flush dns`
  - policy retests
  - temporary runtime rules with later review/removal
- Uses `{"wakeAgent": false}` to skip Hermes/model work for normal runs.
- Emits a compact incident package when Hermes should analyze or notify.
- Keeps private domains, IPs, profile paths, policy names, and state in local `.env` and state files only.

## Quick Start

```bash
git clone <private-repo-url>
cd surge-hermes-guardian
scripts/surge-hermes-guardian setup --print-hermes-command
scripts/surge-hermes-guardian doctor
scripts/surge-hermes-guardian tick
```

Healthy `tick` output is:

```json
{"wakeAgent": false}
```

## Commands

- `setup`: interactive first-run setup. Discovers `surge-cli`, logs, profiles, and policy candidates, then writes `.env`.
- `tick`: one lightweight guardian run for Hermes cron.
- `doctor`: manual sanitized diagnostic summary.
- `redact-check`: repository scan before commit or GitHub push.

## Hermes Deployment

The recommended deployment is a Hermes cron job every minute:

```bash
scripts/surge-hermes-guardian setup --print-hermes-command
```

Review the printed command, then run it. The job should use the repository root
as `workdir` and `scripts/surge-hermes-guardian` as the script.

When `tick` prints `{"wakeAgent": false}`, Hermes skips the model entirely. Any
other output wakes Hermes and the job prompt tells the model how to decide
whether to stay silent, report a handled issue, or ask for user confirmation.

## Autonomy Boundary

Automatically allowed:

- external resource update
- DNS flush
- policy and group retests
- temporary runtime rules
- repeated-error counters and suppression
- later review/removal of temporary rules

Requires user confirmation:

- writing permanent profiles
- editing `.conf` or `.sgmodule`
- restarting or stopping Surge
- long-term policy-group changes
- MITM, Rewrite, Scripting, Replica changes
- certificate, DNS record, server, or account changes
- broad temp-rule deletion

## Privacy

Never commit:

- `.env`
- state or log files
- Surge profiles
- subscription URLs
- node credentials
- real domains or IPs
- notification targets

Run this before every commit:

```bash
scripts/check
```
