# 更新日誌

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.zh-CN.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.md)

## 0.1.0

首個完整版本。

- 面向 Surge 日誌、事件、策略和外部資源做靜默巡檢。
- 健康時只輸出 `{"wakeAgent": false}`，盡量不喚醒 AI、不製造通知。
- 基於 Surge 官方執行階段能力和 `surge-cli` 做執行階段檢查和低風險自我修復。
- 外部資源失敗自動重試，DNS 連續異常自動刷新 Surge DNS 快取。
- 通知前複測策略狀態，減少臨時波動帶來的誤報。
- 反覆 DIRECT 失敗時加入小範圍執行階段臨時規則，並定期清理。
- Hermes 版本支援常駐巡檢、異常通知、記憶沉澱和必要時 AI 分析。
- Codex 版本支援低頻儲存庫檢查、異常回顧和專案維護。
- 提供一鍵安裝、首次設定、自動更新和手動更新指令。
- 提供 `version`、`update`、`doctor`、`feedback` 和 `redact-check` 指令。
- 本機 `.env` 和 state 檔案使用私有權限，不自動上傳日誌或使用資料。
- 回饋報告預設脫敏，提交前需要使用者自行檢查。
- 永久 profile 編輯、憑證、DNS 記錄、伺服器、MITM、Rewrite、Scripting、Replica、reload、restart、profile 選擇和策略組選擇都需要使用者確認。
- 預設簡體中文首頁，並提供繁體中文和英文入口。
- 安裝相關文件提供簡體中文、繁體中文和英文版本，並帶語言切換連結。
