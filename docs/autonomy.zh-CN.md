# 自治模型

[繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/autonomy.zh-TW.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/autonomy.md)

Surge Sentry 使用分层自治模型。

## 自动执行

- 外部资源出现错误时更新外部资源
- 重复 DNS 错误后刷新 DNS
- 升级处理前复测策略和策略组
- 针对重复 DIRECT 失败添加窄范围临时运行时规则
- 冷却期后复查并移除临时规则
- 抑制已恢复的单次策略失败

## 条件执行

- 当 sentry 有足够证据证明目标策略健康、当前策略反复失败时，
  后续可以加入临时策略切换能力
- 用户在本地配置中明确启用的精确媒体域名 allowlist，可执行备份、检查、reload、复验和失败回滚闭环

## 需要确认

- 永久 profile 编辑
- `.conf` 或 `.sgmodule` 变更
- Surge 重启、停止、reload 或 profile 切换
- 长期策略组选择变更
- MITM、Rewrite、Scripting、Replica 或抓包变更
- 证书、DNS 记录、服务器或账号变更
- 大范围删除临时规则
