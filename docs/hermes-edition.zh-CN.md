# Hermes 版本

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/hermes-edition.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/hermes-edition.zh-CN.md)

Hermes 版本是推荐用法。它适合常驻巡检：健康时不吵你，出问题时再通知。

## 一键安装

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

如果仓库还是私有的：

```bash
git clone https://github.com/rexchen2024/surge-guardian-assistant.git ~/.surge-guardian-assistant
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant setup --print-hermes-command
```

Setup 会帮你找 Surge 命令、日志目录、profile 和策略组。它只写本地 `.env`，不会改 Surge profile。

## 直接复制给 Hermes

```text
请从 https://github.com/rexchen2024/surge-guardian-assistant 安装 Surge 守护助手，运行 setup，显示生成的 Hermes cron 命令。确认命令前不要创建任务；未得到我确认前不要编辑 Surge profile 或执行永久网络变更。
```

## 创建定时任务

安装完成后，setup 会打印一条 Hermes cron 命令。检查无误后运行它。

推荐频率：每分钟一次。

模型分析 prompt 使用：

```text
hermes/job-prompts/guardian.md
```

健康输出是：

```json
{"wakeAgent": false}
```

这代表一切正常，不需要唤醒模型。

## 验证

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
```

## 自动更新

Hermes 任务会持续运行 `tick`。只要安装目录是 Git 仓库，守护助手默认每天自动检查一次 GitHub 更新。

关闭自动更新：

```bash
AUTO_UPDATE=0
```

## 常用命令

```bash
scripts/surge-guardian-assistant version
scripts/surge-guardian-assistant update --check
scripts/surge-guardian-assistant update
scripts/surge-guardian-assistant feedback
```
