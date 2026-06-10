# Surge 守护助手

[![Release](https://img.shields.io/github/v/release/rexchen2024/surge-guardian-assistant?label=release)](https://github.com/rexchen2024/surge-guardian-assistant/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.zh-TW.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/README.en.md)

面向 Surge 用户的静默巡检和自愈工具。它基于 Surge 官方运行时能力和 `surge-cli`，持续检查日志、事件、策略和外部资源；健康时不打扰，异常时先自愈，只有重要问题才交给 Hermes、Codex 或聊天工具继续处理。

**当前版本：0.1.0**

本项目仍在初期测试阶段，欢迎试用并提供反馈建议。后续会根据实际使用体验持续更新。

## 目录

- [亮点](#亮点)
- [工作方式](#工作方式)
- [安装方式](#安装方式)
- [文档](#文档)
- [项目资料](#项目资料)
- [我的推荐](#我的推荐)


---

## 亮点

- **极致静默、低功耗**：健康巡检只输出 `{"wakeAgent": false}`，日常路径走本地脚本和 Surge 运行时接口，尽量不启动 AI。
- **Surge 原生巡检**：读取事件、复测策略、刷新 DNS、更新外部资源、添加运行时临时规则。
- **安全自愈优先**：低风险问题先自动处理；动作尽量小范围、运行时、可回退；永久配置、证书、DNS 记录、服务器、MITM、Rewrite、Scripting、重载或重启都需要确认。
- **必要时再用 AI**：重复、复杂或未恢复的问题才交给 Hermes/Codex；重要问题再通过聊天工具推送。
- **可持续沉淀**：Hermes 版本可利用 Hermes 的记忆和技能机制，把重复问题变成后续处理经验。
- **自动更新、隐私优先**：可从 GitHub 拉取新版本；本地有改动不覆盖；不自动上传日志或使用数据。


---

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


---

## 安装方式

**1. 终端**

只想在本机终端检查 Surge。最轻量，脚本直接调用 `surge-cli`，适合手动检查或本地调度。

[一键安装和本地运行说明](docs/runtime-options.zh-CN.md)

**2. 🌟推荐 - Hermes Agent**

常驻巡检、异常通知、持续学习的首选方式。健康时完全静默，重要问题再唤醒 AI，也可以通过聊天工具推送。

[一键安装和 Hermes 任务说明](docs/hermes-edition.zh-CN.md)

**3. Codex**

适合低频检查仓库、复盘异常、维护项目。不建议做每分钟巡检。

[一键安装和 Codex 自动化说明](docs/codex-edition.zh-CN.md)

脚本直接调用 Surge 的 `surge-cli`。一键安装、自动更新、任务频率和安全边界，都在对应说明里。


---

## 文档

- [Hermes 版本](docs/hermes-edition.zh-CN.md)
- [Codex 版本](docs/codex-edition.zh-CN.md)
- [运行方式](docs/runtime-options.zh-CN.md)
- [升级](docs/updating.zh-CN.md)
- [自治模型](docs/autonomy.zh-CN.md)
- [故障排查](docs/troubleshooting.zh-CN.md)
- [常见问题](docs/faq.zh-CN.md)
- [隐私说明](docs/privacy.zh-CN.md)
- [更新日志](CHANGELOG.zh-CN.md)


---

## 项目资料

- 许可证：[MIT](LICENSE)
- 贡献说明：[CONTRIBUTING.md](CONTRIBUTING.md)
- 安全策略：[SECURITY.md](SECURITY.md)
- 行为准则：[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)


---

## 我的推荐

<img src="assets/brand/cmynetwork-icon.png" alt="红莓网络" width="18" align="absmiddle"> [红莓网络](https://cmy.homes/register?aff=4MMK4C)：用了多年的机场，即便是在特殊时期也高度可用，对 Clash 规则友好。
