# 常见问题

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/faq.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/faq.zh-CN.md)

## 这是 Surge 配置仓库吗？

不是。

它不提供 Surge profile、规则集、模块、节点或订阅链接。它是在你已有 Surge 配置的基础上，负责巡检、自愈和异常反馈。

## 会自动改我的 Surge 配置吗？

不会自动修改永久 profile。

它只会执行低风险运行时动作，例如外部资源重试、DNS 刷新、策略复测和小范围临时规则。永久 profile 修改、证书、DNS、MITM、Rewrite、Scripting、重载或重启都需要用户确认。

## 没有 Hermes 能用吗？

可以运行 `doctor` 和 `tick`，也可以用本地调度器定时执行。

但推荐使用 Hermes 版本，因为 Hermes 更适合做常驻调度、模型分析和消息通知。

## Codex 版本适合做什么？

适合低频检查仓库、复盘异常包、更新文档和持续改进项目。

不建议用 Codex 做每分钟健康巡检。健康路径应该尽量轻，不需要每次都启动模型任务。

## 自动更新会覆盖我的修改吗？

不会。

如果用户改过受 Git 管理的文件，自动更新会跳过。你可以手动运行：

```bash
scripts/surge-guardian-assistant update --check
```

## 会上传日志或使用数据吗？

不会自动上传。

反馈报告需要用户主动生成，并且可以先在本地检查：

```bash
scripts/surge-guardian-assistant feedback --print
```
