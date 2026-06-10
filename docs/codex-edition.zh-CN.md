# Codex 版本

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-edition.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-edition.zh-CN.md)

Codex 版本是可选用法。它适合低频检查、分析异常包、维护仓库。不建议用它做每分钟巡检。

## 一键安装

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

如果仓库还是私有的：

```bash
git clone https://github.com/rexchen2024/surge-guardian-assistant.git ~/.surge-guardian-assistant
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant setup
scripts/surge-guardian-assistant doctor
```

## 直接复制给 Codex

```text
请把 https://github.com/rexchen2024/surge-guardian-assistant 安装到本地，作为 Surge 守护助手项目使用。请运行 doctor 和 scripts/check，然后根据 codex/automation-prompts/surge-guardian-review.md 创建或建议一个安全的 Codex 自动化。不要在未确认前编辑 Surge profile 或执行永久网络变更。
```

## 创建 Codex 自动化

自动化的工作目录选这个仓库：

```text
~/.surge-guardian-assistant
```

Prompt 模板：

```text
codex/automation-prompts/surge-guardian-review.md
```

推荐频率：

- 每天检查仓库状态和隐私风险。
- 每周复查文档和测试。
- 出现非静默异常包时再让 Codex 分析。

## 自动更新

Codex 自动化可以每天运行：

```bash
scripts/surge-guardian-assistant update --check
scripts/check
```

如果希望它直接升级，可以让自动化运行：

```bash
scripts/surge-guardian-assistant update
```

仓库有本地改动时，更新会跳过，不会覆盖。

## 安全边界

Codex 不应该直接编辑 Surge profiles、证书、DNS、MITM、Rewrite、Scripting、Replica、profile 选择、策略组选择、reload 或 restart。

如果这些动作看起来有必要，先问用户。
