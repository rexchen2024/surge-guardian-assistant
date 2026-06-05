# Surge Hermes Guardian

[English](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/README.md) | [简体中文](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/README.zh-CN.md)

Surge Hermes Guardian 是一个轻量级自治运维 agent，面向已经在 macOS
上运行 [Surge](https://nssurge.com/) 并使用 Hermes 做定时 agent
任务的用户。它通过 Hermes cron 持续守护 Surge，能自行处理安全范围内的
修复动作，并且只在证据值得分析时才唤醒模型。

它的目标不是制造更多提醒，而是让 Surge 尽可能保持健康，减少重复网络错误，
从长期模式中学习，并且只在问题被有效处理、或高风险动作需要用户确认时通知用户。

## 为什么使用它

- **快速上手**：运行一条 setup 命令，检查生成的 Hermes 命令，然后创建守护任务。
- **默认静默**：健康运行返回 `{"wakeAgent": false}`，Hermes 不调用模型，也不发送消息。
- **安全自治**：可自动更新外部资源、刷新 DNS、复测策略，并添加窄范围临时运行时规则。
- **需要时调用模型**：非静默事件会唤醒 Hermes，使用用户已配置的模型和通知渠道。
- **隐私优先**：真实域名、IP、profile 路径、策略名称、日志和状态只保存在本地 `.env` 与本地 state 文件中。

## 推荐安装方式

前提条件：

- 已安装并运行 Surge for macOS。
- 已安装 Hermes，且 Hermes gateway/cron 系统可用。
- 如果希望收到通知，Hermes 中应已有可用投递目标。它可以是 Telegram、
  Discord、Matrix、微信、飞书、Signal，或你的 Hermes 安装支持的其他平台。
  Guardian 不绑定某一种固定社交渠道。

安装：

```bash
git clone <repo-url>
cd surge-hermes-guardian
scripts/surge-hermes-guardian setup --print-hermes-command
```

配置向导会自动发现 `surge-cli`、Surge 日志、profile 候选项和运行时策略候选项，
然后写入本地 `.env`。它不会编辑 Surge profile。

接着运行本地检查：

```bash
scripts/surge-hermes-guardian doctor
scripts/surge-hermes-guardian tick
```

健康状态下的 `tick` 输出是：

```json
{"wakeAgent": false}
```

最后，检查并运行 setup 打印出的 Hermes cron 命令。推荐调度频率是每分钟一次。

## 命令

- `setup`：交互式首次配置；只写入本地 `.env`。
- `tick`：供 Hermes cron 调用的一次轻量守护运行。
- `doctor`：脱敏后的手动诊断摘要。
- `redact-check`：提交或推送 GitHub 前的仓库扫描。

## Hermes 如何参与

Guardian 脚本在本地完成确定性工作。没有重要事件时，它返回
`{"wakeAgent": false}`，Hermes 不会调用模型。

当脚本输出事件包时，Hermes 会唤醒已配置的模型，并使用
`hermes/job-prompts/guardian.md` 判断应该保持静默、报告已处理的问题，
还是请求用户确认高风险动作。消息投递由 Hermes 根据用户当前配置完成。

## 自治边界

自动允许：

- 更新外部资源
- 刷新 DNS
- 复测策略和策略组
- 窄范围临时运行时规则
- 重复错误计数和抑制
- 后续复查/移除临时规则

需要用户确认：

- 写入永久 profile
- 编辑 `.conf` 或 `.sgmodule`
- 重启、停止、reload 或切换 Surge profile
- 长期策略组变更
- MITM、Rewrite、Scripting、Replica 或抓包变更
- 证书、DNS 记录、服务器或账号变更
- 大范围删除临时规则

## 隐私与发布

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

更多文档：

- [新手上手](docs/onboarding.zh-CN.md)
- [自治模型](docs/autonomy.zh-CN.md)
- [隐私说明](docs/privacy.zh-CN.md)
- [同步流程](docs/sync-workflow.zh-CN.md)
