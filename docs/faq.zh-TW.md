# 常見問題

[简体中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/faq.zh-CN.md) | [English](https://github.com/rexchen1803/surge-sentry/blob/main/docs/faq.md)

## 這是 Surge 設定儲存庫嗎？

不是。

它不提供 Surge profile、規則集、模組、節點或訂閱連結。它是在你已有 Surge 設定的基礎上，負責巡檢、自我修復和異常回饋。

## 會自動改我的 Surge 設定嗎？

不會自動修改永久 profile。

它只會執行低風險執行階段動作，例如外部資源重試、DNS 刷新、策略複測和小範圍臨時規則。永久 profile 修改、憑證、DNS、MITM、Rewrite、Scripting、重載或重啟都需要使用者確認。

## 沒有 Hermes 能用嗎？

可以執行 `doctor` 和 `tick`，也可以用本機排程器定時執行。

可以。Hermes 適合常駐排程和訊息通知；Codex 適合開源專案式的檢查、診斷、回顧和維護。你可以按自己的工作流選擇其中一種。

## Codex 適合做什麼？

適合安裝檢查、Surge 設定診斷、回顧異常包、解讀流量監控結果、更新文件和持續改進專案。

不需要讓 Codex 每分鐘做健康巡檢。健康路徑應該盡量輕，由本機腳本執行；需要解釋、判斷或改進時再交給 Codex。

## 自動更新會覆蓋我的修改嗎？

不會。

如果使用者改過受 Git 管理的檔案，自動更新會跳過。你可以手動執行：

```bash
scripts/surge-sentry update --check
```

## 會上傳日誌或使用資料嗎？

不會自動上傳。

回饋報告需要使用者主動產生，並且可以先在本機檢查：

```bash
scripts/surge-sentry feedback --print
```
