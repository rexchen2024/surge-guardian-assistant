# Surge 守护助手

[English](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/README.md) | [简体中文](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/README.zh-CN.md)

Surge 守护助手是一个面向 macOS [Surge](https://nssurge.com/) 用户的轻量级自治运维助手。它会观察 Surge 信号，执行安全范围内的恢复动作，在健康状态下保持静默，并且在高风险动作前请求用户确认。

仓库主页仍然是：

```text
https://github.com/rexchen2024/surge-hermes-guardian
```

为了保持历史链接稳定，仓库 slug 暂时保留 `surge-hermes-guardian`，但对外项目名调整为 **Surge 守护助手**。

## 选择版本

### Hermes 版本

适合生产使用。Hermes 负责分钟级守护循环，健康检查通过 `{"wakeAgent": false}` 跳过模型工作，只有脚本输出异常包时才唤醒已配置模型。

- 推荐用于常驻巡检。
- 日常噪音最低，健康状态下模型消耗最低。
- 使用 Hermes cron、memory、模型分析和消息投递渠道。
- 最适合已经安装 Hermes 和 Surge 的用户。

[安装 Hermes 版本](docs/hermes-edition.zh-CN.md)

### Codex 版本

适合定期审查、项目维护和异常复盘。Codex 可以针对这个仓库运行较低频 workspace 自动化，并使用内置 prompt 分析非静默异常或提出改进。

- 可选版本，不是默认生产运行时。
- 适合每日/每周检查、隐私扫描、代码和文档维护。
- 适合已经依赖 Codex 自动化的用户。
- 不建议替代 Hermes 做分钟级静默巡检。

[安装 Codex 版本](docs/codex-edition.zh-CN.md)

## 共享能力

- 本地读取 Surge event 和日志信号。
- 安全时自动重试外部资源。
- 重复 DNS 异常后刷新 DNS。
- 升级前先复测策略。
- 对重复 DIRECT 失败添加窄范围运行时临时规则。
- 后续复查和移除运行时临时规则。
- 本地 `.env` 和 state 文件强制使用 `0600` 权限。
- 永久 Surge profile、DNS、证书、服务器、MITM、Rewrite、Scripting、Replica、reload 或 restart 变更都必须先获得用户确认。

## 命令

- `setup`：交互式首次配置；只写入本地 `.env`。
- `tick`：执行一次轻量守护。
- `doctor`：脱敏后的手动诊断摘要。
- `redact-check`：提交或推送 GitHub 前的仓库扫描。

```bash
scripts/surge-hermes-guardian setup --print-hermes-command
scripts/surge-hermes-guardian doctor
scripts/surge-hermes-guardian tick
```

健康状态下的 `tick` 输出是：

```json
{"wakeAgent": false}
```

## 隐私

永远不要提交：

- `.env`
- state 或日志文件
- Surge profiles
- 订阅 URL
- 节点凭据
- 真实域名或 IP
- 通知目标

每次提交前运行：

```bash
scripts/check
```

## 更多文档

- [Hermes 版本](docs/hermes-edition.zh-CN.md)
- [Codex 版本](docs/codex-edition.zh-CN.md)
- [运行方式](docs/runtime-options.zh-CN.md)
- [自治模型](docs/autonomy.zh-CN.md)
- [隐私说明](docs/privacy.zh-CN.md)
- [同步流程](docs/sync-workflow.zh-CN.md)
