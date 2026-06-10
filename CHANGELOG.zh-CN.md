# 更新日志

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.zh-CN.md)

## 0.1.0

首个完整版本。

- Surge 日志和事件巡检。
- 健康时静默输出 `{"wakeAgent": false}`。
- 外部资源失败自动重试。
- DNS 连续异常自动刷新。
- 通知前复测策略状态。
- 反复 DIRECT 失败时添加小范围临时规则。
- Hermes 版本：适合常驻巡检和通知。
- Codex 版本：适合低频检查、异常分析和项目维护。
- 一键安装脚本。
- GitHub 自动更新。
- `version`、`update`、`doctor`、`feedback` 和 `redact-check` 命令。
- 本地 `.env` 和 state 文件私有权限。
- 隐私扫描和脱敏反馈报告。
- GitHub Actions 自动检查。
- License、Contributing、Security、Code of Conduct、Issue 模板和 PR 模板。
- 快速上手、故障排查和发布检查清单。
