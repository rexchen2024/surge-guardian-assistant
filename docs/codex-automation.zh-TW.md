# Codex 自動化說明

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-automation.zh-CN.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-automation.md)

Codex 可以作為 Surge 守護助手的分析和維護層，但不應該作為主要執行方式。

安裝步驟見 [Codex 版本](codex-edition.zh-TW.md)。

## 推薦邊界

生產守護仍然建議交給 Hermes：

- Hermes cron 執行分鐘級 `tick`。
- `{"wakeAgent": false}` 讓健康檢查跳過模型工作。
- 非靜默輸出再喚醒 Hermes 做模型分析和投遞。

Codex 自動化適合較低頻工作：

- 每日或每週儲存庫檢查
- `scripts/check` 驗證
- 隱私/脫敏審計
- 回顧非靜默異常包
- 在重複模式出現後建議程式碼或文件改進

這樣可以保持便宜路徑真的便宜。Codex cron job 很有用，但它仍然會啟動一次
Codex 任務，所以不應該替代 Hermes 的分鐘級健康閘門。

## Codex + Surge 版本

如果使用者已經依賴 Codex 自動化，並且希望把專案維護或異常分析放到 Codex 裡，
那麼 Codex + Surge 版本是可行的。

使用建議：

- 機器有 Surge，並且 Codex 能存取本機 workspace
- 使用者想做週期性專案檢查或異常回顧
- 頻率是每小時、每天或每週
- 每次計畫執行都可以接受模型分析
- 分鐘級常駐監控仍建議交給 Hermes

## 自動化 Prompt

可以用 `codex/automation-prompts/surge-guardian-review.md` 作為 Codex
workspace 自動化的起點。自動化的工作目錄指向儲存庫根目錄即可。

這個 prompt 會明確要求 Codex 把 Hermes 作為預設執行方式，並且在使用者明確確認前，
不要執行永久 Surge 變更。

## 安全規則

- 不要把原始 Surge profiles、訂閱、請求內容或私人日誌貼到 Codex prompt 裡。
- 優先使用 `scripts/check`、`doctor`、摘要 state 和非靜默異常包。
- 不要讓 Codex 自動化直接編輯 Surge profiles。
- 永久路由、DNS、憑證、伺服器、MITM、Rewrite、Scripting、Replica、reload
  和 restart 變更都必須等待使用者明確確認。
- 如果一次執行沒有可處理問題，最終回覆應該簡短，避免製造通知噪音。
