# 故障排查

[简体中文](https://github.com/rexchen2024/surge-sentry/blob/main/docs/troubleshooting.zh-CN.md) | [English](https://github.com/rexchen2024/surge-sentry/blob/main/docs/troubleshooting.md)

先執行：

```bash
cd ~/.surge-sentry
scripts/surge-sentry doctor
```

## `missing .env`

還沒有完成 setup。

```bash
scripts/surge-sentry setup --print-hermes-command
```

## `surge-cli: not found`

確認 Surge for macOS 已安裝，並且 `surge-cli` 路徑正確。

預設路徑：

```text
/Applications/Surge.app/Contents/Applications/surge-cli
```

如果你的路徑不同，重新執行 setup。

## `expected policies: missing`

需要選擇你希望Surge Sentry 複測的策略組。

重新執行 setup，或在 `.env` 中設定：

```bash
EXPECTED_POLICIES=Proxy,ProxyMedia
```

這裡的名字要和 Surge 裡實際的策略組名稱一致。

## 一直輸出 `{"wakeAgent": false}`

這是正常情況，代表沒有需要喚醒 Hermes 或 Codex 的異常。

## 自動更新沒有發生

檢查三件事：

- 安裝目錄必須是 Git 儲存庫。
- Hermes、Codex 或系統任務必須持續執行 `tick`。
- `.env` 中不能設定 `AUTO_UPDATE=0`。

手動檢查：

```bash
scripts/surge-sentry update --check
```

## 更新被跳過

如果你改過受 Git 管理的檔案，自動更新會跳過，避免覆蓋本機修改。

查看狀態：

```bash
git status --short
```

## 需要提交問題

產生脫敏報告：

```bash
scripts/surge-sentry feedback --github-url
```

提交前請先檢查報告內容，不要貼原始 Surge profile、訂閱 URL、節點憑據、請求日誌、真實網域或真實 IP。
