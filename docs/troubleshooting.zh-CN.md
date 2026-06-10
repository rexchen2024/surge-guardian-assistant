# 故障排查

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/troubleshooting.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/troubleshooting.zh-CN.md)

先运行：

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant doctor
```

## `missing .env`

还没有完成 setup。

```bash
scripts/surge-guardian-assistant setup --print-hermes-command
```

## `surge-cli: not found`

确认 Surge for macOS 已安装，并且 `surge-cli` 路径正确。

默认路径：

```text
/Applications/Surge.app/Contents/Applications/surge-cli
```

如果你的路径不同，重新运行 setup。

## `expected policies: missing`

需要选择你希望守护助手复测的策略组。

重新运行 setup，或在 `.env` 中设置：

```bash
EXPECTED_POLICIES=Proxy,ProxyMedia
```

这里的名字要和 Surge 里实际的策略组名称一致。

## 一直输出 `{"wakeAgent": false}`

这是正常情况，代表没有需要唤醒 Hermes 或 Codex 的异常。

## 自动更新没有发生

检查三件事：

- 安装目录必须是 Git 仓库。
- Hermes、Codex 或系统任务必须持续运行 `tick`。
- `.env` 中不能设置 `AUTO_UPDATE=0`。

手动检查：

```bash
scripts/surge-guardian-assistant update --check
```

## 更新被跳过

如果你改过受 Git 管理的文件，自动更新会跳过，避免覆盖本地修改。

查看状态：

```bash
git status --short
```

## 需要提交问题

生成脱敏报告：

```bash
scripts/surge-guardian-assistant feedback --github-url
```

提交前请先检查报告内容，不要贴原始 Surge profile、订阅 URL、节点凭据、请求日志、真实域名或真实 IP。
