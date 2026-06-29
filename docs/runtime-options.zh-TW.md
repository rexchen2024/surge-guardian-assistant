# 執行方式

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/runtime-options.zh-CN.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/runtime-options.md)

Surge Sentry 的核心循環只有一套，但有三種實際執行方式。

## 1. 先選執行方式

**1. 終端**

適合只想在本機終端檢查 Surge 的使用者。最輕量，只執行本機腳本和 `surge-cli`。

**2. Hermes Agent**

適合常駐巡檢、異常通知和背景沉澱。健康時靜默，重要問題再喚醒 AI。

[查看 Hermes 安裝](hermes-edition.zh-TW.md)

**3. Codex**

適合開源專案式使用：安裝檢查、Surge 設定診斷、異常回顧、流量監控解讀和維護專案。健康巡檢仍走本機腳本，避免每次檢查都啟動模型任務。

[查看 Codex 安裝](codex-edition.zh-TW.md)

## 2. 通用一鍵安裝

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen2024/surge-guardian-assistant/main/install.sh)" -- --setup
```

安裝腳本會把專案安裝到 `~/.surge-sentry`，檢查 Surge 環境，並進入首次設定。

## 3. 驗證是否可用

```bash
cd ~/.surge-sentry
scripts/surge-sentry doctor
scripts/surge-sentry tick
```

`doctor` 用來檢查 Surge 指令、日誌和本機設定。`tick` 是一次正式巡檢；健康時只會輸出：

```json
{"wakeAgent": false}
```

## 4. 極簡本機怎麼執行

本機模式可以用 launchd、cron 或其他排程器定時執行：

```bash
/path/to/surge-sentry/scripts/surge-sentry tick >> "$HOME/Library/Logs/surge-sentry.log" 2>&1
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

## 6. 固定時段噪音窗口

Surge Sentry 不會內建任何人的個人維護窗口。它會記錄 DNS、DIRECT 網域失敗和代理異常是否總是在相同星期/時間段附近重複出現；當重複次數達到閾值時，會把它作為候選模式提示使用者確認：這可能是路由器定時重啟、ISP 維護或其他固定週期事件。

確認之後，可以只在本機 `.env` 裡設定：

```bash
MAINTENANCE_WINDOWS="thu 05:00-05:10:dns,direct_domain_failure,proxy"
```

這只會在指定窗口內壓制指定類型的瞬時噪音。這個設定應保留在本機，不要把個人時間表提交到公開倉庫。

## 7. 流量分析和場景監控

Surge Sentry 有兩種流量能力，都只讀取本機 Surge 的流量統計 SQLite，不抓包、不保存請求內容。

第一種是日常低負擔風險分析。適合監控某個代理策略當日是否明顯超過月配額的日均預算，以及是否有本應直連的媒體網域仍在走代理。

第二種是場景式流量監控。適合你臨時想知道「一場比賽 / 一次觀影 / 一次下載到底花了多少流量」的情境。比如 F1 正賽、世界盃 Fox 直播、Apple TV 電影、遠端同步或大檔案下載。

開始前保存基線：

```bash
scripts/surge-sentry traffic start f1-race --note "Apple TV F1 正賽"
```

進行中查看：

```bash
scripts/surge-sentry traffic status f1-race
```

結束後產生最終報告並歸檔：

```bash
scripts/surge-sentry traffic end f1-race
```

輸出會包含本階段新增消耗、按策略彙總、Top 網域、下載/上傳拆分和請求數。它不是替代 Surge 的統計介面，而是把「開始、進行中、結束」的基線和差值保存下來，讓你更容易看清真實場景裡的流量消耗。

也可以給世界盃 Fox 或 Apple TV 單獨命名：

```bash
scripts/surge-sentry traffic start world-cup-fox --note "Fox 世界盃直播"
scripts/surge-sentry traffic start apple-tv-movie --note "Apple TV 電影"
```

如需只看某些策略，可以指定 Surge 策略名匹配：

```bash
scripts/surge-sentry traffic start f1-race --policy-patterns "%US%,%Proxy%"
```

## 8. 安全邊界

不管選擇哪種執行方式，Surge Sentry 都只預設執行低風險動作。自動動作只包括讀取狀態、更新外部資源、刷新 Surge DNS 快取、策略複測、加入或清理執行階段臨時規則。

永久 profile 編輯、憑證、DNS 記錄、伺服器、MITM、Rewrite、Scripting、Replica、reload、restart、profile 選擇和策略組選擇，都必須先得到使用者確認。
