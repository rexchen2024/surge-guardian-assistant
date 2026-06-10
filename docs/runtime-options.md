# Runtime Options

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/runtime-options.zh-CN.md) | [繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/runtime-options.zh-TW.md)

Surge Guardian Assistant has one core loop and three practical ways to run it.

## 1. Choose A Runtime

**1. Recommended Hermes Agent**

Best for always-on monitoring, incident notifications, and learning from repeated patterns. Healthy checks stay silent; important issues can wake AI.

[Read Hermes setup](hermes-edition.md)

**2. Local-only**

Best when you only want to check Surge from the local terminal. This is the lightest path: local scripts plus `surge-cli`.

**3. Codex Edition**

Best for lower-frequency repository checks, incident review, and project maintenance. It is not recommended for minute-level monitoring.

[Read Codex setup](codex-edition.md)

## 2. Common One-Command Install

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

The installer puts the project in `~/.surge-guardian-assistant`, checks the Surge environment, and starts first-run setup.

## 3. Verify It Works

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
```

`doctor` checks the Surge command, logs, and local config. `tick` performs one real check. Healthy output is:

```json
{"wakeAgent": false}
```

## 4. Run Local-only Mode

Local-only mode can be scheduled with launchd, cron, or another local scheduler:

```bash
/path/to/surge-guardian-assistant/scripts/surge-guardian-assistant tick >> "$HOME/Library/Logs/surge-guardian-assistant.log" 2>&1
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

## 6. Safety Boundary

Regardless of runtime, the assistant only performs low-risk actions by default: reading state, updating external resources, flushing the Surge DNS cache, retesting policies, and adding or removing temporary runtime rules.

Permanent profile edits, certificates, DNS records, servers, MITM, Rewrite, Scripting, Replica, reload, restart, profile selection, and policy-group selection require user confirmation.
