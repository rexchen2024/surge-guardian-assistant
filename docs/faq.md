# FAQ

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/faq.zh-CN.md) | [繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/faq.zh-TW.md)

## Is This A Surge Profile Repository?

No.

It does not provide Surge profiles, rule sets, modules, nodes, or subscription links. It monitors, self-heals, and reports incidents on top of an existing Surge setup.

## Does It Edit My Surge Configuration Automatically?

It does not automatically edit permanent profiles.

It only performs low-risk runtime actions, such as external-resource retry, DNS flush, policy retest, and narrow temporary rules. Permanent profile edits, certificates, DNS, MITM, Rewrite, Scripting, reload, or restart actions require user confirmation.

## Can I Use It Without Hermes?

You can run `doctor` and `tick`, and you can schedule `tick` with a local scheduler.

Hermes Edition is still recommended because Hermes is better for always-on scheduling, model analysis, and message delivery.

## What Is Codex Edition For?

Codex Edition is for lower-frequency repository checks, incident review, documentation updates, and ongoing maintenance.

It is not recommended for minute-level health checks. The healthy path should stay lightweight and should not start a model task every time.

## Can Automatic Updates Overwrite My Changes?

No.

If local tracked files were changed, automatic updates skip. You can check manually:

```bash
scripts/surge-guardian-assistant update --check
```

## Does It Upload Logs Or Usage Data?

No automatic upload happens.

Feedback reports are generated only when the user asks, and can be reviewed locally first:

```bash
scripts/surge-guardian-assistant feedback --print
```
