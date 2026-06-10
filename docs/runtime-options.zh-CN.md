# 运行方式

[English](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/runtime-options.md) | [简体中文](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/runtime-options.zh-CN.md)

Surge Hermes Guardian 的核心循环只有一套，但有三种实际运行方式。

## 推荐：Surge + Hermes

适合希望获得自治检查、模型分析和 Hermes 通知投递的用户。

- `scripts/surge-hermes-guardian tick` 执行本地确定性检查。
- 健康输出必须精确为 `{"wakeAgent": false}`。
- 非静默输出会成为 Hermes 的现场证据包。
- Hermes 再判断应该保持静默、报告已经处理的问题，还是在高风险动作前请求确认。

这是最完整的模式，因为 Hermes 提供调度、模型推理、记忆和通知投递，
Guardian 核心不需要自己承担这些职责。

生产使用时，建议继续把它作为默认部署方式。Guardian 的
`{"wakeAgent": false}` 合同就是为 Hermes cron 设计的：健康检查可以不调用模型，
只有有证据的问题包才唤醒 agent。

## 本地模式：只有 Surge，没有 Hermes

适合机器上只有 Surge、没有 Hermes 的用户。

仍然可用：

- 日志和事件检查
- 重复错误计数
- 外部资源重试
- DNS 刷新
- 策略复测
- 窄范围临时运行时规则
- 临时规则清理和状态对账
- `doctor`、`tick` 和 `redact-check`

不会自动发生：

- 模型分析
- 聊天式解释
- 通过 Hermes memory 做跨会话学习
- 通过 Telegram、Discord、Matrix、微信、飞书、Signal 或其他 Hermes
  渠道投递通知

可以用 launchd、cron 或其他本地调度器运行。最小 launchd 任务可以调用：

```bash
/path/to/surge-hermes-guardian/scripts/surge-hermes-guardian tick >> "$HOME/Library/Logs/surge-hermes-guardian.log" 2>&1
```

本地模式下，只需要关注日志中不等于下面内容的输出：

```json
{"wakeAgent": false}
```

这个模式刻意保持简单：保留确定性的安全自治能力，但不假装替代完整 agent
运行时。

## Codex 辅助模式

Codex 适合在用户主动发起时检查仓库、审查本地状态、分析异常日志。
它很适合维护和深度排障，但不应该默认当成常驻分钟级调度器。

如果希望 Codex 参与，建议仍然把调度留在本地，只在出现非静默事件或需要优化
项目时，把异常日志或仓库状态交给 Codex 分析。这样日常路径保持轻量，
也避免把每分钟检查都变成模型任务。

Codex 自动化也可以运行定时 workspace 任务。建议把它用于较低频的审查工作，
比如每日仓库检查、每周隐私扫描，或非静默异常复盘。详见
[Codex 自动化选项](codex-automation.zh-CN.md)。

## 简单判断

- 只想要确定性自愈和手动查看：用 Surge-only 本地模式。
- 想要安静的定时自动化和通知：用 Hermes。
- 想做交互式改进、排障和项目维护：用 Codex。
