# 升级

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/updating.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/updating.zh-CN.md)

Surge 守护助手以 Git checkout 的方式安装。GitHub 就是更新源。

这样升级逻辑很简单：

- 用户保留同一份本地 `.env`
- 代码更新来自 `main`
- 本地私有 state 不进入 Git
- 更新命令会先校验新代码，再报告成功

## 查看已安装版本

```bash
scripts/surge-guardian-assistant version
```

## 检查是否有更新

```bash
scripts/surge-guardian-assistant update --check
```

## 执行升级

```bash
scripts/surge-guardian-assistant update
```

更新命令会执行：

1. `git fetch --prune origin`
2. 本地改动安全检查
3. `git pull --ff-only`
4. `scripts/check`

如果用户修改过受 Git 管理的文件，命令会停止，避免覆盖本地改动。先 commit、
stash 或 reset 这些本地改动后再升级。

## 更新日志

见 [更新日志](../CHANGELOG.zh-CN.md)。
