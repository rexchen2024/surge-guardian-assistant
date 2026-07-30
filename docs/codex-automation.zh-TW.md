# Codex 自動化說明

[简体中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/codex-automation.zh-CN.md) | [English](https://github.com/rexchen1803/surge-sentry/blob/main/docs/codex-automation.md)

Codex 可以作為 Surge Sentry 的獨立使用路線：負責安裝、檢查、解釋、回顧和維護。健康巡檢仍由本機腳本完成，Codex 在需要判斷和改進時介入。

安裝步驟見 [Codex 版本](codex-edition.zh-TW.md)。

## 推薦邊界

如果你選擇 Hermes 路線：

- Hermes cron 執行分鐘級 `tick`。
- `{"wakeAgent": false}` 讓健康檢查跳過模型工作。
- 非靜默輸出再喚醒 Hermes 做模型分析和投遞。

如果你選擇 Codex 路線：

- 每日或每週儲存庫檢查
- `scripts/check` 驗證
- 隱私/脫敏審計
- 回顧非靜默異常包
- 解釋 F1、世界盃 Fox、Apple TV 等流量監控結果
- 診斷 Surge 設定風險並提出改動方案
- 在重複模式出現後建議程式碼或文件改進

這樣可以保持健康路徑足夠輕，同時讓 Codex 做更擅長的判斷、解釋和專案維護。

## Codex + Surge 版本

如果使用者已經依賴 Codex 自動化，或者希望用開源專案和本機 workspace 管理 Surge Sentry，那麼 Codex + Surge 版本是可行的。

使用建議：

- 機器有 Surge，並且 Codex 能存取本機 workspace
- 使用者想做週期性專案檢查或異常回顧
- 頻率是每小時、每天或每週
- 每次計畫執行都可以接受模型分析
- 分鐘級健康檢查仍由 `scripts/surge-sentry tick` 這類本機腳本承擔

## 自動化 Prompt

可以用 `codex/automation-prompts/surge-sentry-review.md` 作為 Codex
workspace 自動化的起點。自動化的工作目錄指向儲存庫根目錄即可。

這個 prompt 會明確要求 Codex 保持 Surge 設定安全邊界，並且在使用者明確確認前，不要執行永久 Surge 變更。

## 安全規則

- 不要把原始 Surge profiles、訂閱、請求內容或私人日誌貼到 Codex prompt 裡。
- 優先使用 `scripts/check`、`doctor`、摘要 state 和非靜默異常包。
- 不要讓 Codex 自動化直接編輯 Surge profiles。
- 永久路由、DNS、憑證、伺服器、MITM、Rewrite、Scripting、Replica、reload
  和 restart 變更都必須等待使用者明確確認。
- 如果一次執行沒有可處理問題，最終回覆應該簡短，避免製造通知噪音。
