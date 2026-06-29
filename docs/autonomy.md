# Autonomy Model

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/autonomy.zh-CN.md) | [繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/autonomy.zh-TW.md)

Surge Sentry uses layered autonomy.

## Automatic

- update external resources when resource errors appear
- flush DNS after repeated DNS errors
- retest policies and groups before escalating
- add narrow temporary runtime rules for repeated DIRECT failures
- review and remove temporary rules after a cooldown
- suppress recovered single-event policy failures

## Conditional

- temporary policy switching can be added after the sentry has enough evidence
  that the target policy is healthy and the current policy is repeatedly failing

## Confirmation Required

- permanent profile edits
- `.conf` or `.sgmodule` changes
- Surge restart, stop, reload, or profile switch
- long-term policy-group selection changes
- MITM, Rewrite, Scripting, Replica, or capture changes
- certificate, DNS record, server, or account changes
- broad deletion of temporary rules
