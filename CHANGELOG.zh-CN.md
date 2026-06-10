# 更新日志

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/CHANGELOG.zh-CN.md)

## 0.3.0

- 正常 `tick` 巡检时默认自动检查更新。
- 新增 `AUTO_UPDATE` 和 `AUTO_UPDATE_INTERVAL_SECONDS`。
- 升级保持安全：用户改过受 Git 管理的文件时会停止更新。
- 简化 README 和升级说明。

## 0.2.0

- 对外项目名改为 Surge 守护助手。
- 新增 Hermes 版本和 Codex 版本文档。
- 只保留 `scripts/surge-guardian-assistant` 作为公开 CLI 入口。
- 新增 `version` 和 `update` 命令。
- 新增 `install.sh`，支持基于 Git 的一条命令安装。
- 本地 `.env` 和 state 文件保持 `0600` 私有权限。

## 0.1.0

- 初始 Surge 日志和事件守护循环。
- 面向 Hermes cron 的健康输出 `{"wakeAgent": false}`。
- 支持外部资源重试、DNS 刷新、策略复测、临时规则处理、隐私扫描和中英文文档。
