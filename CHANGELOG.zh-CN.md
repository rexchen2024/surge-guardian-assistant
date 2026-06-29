# 更新日志

[繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.zh-TW.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.md)

## 0.2.0

- 加入本地可配置的固定维护窗口，用于压制 DNS、DIRECT 域名失败和代理瞬时噪声；默认不启用任何个人窗口。
- 检测相同星期/时间段反复出现的噪声，并先作为可能的路由器、运营商或上游维护模式提示用户确认，再决定是否配置静默。
- 按 key 合并重复的压制记录，让本地状态保留计数，但不堆积重复条目。
- 记录更严格的 Hermes 投递契约：只有最终回复精确等于 `[SILENT]` 才静默；“解释 + [SILENT]”会正常投递。
- 为 live Hermes 里的高频 Surge Sentry 静默输出加入 24 小时保留策略。
- 强化 Codex 路线说明：Codex 可作为开源用户的独立使用客户端，用于安装检查、Surge 配置诊断、异常复盘、流量监控解读和安全改动建议。
- 新增项目式流量监控命令，支持 F1、世界杯 Fox、Apple TV 等具体场景的开始、进行中和结束流量报告。
- 验证记录：仓库 `scripts/check` 通过，live 脚本语法检查通过，临时 HOME 烟测返回 `{"wakeAgent": false}`，Hermes cron 调度器测试通过。

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
- Codex 版本支持安装检查、配置诊断、异常复盘和项目维护。
- 提供一键安装、首次配置、自动更新和手动更新命令。
- 提供 `version`、`update`、`doctor`、`feedback` 和 `redact-check` 命令。
- 本地 `.env` 和 state 文件使用私有权限，不自动上传日志或使用数据。
- 反馈报告默认脱敏，提交前需要用户自行检查。
- 永久 profile 编辑、证书、DNS 记录、服务器、MITM、Rewrite、Scripting、Replica、reload、restart、profile 选择和策略组选择都需要用户确认。
