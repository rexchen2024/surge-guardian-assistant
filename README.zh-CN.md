# Surge 守护助手

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.zh-CN.md)

当前版本：**0.3.0**

Surge 守护助手会帮你盯着 Surge。正常时不吵你；出问题时先自己做安全修复；需要改危险设置时，再来问你。

项目地址：

```text
https://github.com/rexchen2024/surge-guardian-assistant
```

## 安装

一条命令：

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)"
```

如果仓库是私有的，用 Git：

```bash
git clone https://github.com/rexchen2024/surge-guardian-assistant.git
cd surge-guardian-assistant
scripts/surge-guardian-assistant setup --print-hermes-command
```

## 它会做什么

- 看 Surge 日志和事件。
- 外部资源失败时自动重试。
- DNS 连续异常时刷新 DNS。
- 通知你之前先复测策略。
- 对反复 DIRECT 失败加小范围临时规则。
- 保护本地 `.env` 和 state 文件。
- 不会擅自改永久 Surge 配置。

健康输出是：

```json
{"wakeAgent": false}
```

## 选择版本

**Hermes 版本** 是默认推荐。适合常驻巡检，正常时静默，有事再通过 Hermes 通知你。

[安装 Hermes 版本](docs/hermes-edition.zh-CN.md)

**Codex 版本** 适合低频检查和项目维护。如果你已经在用 Codex 自动化，可以选它。

[安装 Codex 版本](docs/codex-edition.zh-CN.md)

## 更新

安装后，正常巡检时会每天自动检查一次 GitHub 更新。用户改过受 Git 管理的文件时，不会覆盖。

手动升级：

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant update
```

只检查不升级：

```bash
scripts/surge-guardian-assistant update --check
```

如果不想自动更新，在 `.env` 里写：

```bash
AUTO_UPDATE=0
```

## 常用命令

```bash
scripts/surge-guardian-assistant setup --print-hermes-command
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
scripts/surge-guardian-assistant version
scripts/surge-guardian-assistant update
```

## 隐私

不要提交 `.env`、日志、state、Surge profiles、订阅 URL、节点凭据、真实域名、真实 IP 或通知目标。

发布前运行：

```bash
scripts/check
```

## 文档

- [Hermes 版本](docs/hermes-edition.zh-CN.md)
- [Codex 版本](docs/codex-edition.zh-CN.md)
- [升级](docs/updating.zh-CN.md)
- [自治模型](docs/autonomy.zh-CN.md)
- [隐私说明](docs/privacy.zh-CN.md)
- [更新日志](CHANGELOG.zh-CN.md)
