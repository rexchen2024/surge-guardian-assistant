# 新手上手

[English](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/onboarding.md) | [简体中文](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/onboarding.zh-CN.md)

本指南假设你已经安装了 Surge for macOS 和 Hermes。

## 1. Clone

```bash
git clone <repo-url>
cd surge-hermes-guardian
```

## 2. 运行 Setup

```bash
scripts/surge-hermes-guardian setup --print-hermes-command
```

Setup 会自动发现：

- `surge-cli`
- Surge 日志目录
- profile 候选项
- 运行时策略候选项

它会在仓库根目录写入 `.env`。它不会编辑 Surge profiles。

## 3. 本地验证

```bash
scripts/surge-hermes-guardian doctor
scripts/surge-hermes-guardian tick
```

健康状态下的 `tick` 输出是：

```json
{"wakeAgent": false}
```

## 4. 安装 Hermes Cron

检查 setup 打印出的命令，然后运行它。推荐调度频率是每分钟一次。

Hermes 会根据用户现有的 Hermes 配置处理消息投递。如果还没有配置投递目标，
请先配置一个 Hermes 支持的平台。Guardian 不要求必须使用 Telegram。

## 5. 日常使用

- 使用 `doctor` 手动查看脱敏后的状态摘要。
- 提交更改前运行 `redact-check` 或 `scripts/check`。
- 不要把 `.env`、日志、state、profiles 或真实基础设施标识提交到 Git。

