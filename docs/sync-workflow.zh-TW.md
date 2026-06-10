# 同步流程

[简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/sync-workflow.zh-CN.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/sync-workflow.md)

當本機 Surge 腳本繼續演進，並且 GitHub 專案需要吸收這些能力時，使用這個流程。

1. 只把可複用行為複製到 `guardian/`。
2. 將真實網域、IP、路徑、策略名稱和使用者標識替換為設定項。
3. 為該行為新增或更新測試。
4. 執行：

```bash
scripts/check
```

5. 只有在 `redact-check` 通過後才提交。
