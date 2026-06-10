# Codex 版本

[English](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/codex-edition.md) | [简体中文](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/codex-edition.zh-CN.md)

Codex 版本是可选部署方式，适合希望用 Codex 检查项目、分析非静默异常、并提出改进的用户。

它不是默认生产运行时。分钟级静默巡检仍然更适合 Hermes 版本。

## 它做什么

- 运行较低频的 Codex workspace 自动化。
- 检查仓库健康度和隐私风险。
- 运行 `scripts/check`。
- 在提供非静默异常包时进行分析。
- 在重复模式出现后建议代码或文档改进。

## 前提条件

- 已安装并运行 Surge for macOS。
- Codex 可以访问本地仓库 workspace。
- 用户可以使用 Codex 自动化。
- 用户接受所选频率下的模型分析任务。

## 安装

```bash
git clone https://github.com/rexchen2024/surge-hermes-guardian.git
cd surge-hermes-guardian
scripts/surge-hermes-guardian setup --print-hermes-command
scripts/surge-hermes-guardian doctor
```

setup 仍然写入同一份本地 `.env`，因为两个版本共享确定性守护逻辑。

## 创建 Codex 自动化

创建一个指向本仓库根目录的 Codex workspace automation。Prompt 模板使用：

```text
codex/automation-prompts/surge-guardian-review.md
```

推荐频率：

- 每日做仓库健康检查
- 每周做隐私和文档检查
- 出现非静默异常包时按需分析

不建议用 Codex 做分钟级健康巡检。Codex automation 会启动一次 Codex 任务，
而 Hermes 在健康运行时可以完全跳过模型工作。

## 安全边界

Codex 自动化不应该直接编辑 Surge profiles、`.conf`、`.sgmodule`、证书、DNS
记录、服务器设置、MITM、Rewrite、Scripting、Replica、profile 选择、策略组选择、
reload 或 restart 行为。

如果这些动作看起来有必要，Codex 应该先请求用户确认，而不是直接执行。
