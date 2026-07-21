# 升级

[繁體中文](https://github.com/rexchen2024/surge-sentry/blob/main/docs/updating.zh-TW.md) | [English](https://github.com/rexchen2024/surge-sentry/blob/main/docs/updating.md)

更新来自 GitHub。

自动更新不是后台偷偷运行。它需要 Hermes、Codex 或系统任务继续执行 `tick`。

## 默认行为

```bash
AUTO_UPDATE=1
AUTO_UPDATE_INTERVAL_SECONDS=86400
```

也就是：每天最多检查一次。

如果有新代码，会自动拉取并运行 `scripts/check`。

如果用户改过受 Git 管理的文件，会跳过更新，不会覆盖。

## 手动命令

查看版本：

```bash
scripts/surge-sentry version
```

只检查：

```bash
scripts/surge-sentry update --check
```

立刻升级：

```bash
scripts/surge-sentry update
```

关闭自动更新：在安装目录的 `.env` 里写入：

```bash
AUTO_UPDATE=0
```

## 说明

- `.env` 留在本地。
- state 文件留在本地。
- 更新使用 `git pull --ff-only`。
- 安装目录不是 Git 仓库时不能自动更新。
- 版本说明见 [更新日志](../CHANGELOG.zh-CN.md)。
