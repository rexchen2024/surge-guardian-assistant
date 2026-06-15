# 更新日志

[繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.zh-TW.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.md)

## 0.1.1

- 将 CloudKit 和 Microsoft 主机视为保守 DIRECT 流量，避免守卫为这些系统服务添加临时代理规则。
- 记录 Unknown VIF virtual IP 和 DIRECT IP 连接失败这类后台噪声，但不因此唤醒 Hermes。
- 收紧 Hermes 提示词，已处理的轻微事件必须只返回 `[SILENT]`。

## 0.1.0

首个完整版本。

- 面向 Surge 日志、事件、策略和外部资源做静默巡检。
- 健康时只输出 `{"wakeAgent": false}`，尽量不唤醒 AI、不制造通知。
- 基于 Surge 官方运行时能力和 `surge-cli` 做运行时检查和低风险自愈。
- 外部资源失败自动重试，DNS 连续异常自动刷新 Surge DNS 缓存。
- 通知前复测策略状态，减少临时波动带来的误报。
- 反复 DIRECT 失败时添加小范围运行时临时规则，并定期清理。
- Hermes 版本支持常驻巡检、异常通知、记忆沉淀和必要时 AI 分析。
- Codex 版本支持低频仓库检查、异常复盘和项目维护。
- 提供一键安装、首次配置、自动更新和手动更新命令。
- 提供 `version`、`update`、`doctor`、`feedback` 和 `redact-check` 命令。
- 本地 `.env` 和 state 文件使用私有权限，不自动上传日志或使用数据。
- 反馈报告默认脱敏，提交前需要用户自行检查。
- 永久 profile 编辑、证书、DNS 记录、服务器、MITM、Rewrite、Scripting、Replica、reload、restart、profile 选择和策略组选择都需要用户确认。
