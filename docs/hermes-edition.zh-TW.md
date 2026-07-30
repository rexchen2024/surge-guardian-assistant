# Hermes 版本

[简体中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/hermes-edition.zh-CN.md) | [English](https://github.com/rexchen1803/surge-sentry/blob/main/docs/hermes-edition.md)

Hermes Agent 是推薦用法。它適合常駐巡檢：健康時不打擾，出問題時再通知。

## 1. 最省事：複製給 Hermes

如果你已經在用 Hermes，把下面這段發給 Hermes：

```text
請從 https://github.com/rexchen1803/surge-sentry 安裝 Surge Sentry，執行 setup，檢查 Surge 環境，並顯示產生的 Hermes cron 指令。確認指令前不要建立任務；未得到我確認前不要編輯 Surge profile、憑證、DNS、伺服器、MITM、Rewrite、Scripting、Replica，也不要執行 reload 或 restart。
```

Hermes 應該做三件事：

1. 安裝專案到本機。
2. 執行 setup 和基礎檢查。
3. 把產生的 Hermes cron 指令顯示給你確認。

確認前，它不應該直接建立任務，也不應該做永久 Surge 變更。

## 2. 終端一鍵安裝

如果你想自己在終端安裝，執行：

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen1803/surge-sentry/main/install.sh)" -- --setup
```

安裝會把專案放到 `~/.surge-sentry`。setup 會查找 Surge 指令、日誌目錄、profile 和策略組；它只寫本機 `.env`，不會修改 Surge profile。

## 3. 驗證本機巡檢

```bash
cd ~/.surge-sentry
scripts/surge-sentry doctor
scripts/surge-sentry tick
```

健康輸出是：

```json
{"wakeAgent": false}
```

這代表一切正常，不需要喚醒模型。

## 4. 建立 Hermes 定時任務

安裝輸出裡會出現一條 Hermes cron 指令。先檢查三點：

1. 任務名稱是 `Surge Sentry`。
2. 目錄指向 `~/.surge-sentry`。
3. 頻率符合你的預期，推薦每分鐘一次。

確認無誤後再執行這條指令。模型分析 prompt 使用：

```text
hermes/job-prompts/sentry.md
```

## 5. 自動更新

Hermes 任務會持續執行 `tick`。只要安裝目錄是 Git 儲存庫，Surge Sentry 預設每天自動檢查一次 GitHub 更新。

關閉自動更新：在安裝目錄的 `.env` 裡寫入：

```bash
AUTO_UPDATE=0
```

## 6. 安全邊界

Hermes 可以負責排程、分析和通知，但不應該直接執行永久 Surge 變更。Surge Sentry 可以自動執行低風險動作，例如讀取狀態、更新外部資源、刷新 Surge DNS 快取、策略複測、加入或清理執行階段臨時規則。

涉及永久 profile 編輯、憑證、DNS 記錄、伺服器、MITM、Rewrite、Scripting、Replica、reload、restart、profile 選擇或策略組選擇時，先讓 Hermes 通知並等待使用者確認。

## 7. 常用指令

```bash
scripts/surge-sentry version
scripts/surge-sentry update --check
scripts/surge-sentry update
scripts/surge-sentry feedback
```
