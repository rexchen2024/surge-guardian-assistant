# 快速上手

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/onboarding.zh-CN.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/onboarding.md)

本指南假設你已經安裝 Surge for macOS。Hermes 是推薦的定時模型輔助執行方式，
但本機 `doctor` 和 `tick` 指令不依賴 Hermes，也可以單獨執行。

## 1. 取得專案

```bash
git clone https://github.com/rexchen2024/surge-guardian-assistant.git ~/.surge-guardian-assistant
cd ~/.surge-guardian-assistant
```

## 2. 執行 Setup

```bash
scripts/surge-guardian-assistant setup --print-hermes-command
```

Setup 會自動發現：

- `surge-cli`
- Surge 日誌目錄
- profile 候選項
- 執行階段策略候選項

它會在儲存庫根目錄寫入 `.env`。它不會編輯 Surge profiles。

## 3. 本機驗證

```bash
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
```

健康狀態下的 `tick` 輸出是：

```json
{"wakeAgent": false}
```

## 4. 選擇執行方式

如果使用推薦的 Hermes 工作流，檢查 setup 印出的指令，然後執行它。
推薦排程頻率是每分鐘一次。

Hermes 會根據使用者現有的 Hermes 設定處理訊息投遞。如果還沒有設定投遞目標，
請先設定一個 Hermes 支援的平台。Guardian 不要求必須使用 Telegram。

如果這台機器只有 Surge、沒有 Hermes，可以用 launchd 或其他本機排程器執行
`tick`，然後只查看不等於 `{"wakeAgent": false}` 的輸出。詳見
[執行方式](runtime-options.zh-TW.md)。

## 5. 日常使用

- 使用 `doctor` 手動查看脫敏後的狀態摘要。
- 使用 `update --check` 檢查 GitHub 是否有新版本。
- 使用 `feedback` 產生脫敏回饋報告。
- 提交變更前執行 `redact-check` 或 `scripts/check`。
- 不要把 `.env`、日誌、state、profiles 或真實基礎設施標識提交到 Git。
