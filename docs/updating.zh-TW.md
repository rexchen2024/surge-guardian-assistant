# 升級

[简体中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/updating.zh-CN.md) | [English](https://github.com/rexchen1803/surge-sentry/blob/main/docs/updating.md)

更新來自 GitHub。

自動更新不是背景偷偷執行。它需要 Hermes、Codex 或系統任務繼續執行 `tick`。

## 預設行為

```bash
AUTO_UPDATE=1
AUTO_UPDATE_INTERVAL_SECONDS=86400
```

也就是：每天最多檢查一次。

如果有新程式碼，會自動拉取並執行 `scripts/check`。

如果使用者改過受 Git 管理的檔案，會跳過更新，不會覆蓋。

## 手動指令

查看版本：

```bash
scripts/surge-sentry version
```

只檢查：

```bash
scripts/surge-sentry update --check
```

立刻升級：

```bash
scripts/surge-sentry update
```

關閉自動更新：在安裝目錄的 `.env` 裡寫入：

```bash
AUTO_UPDATE=0
```

## 說明

- `.env` 留在本機。
- state 檔案留在本機。
- 更新使用 `git pull --ff-only`。
- 安裝目錄不是 Git 儲存庫時不能自動更新。
- 版本說明見 [更新日誌](../CHANGELOG.zh-CN.md)。
