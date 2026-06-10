# 同步流程

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/sync-workflow.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/sync-workflow.zh-CN.md)

当本地 Surge 脚本继续演进，并且 GitHub 项目需要吸收这些能力时，使用这个流程。

1. 只把可复用行为复制到 `guardian/`。
2. 将真实域名、IP、路径、策略名称和用户标识替换为配置项。
3. 为该行为新增或更新测试。
4. 运行：

```bash
scripts/check
```

5. 只有在 `redact-check` 通过后才提交。

