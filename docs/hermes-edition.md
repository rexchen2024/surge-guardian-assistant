# Hermes Edition

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/hermes-edition.zh-CN.md)

Hermes Edition is the recommended setup. It is for always-on monitoring: quiet when healthy, noisy only when something needs attention.

## One-Command Install

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

Setup finds the Surge command, log directory, profiles, and policy groups. It writes only local `.env`; it does not edit Surge profiles.

## Prompt For Hermes

```text
Install Surge Guardian Assistant from https://github.com/rexchen2024/surge-guardian-assistant, run setup, and show me the generated Hermes cron command. Do not create the job until I confirm it. Do not edit Surge profiles or make permanent network changes without asking me first.
```

## Create The Schedule

After setup, the tool prints a Hermes cron command. Review the path, frequency, and job name before running it.

Recommended frequency: once per minute.

Model-analysis prompt:

```text
hermes/job-prompts/guardian.md
```

Healthy output:

```json
{"wakeAgent": false}
```

That means nothing needs model attention.

## Verify

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
```

## Automatic Updates

The Hermes job keeps running `tick`. If the install path is a Git checkout, the assistant checks GitHub for updates once a day by default.

Turn it off by writing this in the install directory's `.env`:

```bash
AUTO_UPDATE=0
```

## Useful Commands

```bash
scripts/surge-guardian-assistant version
scripts/surge-guardian-assistant update --check
scripts/surge-guardian-assistant update
scripts/surge-guardian-assistant feedback
```
