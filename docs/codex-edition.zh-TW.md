# Codex 版本

[简体中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/codex-edition.zh-CN.md) | [English](https://github.com/rexchen1803/surge-sentry/blob/main/docs/codex-edition.md)

Codex 是 Surge Sentry 面向開源使用者和本機工作區的重要客戶端。它適合安裝檢查、Surge 設定診斷、異常回顧、流量監控結果解讀、隱私檢查、文件維護和安全改動建議。

它不需要替代每分鐘健康閘門。健康路徑仍應盡量輕，交給本機腳本或 Hermes 更合適；Codex 更適合在需要判斷、解釋、整理和改進時介入。

## 1. 最省事：複製給 Codex

如果你已經在用 Codex，把下面這段發給 Codex：

```text
請把 https://github.com/rexchen1803/surge-sentry 安裝到本機，作為 Surge Sentry 專案使用。請執行 doctor 和 scripts/check，然後根據 codex/automation-prompts/surge-sentry-review.md 建立或建議一個安全的 Codex 自動化。不要在未確認前編輯 Surge profile、憑證、DNS、伺服器、MITM、Rewrite、Scripting、Replica，也不要執行 reload 或 restart。
```

Codex 應該做四件事：

1. 安裝專案到本機。
2. 執行基礎檢查。
3. 檢查 Surge Sentry 的本機設定、隱私邊界和執行文件。
4. 給出 Codex 自動化建議，或幫你建立安全的 Codex 自動化。

## 2. 終端一鍵安裝

如果你想自己在終端安裝，執行：

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen1803/surge-sentry/main/install.sh)" -- --setup
```

安裝腳本會把專案放到 `~/.surge-sentry`。

## 3. 驗證專案可用

```bash
cd ~/.surge-sentry
scripts/surge-sentry doctor
scripts/check
```

`doctor` 檢查本機 Surge 環境。`scripts/check` 檢查專案測試、基礎安全和脫敏規則。

## 4. 建立 Codex 自動化

讓 Codex 使用這個工作目錄：

```text
~/.surge-sentry
```

Prompt 範本：

```text
codex/automation-prompts/surge-sentry-review.md
```

推薦用途：

1. 每天檢查儲存庫狀態和隱私風險。
2. 每週複查文件、測試和設定範例。
3. 出現非靜默異常包後，讓 Codex 判斷是臨時波動、已處理問題還是需要使用者確認。
4. 對 F1、世界盃 Fox、Apple TV 等流量監控結果做解釋和回顧。
5. 在需要調整 Surge 設定時，先讓 Codex 給出方案和風險，不直接改永久 profile。

## 5. 自動更新

Codex 自動化可以每天執行：

```bash
scripts/surge-sentry update --check
scripts/check
```

如果希望它直接升級，可以讓自動化執行：

```bash
scripts/surge-sentry update
```

儲存庫有本機改動時，更新會跳過，不會覆蓋。

## 6. 安全邊界

Codex 不應該直接編輯 Surge profiles、憑證、DNS 記錄、伺服器、MITM、Rewrite、Scripting、Replica、profile 選擇、策略組選擇、reload 或 restart。

如果這些動作看起來有必要，先問使用者。
