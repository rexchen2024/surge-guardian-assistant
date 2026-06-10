# 升级

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/updating.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/updating.zh-CN.md)

更新来自 GitHub。

安装后，正常 `tick` 巡检会每天检查一次更新。如果 GitHub 有新代码，它会自动拉取并运行 `scripts/check`。如果用户改过受 Git 管理的文件，它会跳过，不会覆盖。

## 自动更新

默认开启：

```bash
AUTO_UPDATE=1
AUTO_UPDATE_INTERVAL_SECONDS=86400
```

如果不想自动更新，在 `.env` 里关掉：

```bash
AUTO_UPDATE=0
```

## 手动命令

查看版本：

```bash
scripts/surge-guardian-assistant version
```

检查更新：

```bash
scripts/surge-guardian-assistant update --check
```

立刻升级：

```bash
scripts/surge-guardian-assistant update
```

## 说明

- `.env` 留在本地。
- state 文件留在本地。
- 更新使用 `git pull --ff-only`。
- 用户改过受 Git 管理的文件时会停止更新。
- 版本说明见 [更新日志](../CHANGELOG.zh-CN.md)。
