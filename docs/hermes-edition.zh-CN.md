# Hermes 版本

[English](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/hermes-edition.md) | [简体中文](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/hermes-edition.zh-CN.md)

Hermes 版本是 Surge 守护助手推荐的生产部署方式。

## 它做什么

- 由 Hermes cron 运行 `tick`，通常每分钟一次。
- 健康运行通过 `{"wakeAgent": false}` 保持静默。
- 只有非静默异常包才唤醒 Hermes 中已配置的模型。
- 通过 Hermes 投递渠道发送已处理摘要或确认请求。
- 永久 Surge 变更必须先获得用户确认。

## 前提条件

- 已安装并运行 Surge for macOS。
- 已安装 Hermes。
- Hermes cron 可用。
- 如果希望收到通知，Hermes 已配置可用投递目标。

投递目标可以是 Telegram、Discord、Matrix、微信、飞书、Signal，或用户 Hermes
安装支持的其他平台。

## 安装

```bash
git clone https://github.com/rexchen2024/surge-hermes-guardian.git
cd surge-hermes-guardian
scripts/surge-hermes-guardian setup --print-hermes-command
```

Setup 会自动发现：

- `surge-cli`
- Surge 日志目录
- profile 候选项
- 运行时策略候选项

它只写入本地 `.env`，不会编辑 Surge profile。

## 验证

```bash
scripts/surge-hermes-guardian doctor
scripts/surge-hermes-guardian tick
```

健康输出：

```json
{"wakeAgent": false}
```

## 创建 Hermes 任务

检查 setup 打印出的 Hermes cron 命令，然后运行它。推荐调度频率是每分钟一次。

模型分析 prompt 使用 `hermes/job-prompts/guardian.md`。它会要求 Hermes 对轻微且已处理的问题保持静默，并且在危险 Surge 变更前请求确认。

## 日常使用

- 使用 `doctor` 查看脱敏后的状态摘要。
- 发布更改前运行 `scripts/check`。
- 不要把 `.env`、日志、state、profiles 或真实基础设施标识提交到 Git。
- 常驻巡检默认推荐使用 Hermes 版本。
