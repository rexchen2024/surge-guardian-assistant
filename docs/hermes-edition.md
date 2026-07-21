# Hermes Edition

[简体中文](https://github.com/rexchen2024/surge-sentry/blob/main/docs/hermes-edition.zh-CN.md) | [繁體中文](https://github.com/rexchen2024/surge-sentry/blob/main/docs/hermes-edition.zh-TW.md)

Hermes Edition is the recommended setup. It is for always-on monitoring: quiet when healthy, noisy only when something needs attention.

## 1. Easiest: Paste This Into Hermes

If you already use Hermes, send it this prompt:

```text
Install Surge Sentry from https://github.com/rexchen2024/surge-sentry, run setup, check the Surge environment, and show me the generated Hermes cron command. Do not create the job until I confirm it. Do not edit Surge profiles, certificates, DNS, servers, MITM, Rewrite, Scripting, or Replica, and do not run reload or restart without asking me first.
```

Hermes should do three things:

1. Install the project locally.
2. Run setup and basic checks.
3. Show you the generated Hermes cron command for confirmation.

Before confirmation, it should not create the job or make permanent Surge changes.

## 2. Terminal One-Command Install

If you prefer doing it yourself in Terminal, run:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-sentry/main/install.sh)" -- --setup
```

The project installs to `~/.surge-sentry`. Setup finds the Surge command, log directory, profiles, and policy groups. It writes only local `.env`; it does not edit Surge profiles.

## 3. Verify The Local Check

```bash
cd ~/.surge-sentry
scripts/surge-sentry doctor
scripts/surge-sentry tick
```

Healthy output is:

```json
{"wakeAgent": false}
```

That means nothing needs model attention.

## 4. Create The Hermes Schedule

Setup prints a Hermes cron command. Check three things first:

1. The job name is `Surge Sentry`.
2. The working directory points to `~/.surge-sentry`.
3. The frequency is what you want. Once per minute is recommended.

Run the command only after confirming it. The model-analysis prompt is:

```text
hermes/job-prompts/sentry.md
```

## 5. Automatic Updates

The Hermes job keeps running `tick`. If the install path is a Git checkout, the assistant checks GitHub for updates once a day by default.

Turn it off by writing this in the install directory's `.env`:

```bash
AUTO_UPDATE=0
```

## 6. Safety Boundary

Hermes can schedule, analyze, and notify, but it should not directly perform permanent Surge changes. The assistant can automatically do low-risk actions such as reading state, updating external resources, flushing the Surge DNS cache, retesting policies, and adding or removing temporary runtime rules.

Permanent profile edits, certificates, DNS records, servers, MITM, Rewrite, Scripting, Replica, reload, restart, profile selection, and policy-group selection require user confirmation.

## 7. Useful Commands

```bash
scripts/surge-sentry version
scripts/surge-sentry update --check
scripts/surge-sentry update
scripts/surge-sentry feedback
```
