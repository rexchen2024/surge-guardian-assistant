# Surge Hermes Guardian

[English](README.md) | [简体中文](README.zh-CN.md)

Surge Hermes Guardian 是一个面向 macOS Surge 的轻量级自治守护项目。
它设计为由 Hermes cron 每分钟运行一次，在健康时保持静默，
只有当本地确定性检查发现值得分析的问题时才唤醒模型。

它的运行原则很简单：保持 Surge 健康，减少重复错误，
并避免打扰用户，除非问题已经被处理且值得告知，或风险过高需要用户确认。

## 功能

- 读取新的 Surge 日志行和 `surge-cli --raw dump event`。
- 分类外部资源、DNS、策略、运行时和重复 DIRECT 失败。
- 自动执行低风险修复：
  - `external-resource update all`
  - `flush dns`
  - 策略复测
  - 临时运行时规则，并在之后复查/移除
- 使用 `{"wakeAgent": false}` 跳过正常运行时的 Hermes/模型工作。
- 当需要 Hermes 分析或通知时，输出紧凑的事件包。
- 将私人域名、IP、profile 路径、策略名称和状态只保存在本地 `.env` 和 state 文件中。

## 快速开始

```bash
git clone <private-repo-url>
cd surge-hermes-guardian
scripts/surge-hermes-guardian setup --print-hermes-command
scripts/surge-hermes-guardian doctor
scripts/surge-hermes-guardian tick
```

健康状态下的 `tick` 输出是：

```json
{"wakeAgent": false}
```

## 命令

- `setup`：交互式首次配置。发现 `surge-cli`、日志、profiles 和策略候选项，然后写入 `.env`。
- `tick`：供 Hermes cron 调用的一次轻量守护运行。
- `doctor`：手动脱敏诊断摘要。
- `redact-check`：提交或推送 GitHub 前的仓库扫描。

## Hermes 部署

推荐部署方式是每分钟运行一次的 Hermes cron job：

```bash
scripts/surge-hermes-guardian setup --print-hermes-command
```

检查打印出的命令，然后运行它。该 job 应使用仓库根目录作为 `workdir`，
并使用 `scripts/surge-hermes-guardian` 作为脚本。

当 `tick` 打印 `{"wakeAgent": false}` 时，Hermes 会完全跳过模型。
任何其他输出都会唤醒 Hermes，job prompt 会告诉模型如何决定是保持静默、
报告已处理的问题，还是请求用户确认。

## 自治边界

自动允许：

- 更新外部资源
- 刷新 DNS
- 复测策略和策略组
- 临时运行时规则
- 重复错误计数和抑制
- 后续复查/移除临时规则

需要用户确认：

- 写入永久 profile
- 编辑 `.conf` 或 `.sgmodule`
- 重启或停止 Surge
- 长期策略组变更
- MITM、Rewrite、Scripting、Replica 变更
- 证书、DNS 记录、服务器或账号变更
- 大范围删除临时规则

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
