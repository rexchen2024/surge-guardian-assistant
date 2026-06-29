# 更新日誌

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.zh-CN.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.md)

## 0.2.0

- 加入本機可設定的固定維護窗口，用於壓制 DNS、DIRECT 網域失敗和代理瞬時噪音；預設不啟用任何個人窗口。
- 偵測相同星期/時間段反覆出現的噪音，並先作為可能的路由器、ISP 或上游維護模式提示使用者確認，再決定是否設定靜默。
- 按 key 合併重複的壓制記錄，讓本機狀態保留計數，但不堆積重複條目。
- 記錄更嚴格的 Hermes 投遞契約：只有最終回覆精確等於 `[SILENT]` 才靜默；「說明 + [SILENT]」會正常投遞。
- 為 live Hermes 裡的高頻 Surge Sentry 靜默輸出加入 24 小時保留策略。
- 強化 Codex 路線說明：Codex 可作為開源使用者的獨立使用客戶端，用於安裝檢查、Surge 設定診斷、異常回顧、流量監控解讀和安全改動建議。
- 新增專案式流量監控指令，支援 F1、世界盃 Fox、Apple TV 等具體場景的開始、進行中和結束流量報告。
- 驗證記錄：倉庫 `scripts/check` 通過，live 腳本語法檢查通過，臨時 HOME 煙測返回 `{"wakeAgent": false}`，Hermes cron 調度器測試通過。

## 0.1.1

- 將 CloudKit 和 Microsoft 主機視為保守 DIRECT 流量，避免守衛為這些系統服務加入臨時代理規則。
- 記錄 Unknown VIF virtual IP 和 DIRECT IP 連線失敗這類背景噪音，但不因此喚醒 Hermes。
- 收緊 Hermes 提示詞，已處理的輕微事件必須只回傳 `[SILENT]`。

## 0.1.0

首個完整版本。

- 面向 Surge 日誌、事件、策略和外部資源做靜默巡檢。
- 健康時只輸出 `{"wakeAgent": false}`，盡量不喚醒 AI、不製造通知。
- 基於 Surge 官方執行階段能力和 `surge-cli` 做執行階段檢查和低風險自我修復。
- 外部資源失敗自動重試，DNS 連續異常自動刷新 Surge DNS 快取。
- 通知前複測策略狀態，減少臨時波動帶來的誤報。
- 反覆 DIRECT 失敗時加入小範圍執行階段臨時規則，並定期清理。
- Hermes 版本支援常駐巡檢、異常通知、記憶沉澱和必要時 AI 分析。
- Codex 版本支援安裝檢查、設定診斷、異常回顧和專案維護。
- 提供一鍵安裝、首次設定、自動更新和手動更新指令。
- 提供 `version`、`update`、`doctor`、`feedback` 和 `redact-check` 指令。
- 本機 `.env` 和 state 檔案使用私有權限，不自動上傳日誌或使用資料。
- 回饋報告預設脫敏，提交前需要使用者自行檢查。
- 永久 profile 編輯、憑證、DNS 記錄、伺服器、MITM、Rewrite、Scripting、Replica、reload、restart、profile 選擇和策略組選擇都需要使用者確認。
