# 自治模型

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/autonomy.zh-CN.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/autonomy.md)

Surge Sentry 使用分層自治模型。

## 自動執行

- 外部資源出現錯誤時更新外部資源
- 重複 DNS 錯誤後刷新 DNS
- 升級處理前複測策略和策略組
- 針對重複 DIRECT 失敗加入窄範圍臨時執行階段規則
- 冷卻期後複查並移除臨時規則
- 抑制已恢復的單次策略失敗

## 條件執行

- 當 sentry 有足夠證據證明目標策略健康、目前策略反覆失敗時，
  後續可以加入臨時策略切換能力
- 使用者在本機設定中明確啟用的精確媒體網域 allowlist，可執行備份、檢查、reload、複驗和失敗回復閉環

## 需要確認

- 永久 profile 編輯
- `.conf` 或 `.sgmodule` 變更
- Surge 重啟、停止、reload 或 profile 切換
- 長期策略組選擇變更
- MITM、Rewrite、Scripting、Replica 或抓包變更
- 憑證、DNS 記錄、伺服器或帳號變更
- 大範圍刪除臨時規則
