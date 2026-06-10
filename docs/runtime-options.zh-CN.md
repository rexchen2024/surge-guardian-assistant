# 运行方式

[繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/runtime-options.zh-TW.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/runtime-options.md)

Surge 守护助手的核心循环只有一套，但有三种实际运行方式。

## 1. 先选运行方式

**1. 终端**

适合只想在本机终端检查 Surge 的用户。最轻量，只运行本地脚本和 `surge-cli`。

**2. 🌟推荐 - Hermes Agent**

适合常驻巡检、异常通知和持续学习。健康时静默，重要问题再唤醒 AI。

[查看 Hermes 安装](hermes-edition.zh-CN.md)

**3. Codex**

适合低频检查仓库、复盘异常和维护项目。不建议做每分钟巡检。

[查看 Codex 安装](codex-edition.zh-CN.md)

## 2. 通用一键安装

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

安装脚本会把项目安装到 `~/.surge-guardian-assistant`，检查 Surge 环境，并进入首次配置。

## 3. 验证是否可用

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
```

`doctor` 用来检查 Surge 命令、日志和本地配置。`tick` 是一次正式巡检；健康时只会输出：

```json
{"wakeAgent": false}
```

## 4. 极简本地怎么运行

本地模式可以用 launchd、cron 或其他调度器定时运行：

```bash
/path/to/surge-guardian-assistant/scripts/surge-guardian-assistant tick >> "$HOME/Library/Logs/surge-guardian-assistant.log" 2>&1
```

本地模式仍然支持：

1. 日志和事件检查。
2. 外部资源重试。
3. DNS 刷新。
4. 策略复测。
5. 小范围运行时临时规则。
6. 临时规则清理和状态对账。

不会自动发生：

1. 模型分析。
2. 聊天式解释。
3. Hermes memory 跨会话学习。
4. Telegram、Discord、Matrix、微信、飞书、Signal 等 Hermes 渠道通知。

## 5. 自动更新

只要安装目录还是 Git 仓库，后续就可以继续从 GitHub 获取更新。自动更新说明见 [升级](updating.zh-CN.md)。

## 6. 安全边界

不管选择哪种运行方式，守护助手都只默认执行低风险动作。自动动作只包括读取状态、更新外部资源、刷新 Surge DNS 缓存、策略复测、添加或清理运行时临时规则。

永久 profile 编辑、证书、DNS 记录、服务器、MITM、Rewrite、Scripting、Replica、reload、restart、profile 选择和策略组选择，都必须先得到用户确认。
