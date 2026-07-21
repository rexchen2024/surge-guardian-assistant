# GitHub 發布檢查清單

[简体中文](https://github.com/rexchen2024/surge-sentry/blob/main/docs/github-checklist.zh-CN.md) | [English](https://github.com/rexchen2024/surge-sentry/blob/main/docs/github-checklist.md)

發布 release 或把儲存庫設為公開前，按這份清單快速檢查。

## 儲存庫

- README 在第一屏說清楚專案做什麼。
- README 連結到安裝、升級、回饋、授權條款和安全說明，但不過度擁擠。
- `README.md` 預設使用簡體中文。
- `README.zh-TW.md` 和 `README.en.md` 已存在，並且從首頁可進入。
- 安裝頁面提供簡體中文、繁體中文和英文版本，並帶語言切換連結。
- Issue 和 PR 模板預設使用清晰的簡體中文。
- FAQ 說明本專案不是 Surge profile、規則集、模組集合或代理訂閱專案。
- FAQ 覆蓋常見的 Surge 使用者誤解。
- `LICENSE`、`CONTRIBUTING.md`、`SECURITY.md` 和 `CODE_OF_CONDUCT.md` 已存在。
- Issue 模板和 PR 模板已存在。
- 如果啟用了 GitHub Actions，檢查工作流需要通過。
- release tag 指向目標提交。

## 隱私

- `.env` 已被忽略。
- 沒有提交 Surge profiles。
- 沒有提交訂閱 URL、節點憑據、請求日誌、DNS dump、event dump、真實網域、真實 IP、個人路徑或通知目標。
- 範例設定只使用範例值。
- 發布前檢查截圖和終端片段。

## 驗證

執行：

```bash
scripts/check
scripts/surge-sentry version
scripts/surge-sentry feedback --print
```

然後檢查：

```bash
git status --short
git tag --list
gh release list --repo rexchen2024/surge-sentry --limit 5
```

## 對外描述

把專案描述為 Surge Sentry，而不是 Surge profile 或代理訂閱。

承諾保持收窄：

- 健康巡檢靜默
- 安全自我修復
- Hermes 路線用於常駐巡檢、低噪音通知和背景沉澱
- Codex 路線用於安裝檢查、Surge 設定診斷、異常回顧、流量監控解讀和專案維護
- 不自動遙測
- 沒有使用者確認，不做永久 Surge 變更
