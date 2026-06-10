# Codex 自动化说明

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-automation.md)

Codex 可以作为 Surge 守护助手的分析和维护层，但不应该作为主要运行时。

安装步骤见 [Codex 版本](codex-edition.zh-CN.md)。

## 推荐边界

生产守护仍然建议交给 Hermes：

- Hermes cron 执行分钟级 `tick`。
- `{"wakeAgent": false}` 让健康检查跳过模型工作。
- 非静默输出再唤醒 Hermes 做模型分析和投递。

Codex 自动化适合较低频工作：

- 每日或每周仓库检查
- `scripts/check` 校验
- 隐私/脱敏审计
- 复盘非静默异常包
- 在重复模式出现后建议代码或文档改进

这样可以保持便宜路径真的便宜。Codex cron job 很有用，但它仍然会启动一次
Codex 任务，所以不应该替代 Hermes 的分钟级健康闸门。

## Codex + Surge 版本

如果用户已经依赖 Codex 自动化，并且希望把项目维护或异常分析放到 Codex 里，
那么 Codex + Surge 版本是可行的。

适合：

- 机器有 Surge，并且 Codex 能访问本地 workspace
- 用户想做周期性项目检查或异常复盘
- 频率是每小时、每天或每周
- 每次计划运行都可以接受模型分析

不适合：

- 严格的分钟级常驻监控
- 对电量、带宽、成本非常敏感的机器
- 希望健康检查完全不调用模型的用户
- 已经通过 Hermes 获得更好通知投递的场景

## 自动化 Prompt

可以用 `codex/automation-prompts/surge-guardian-review.md` 作为 Codex
workspace 自动化的起点。自动化的工作目录指向仓库根目录即可。

这个 prompt 会明确要求 Codex 把 Hermes 作为默认运行时，并且在用户明确确认前，
不要执行永久 Surge 变更。

## 安全规则

- 不要把原始 Surge profiles、订阅、请求体或私人日志粘到 Codex prompt 里。
- 优先使用 `scripts/check`、`doctor`、摘要 state 和非静默异常包。
- 不要让 Codex 自动化直接编辑 Surge profiles。
- 永久路由、DNS、证书、服务器、MITM、Rewrite、Scripting、Replica、reload
  和 restart 变更都必须等待用户明确确认。
- 如果一次运行没有可执行问题，最终回复应该简短，避免制造通知噪音。
