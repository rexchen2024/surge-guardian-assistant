# Codex 版本

[繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-edition.zh-TW.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-edition.md)

Codex 是 Surge Sentry 面向开源用户和本地工作区的重要客户端。它适合安装检查、Surge 配置诊断、异常复盘、流量监控结果解读、隐私检查、文档维护和安全改动建议。

它不需要替代每分钟健康闸门。健康路径仍应尽量轻，交给本地脚本或 Hermes 更合适；Codex 更适合在需要判断、解释、整理和改进时介入。

## 1. 最省事：复制给 Codex

如果你已经在用 Codex，把下面这段发给 Codex：

```text
请把 https://github.com/rexchen2024/surge-guardian-assistant 安装到本地，作为 Surge Sentry 项目使用。请运行 doctor 和 scripts/check，然后根据 codex/automation-prompts/surge-sentry-review.md 创建或建议一个安全的 Codex 自动化。不要在未确认前编辑 Surge profile、证书、DNS、服务器、MITM、Rewrite、Scripting、Replica，也不要执行 reload 或 restart。
```

Codex 应该做四件事：

1. 安装项目到本地。
2. 运行基础检查。
3. 检查 Surge Sentry 的本地配置、隐私边界和运行文档。
4. 给出 Codex 自动化建议，或帮你创建安全的 Codex 自动化。

## 2. 终端一键安装

如果你想自己在终端安装，运行：

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

安装脚本会把项目放到 `~/.surge-sentry`。

## 3. 验证项目可用

```bash
cd ~/.surge-sentry
scripts/surge-sentry doctor
scripts/check
```

`doctor` 检查本机 Surge 环境。`scripts/check` 检查项目测试、基础安全和脱敏规则。

## 4. 创建 Codex 自动化

让 Codex 使用这个工作目录：

```text
~/.surge-sentry
```

Prompt 模板：

```text
codex/automation-prompts/surge-sentry-review.md
```

推荐用途：

1. 每天检查仓库状态和隐私风险。
2. 每周复查文档、测试和配置示例。
3. 出现非静默异常包后，让 Codex 判断是临时波动、已处理问题还是需要用户确认。
4. 对 F1、世界杯 Fox、Apple TV 等流量监控结果做解释和复盘。
5. 在需要调整 Surge 配置时，先让 Codex 给出方案和风险，不直接改永久 profile。

## 5. 自动更新

Codex 自动化可以每天运行：

```bash
scripts/surge-sentry update --check
scripts/check
```

如果希望它直接升级，可以让自动化运行：

```bash
scripts/surge-sentry update
```

仓库有本地改动时，更新会跳过，不会覆盖。

## 6. 安全边界

Codex 不应该直接编辑 Surge profiles、证书、DNS 记录、服务器、MITM、Rewrite、Scripting、Replica、profile 选择、策略组选择、reload 或 restart。

如果这些动作看起来有必要，先问用户。
