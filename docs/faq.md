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

Yes. Hermes is strong for always-on scheduling and message delivery; Codex is strong for open-source project-style checks, diagnostics, review, and maintenance. Choose the path that fits your workflow.

## What Is Codex Edition For?

Codex Edition is for install checks, Surge config diagnostics, incident review, traffic-monitor interpretation, documentation updates, and ongoing maintenance.

Codex does not need to run every minute. Keep healthy checks lightweight on local scripts; use Codex when you need explanation, judgment, or improvement.

## Can Automatic Updates Overwrite My Changes?

No.

If local tracked files were changed, automatic updates skip. You can check manually:

```bash
scripts/surge-sentry update --check
```

## Does It Upload Logs Or Usage Data?

No automatic upload happens.

Feedback reports are generated only when the user asks, and can be reviewed locally first:

```bash
scripts/surge-sentry feedback --print
```
