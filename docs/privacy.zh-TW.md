# 隱私說明

[简体中文](https://github.com/rexchen2024/surge-sentry/blob/main/docs/privacy.zh-CN.md) | [English](https://github.com/rexchen2024/surge-sentry/blob/main/docs/privacy.md)

請把以下內容視為敏感資訊：

- Surge profile 檔案
- 訂閱 URL
- 代理節點伺服器名、連接埠、密碼和 token
- 控制器憑證
- 請求日誌、DNS dump 和原始 event dump
- 能識別私人基礎設施的真實網域和 IP

發布前：

- 確保 `.env` 不進入 Git。
- 用範例值替換真實網域和 IP。
- 分享前檢查截圖和終端日誌。
- 優先分享摘要，不要分享原始 dump。
- 每次提交前執行 `scripts/surge-sentry redact-check`。

## 回饋報告

專案不會自動上傳日誌、使用資料或裝置資訊。

使用者可以主動產生一份脫敏報告：

```bash
scripts/surge-sentry feedback
```

報告預設寫到本機 state 目錄，權限是 `0600`。分享前請先打開看一遍。

如果想複製到 GitHub issue：

```bash
scripts/surge-sentry feedback --github-url
```

這只是產生連結，不會自動提交。

報告本身不要求真實身份。透過 GitHub 提交時，GitHub 帳號是否可見由 GitHub 決定。
