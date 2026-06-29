# Codex 自动化说明

[繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-automation.zh-TW.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-automation.md)

Codex 可以作为 Surge Sentry 的独立使用路线：负责安装、检查、解释、复盘和维护。健康巡检仍由本地脚本完成，Codex 在需要判断和改进时介入。

安装步骤见 [Codex 版本](codex-edition.zh-CN.md)。

## 推荐边界

如果你选择 Hermes 路线：

- Hermes cron 执行分钟级 `tick`。
- `{"wakeAgent": false}` 让健康检查跳过模型工作。
- 非静默输出再唤醒 Hermes 做模型分析和投递。

如果你选择 Codex 路线：

- 每日或每周仓库检查
- `scripts/check` 校验
- 隐私/脱敏审计
- 复盘非静默异常包
- 解释 F1、世界杯 Fox、Apple TV 等流量监控结果
- 诊断 Surge 配置风险并提出改动方案
- 在重复模式出现后建议代码或文档改进

这样可以保持健康路径足够轻，同时让 Codex 做更擅长的判断、解释和项目维护。

## Codex + Surge 版本

如果用户已经依赖 Codex 自动化，或者希望用开源项目和本地 workspace 管理 Surge Sentry，那么 Codex + Surge 版本是可行的。

使用建议：

- 机器有 Surge，并且 Codex 能访问本地 workspace
- 用户想做周期性项目检查或异常复盘
- 频率是每小时、每天或每周
- 每次计划运行都可以接受模型分析
- 分钟级健康检查仍由 `scripts/surge-sentry tick` 这类本地脚本承担

## 自动化 Prompt

可以用 `codex/automation-prompts/surge-sentry-review.md` 作为 Codex
workspace 自动化的起点。自动化的工作目录指向仓库根目录即可。

这个 prompt 会明确要求 Codex 保持 Surge 配置安全边界，并且在用户明确确认前，不要执行永久 Surge 变更。

## 安全规则

- 不要把原始 Surge profiles、订阅、请求体或私人日志粘到 Codex prompt 里。
- 优先使用 `scripts/check`、`doctor`、摘要 state 和非静默异常包。
- 不要让 Codex 自动化直接编辑 Surge profiles。
- 永久路由、DNS、证书、服务器、MITM、Rewrite、Scripting、Replica、reload
  和 restart 变更都必须等待用户明确确认。
- 如果一次运行没有可执行问题，最终回复应该简短，避免制造通知噪音。
