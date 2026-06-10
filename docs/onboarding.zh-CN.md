# 快速上手

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/onboarding.md)

本指南假设你已经安装了 Surge for macOS。Hermes 是推荐的定时模型辅助运行方式，
但本地 `doctor` 和 `tick` 命令不依赖 Hermes，也可以单独运行。

## 1. 获取项目

```bash
git clone https://github.com/rexchen2024/surge-guardian-assistant.git ~/.surge-guardian-assistant
cd ~/.surge-guardian-assistant
```

## 2. 运行 Setup

```bash
scripts/surge-guardian-assistant setup --print-hermes-command
```

Setup 会自动发现：

- `surge-cli`
- Surge 日志目录
- profile 候选项
- 运行时策略候选项

它会在仓库根目录写入 `.env`。它不会编辑 Surge profiles。

## 3. 本地验证

```bash
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
```

健康状态下的 `tick` 输出是：

```json
{"wakeAgent": false}
```

## 4. 选择运行方式

如果使用推荐的 Hermes 工作流，检查 setup 打印出的命令，然后运行它。
推荐调度频率是每分钟一次。

Hermes 会根据用户现有的 Hermes 配置处理消息投递。如果还没有配置投递目标，
请先配置一个 Hermes 支持的平台。Guardian 不要求必须使用 Telegram。

如果这台机器只有 Surge、没有 Hermes，可以用 launchd 或其他本地调度器运行
`tick`，然后只查看不等于 `{"wakeAgent": false}` 的输出。详见
[运行方式](runtime-options.zh-CN.md)。

## 5. 日常使用

- 使用 `doctor` 手动查看脱敏后的状态摘要。
- 使用 `update --check` 检查 GitHub 是否有新版本。
- 使用 `feedback` 生成脱敏反馈报告。
- 提交更改前运行 `redact-check` 或 `scripts/check`。
- 不要把 `.env`、日志、state、profiles 或真实基础设施标识提交到 Git。
