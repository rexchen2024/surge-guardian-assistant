# 執行方式

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/runtime-options.zh-CN.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/runtime-options.md)

Surge 守護助手的核心循環只有一套，但有三種實際執行方式。

## 1. 先選執行方式

**1. 終端**

適合只想在本機終端檢查 Surge 的使用者。最輕量，只執行本機腳本和 `surge-cli`。

**2. 🌟推薦 - Hermes Agent**

適合常駐巡檢、異常通知和持續學習。健康時靜默，重要問題再喚醒 AI。

[查看 Hermes 安裝](hermes-edition.zh-TW.md)

**3. Codex**

適合低頻檢查儲存庫、回顧異常和維護專案。不建議做每分鐘巡檢。

[查看 Codex 安裝](codex-edition.zh-TW.md)

## 2. 通用一鍵安裝

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

安裝腳本會把專案安裝到 `~/.surge-guardian-assistant`，檢查 Surge 環境，並進入首次設定。

## 3. 驗證是否可用

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant doctor
scripts/surge-guardian-assistant tick
```

`doctor` 用來檢查 Surge 指令、日誌和本機設定。`tick` 是一次正式巡檢；健康時只會輸出：

```json
{"wakeAgent": false}
```

## 4. 極簡本機怎麼執行

本機模式可以用 launchd、cron 或其他排程器定時執行：

```bash
/path/to/surge-guardian-assistant/scripts/surge-guardian-assistant tick >> "$HOME/Library/Logs/surge-guardian-assistant.log" 2>&1
```

本機模式仍然支援：

1. 日誌和事件檢查。
2. 外部資源重試。
3. DNS 刷新。
4. 策略複測。
5. 小範圍執行階段臨時規則。
6. 臨時規則清理和狀態對帳。

不會自動發生：

1. 模型分析。
2. 聊天式解釋。
3. Hermes memory 跨會話學習。
4. Telegram、Discord、Matrix、微信、飛書、Signal 等 Hermes 渠道通知。

## 5. 自動更新

只要安裝目錄還是 Git 儲存庫，後續就可以繼續從 GitHub 取得更新。自動更新說明見 [升級](updating.zh-TW.md)。

## 6. 安全邊界

不管選擇哪種執行方式，守護助手都只預設執行低風險動作。自動動作只包括讀取狀態、更新外部資源、刷新 Surge DNS 快取、策略複測、加入或清理執行階段臨時規則。

永久 profile 編輯、憑證、DNS 記錄、伺服器、MITM、Rewrite、Scripting、Replica、reload、restart、profile 選擇和策略組選擇，都必須先得到使用者確認。
