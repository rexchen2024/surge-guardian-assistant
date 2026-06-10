# Surge 守护助手

[![Release](https://img.shields.io/github/v/release/rexchen2024/surge-guardian-assistant?label=release)](https://github.com/rexchen2024/surge-guardian-assistant/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[繁體中文（香港）](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.zh-HK.md) | [繁體中文（台灣）](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.zh-TW.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.en.md)

面向 Surge 用户的静默巡检和自愈工具。它基于 Surge 官方 Agent Skill / `surge-cli` 的运行时能力，持续检查日志、事件、策略和外部资源；健康时不打扰，异常时先自愈，只有重要问题才交给 Hermes、Codex 或聊天工具继续处理。

**当前版本：0.1.0**

## 目录

- [亮点](#亮点)
- [安装方式](#安装方式)
- [一键安装](#一键安装)
- [工作方式](#工作方式)
- [自动更新](#自动更新)
- [常用命令](#常用命令)
- [文档](#文档)

## 亮点

- **极致静默、低功耗**：健康巡检只输出 `{"wakeAgent": false}`，日常路径走本地脚本和 Surge 运行时接口，尽量不启动 AI。
- **Surge 原生巡检**：读取事件、复测策略、刷新 DNS、更新外部资源、添加运行时临时规则。
- **安全自愈优先**：低风险问题先自动处理；永久配置、证书、DNS、MITM、Rewrite、Scripting、重载或重启都需要确认。
- **必要时再用 AI**：重复、复杂或未恢复的问题才交给 Hermes/Codex；重要问题再通过聊天工具推送。
- **可持续沉淀**：Hermes 版本可利用 Hermes 的记忆和技能机制，把重复问题变成后续处理经验。
- **自动更新、隐私优先**：可从 GitHub 拉取新版本；本地有改动不覆盖；不自动上传日志或使用数据。

## 安装方式

**极简本地**  
只想在本机终端检查 Surge。最轻量，脚本直接调用 `surge-cli`，适合手动检查或本地调度。  
[查看说明](docs/runtime-options.zh-CN.md)

**⭐ Hermes Agent 推荐**  
适合常驻巡检、异常通知和持续学习。健康时完全静默，重要问题再唤醒 AI，也可以通过聊天工具推送。  
[安装说明](docs/hermes-edition.zh-CN.md)

**Codex 版本**  
适合低频检查仓库、复盘异常、维护项目。不建议做每分钟巡检。  
[安装说明](docs/codex-edition.zh-CN.md)

终端能直接使用的是 Surge 的 `surge-cli`。本项目的脚本会调用它完成检查和低风险处理；Surge Agent Skill 更适合让支持的 AI 工具理解并调用这些能力，不是必须额外安装的独立运行时。

## 一键安装

默认装到 `~/.surge-guardian-assistant`：

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

如果仓库暂时还是私有的，用 Git：

```bash
git clone https://github.com/rexchen2024/surge-guardian-assistant.git ~/.surge-guardian-assistant
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant setup --print-hermes-command
```

安装后先验证：

```bash
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
```

<details>
<summary>复制给 Hermes</summary>

```text
请从 https://github.com/rexchen2024/surge-guardian-assistant 安装 Surge 守护助手，运行 setup，显示生成的 Hermes cron 命令。不要在未确认前编辑 Surge profile 或执行永久网络变更。
```

</details>

<details>
<summary>复制给 Codex</summary>

```text
请把 https://github.com/rexchen2024/surge-guardian-assistant 作为 Surge 守护助手项目安装到本地，运行 doctor 和 scripts/check，帮我创建或建议一个安全的 Codex 自动化。不要在未确认前编辑 Surge profile。
```

</details>

## 工作方式

```mermaid
flowchart LR
  Surge["Surge 日志 / 事件 / 运行时状态"] --> Tick["本地 tick 巡检"]
  Tick --> Quiet{"是否健康？"}
  Quiet -->|是| Silent["静默输出 wakeAgent:false"]
  Quiet -->|否| Heal["低风险自愈"]
  Heal --> Again{"是否恢复？"}
  Again -->|是| Silent
  Again -->|否| AI["Hermes / Codex 分析"]
  AI --> Notify["重要问题再推送或请求确认"]
```

## 项目边界

本项目主体不是 Surge 配置库、规则集、模块合集或机场推荐。它只在你已有 Surge 配置的基础上做巡检、自愈和异常反馈。

所有自动处理都尽量保持小范围、运行时、可回退。涉及永久配置的动作，都应该由用户确认后再执行。

## 自动更新

只要安装目录是 Git 仓库，并且 Hermes/Codex/系统任务还在运行 `tick`，它会默认每天检查一次 GitHub 更新。

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant update --check
scripts/surge-guardian-assistant update
```

不想自动更新，在 `.env` 里写：

```bash
AUTO_UPDATE=0
```

## 常用命令

```bash
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
scripts/surge-guardian-assistant version
scripts/surge-guardian-assistant update
scripts/surge-guardian-assistant feedback
scripts/surge-guardian-assistant redact-check
```

## 文档

- [Hermes 版本](docs/hermes-edition.zh-CN.md)
- [Codex 版本](docs/codex-edition.zh-CN.md)
- [升级](docs/updating.zh-CN.md)
- [自治模型](docs/autonomy.zh-CN.md)
- [故障排查](docs/troubleshooting.zh-CN.md)
- [常见问题](docs/faq.zh-CN.md)
- [隐私说明](docs/privacy.zh-CN.md)
- [更新日志](CHANGELOG.zh-CN.md)

## 项目规则

- 许可证：[MIT](LICENSE)
- 贡献说明：[CONTRIBUTING.md](CONTRIBUTING.md)
- 安全策略：[SECURITY.md](SECURITY.md)

## 我推荐的机场

[红莓网络](https://cmy.homes/register?aff=4MMK4C)
