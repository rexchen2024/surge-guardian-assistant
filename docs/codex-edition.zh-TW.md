# Codex 版本

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-edition.zh-CN.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/codex-edition.md)

Codex 版本適合低頻檢查、分析異常包、維護儲存庫。不建議用它做每分鐘巡檢。

## 1. 最省事：複製給 Codex

如果你已經在用 Codex，把下面這段發給 Codex：

```text
請把 https://github.com/rexchen2024/surge-guardian-assistant 安裝到本機，作為 Surge 守護助手專案使用。請執行 doctor 和 scripts/check，然後根據 codex/automation-prompts/surge-guardian-review.md 建立或建議一個安全的 Codex 自動化。不要在未確認前編輯 Surge profile、憑證、DNS、伺服器、MITM、Rewrite、Scripting、Replica，也不要執行 reload 或 restart。
```

Codex 應該做三件事：

1. 安裝專案到本機。
2. 執行基礎檢查。
3. 給出低頻自動化建議，或幫你建立 Codex 自動化。

## 2. 終端一鍵安裝

如果你想自己在終端安裝，執行：

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

安裝腳本會把專案放到 `~/.surge-guardian-assistant`。

## 3. 驗證專案可用

```bash
cd ~/.surge-guardian-assistant
scripts/surge-guardian-assistant doctor
scripts/check
```

`doctor` 檢查本機 Surge 環境。`scripts/check` 檢查專案測試、基礎安全和脫敏規則。

## 4. 建立 Codex 自動化

讓 Codex 使用這個工作目錄：

```text
~/.surge-guardian-assistant
```

Prompt 範本：

```text
codex/automation-prompts/surge-guardian-review.md
```

推薦頻率：

1. 每天檢查儲存庫狀態和隱私風險。
2. 每週複查文件和測試。
3. 出現非靜默異常包時再讓 Codex 分析。

## 5. 自動更新

Codex 自動化可以每天執行：

```bash
scripts/surge-guardian-assistant update --check
scripts/check
```

如果希望它直接升級，可以讓自動化執行：

```bash
scripts/surge-guardian-assistant update
```

儲存庫有本機改動時，更新會跳過，不會覆蓋。

## 6. 安全邊界

Codex 不應該直接編輯 Surge profiles、憑證、DNS 記錄、伺服器、MITM、Rewrite、Scripting、Replica、profile 選擇、策略組選擇、reload 或 restart。

如果這些動作看起來有必要，先問使用者。
