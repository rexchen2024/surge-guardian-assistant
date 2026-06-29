# 常见问题

[繁體中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/faq.zh-TW.md) | [English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/faq.md)

## 这是 Surge 配置仓库吗？

不是。

它不提供 Surge profile、规则集、模块、节点或订阅链接。它是在你已有 Surge 配置的基础上，负责巡检、自愈和异常反馈。

## 会自动改我的 Surge 配置吗？

不会自动修改永久 profile。

它只会执行低风险运行时动作，例如外部资源重试、DNS 刷新、策略复测和小范围临时规则。永久 profile 修改、证书、DNS、MITM、Rewrite、Scripting、重载或重启都需要用户确认。

## 没有 Hermes 能用吗？

可以运行 `doctor` 和 `tick`，也可以用本地调度器定时执行。

可以。Hermes 适合常驻调度和消息通知；Codex 适合开源项目式的检查、诊断、复盘和维护。你可以按自己的工作流选择其中一种。

## Codex 版本适合做什么？

适合安装检查、Surge 配置诊断、复盘异常包、解读流量监控结果、更新文档和持续改进项目。

不需要让 Codex 每分钟做健康巡检。健康路径应该尽量轻，由本地脚本执行；需要解释、判断或改进时再交给 Codex。

## 自动更新会覆盖我的修改吗？

不会。

如果用户改过受 Git 管理的文件，自动更新会跳过。你可以手动运行：

```bash
scripts/surge-sentry update --check
```

## 会上传日志或使用数据吗？

不会自动上传。

反馈报告需要用户主动生成，并且可以先在本地检查：

```bash
scripts/surge-sentry feedback --print
```
