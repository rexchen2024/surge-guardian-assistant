# Sync Workflow

[简体中文](https://github.com/rexchen2024/surge-sentry/blob/main/docs/sync-workflow.zh-CN.md) | [繁體中文](https://github.com/rexchen2024/surge-sentry/blob/main/docs/sync-workflow.zh-TW.md)

Use this flow when local Surge scripts evolve and the GitHub project should learn
from them.

1. Copy only the reusable behavior into `surge_sentry/`.
2. Replace real domains, IPs, paths, policy names, and user identifiers with configuration.
3. Add or update a test for the behavior.
4. Run:

```bash
scripts/check
```

5. Commit only after `redact-check` passes.
