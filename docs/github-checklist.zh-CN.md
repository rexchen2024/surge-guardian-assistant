# GitHub 发布检查清单

[繁體中文](https://github.com/rexchen2024/surge-sentry/blob/main/docs/github-checklist.zh-TW.md) | [English](https://github.com/rexchen2024/surge-sentry/blob/main/docs/github-checklist.md)

发布 release 或把仓库设为公开前，按这份清单快速检查。

## 仓库

- README 在第一屏说清楚项目做什么。
- README 链接到安装、升级、反馈、许可证和安全说明，但不过度拥挤。
- `README.md` 默认使用简体中文。
- `README.zh-TW.md` 和 `README.en.md` 已存在，并且从主页可进入。
- 安装页面提供简体中文、繁体中文和英文版本，并带语言切换链接。
- Issue 和 PR 模板默认使用清晰的简体中文。
- FAQ 说明本项目不是 Surge profile、规则集、模块集合或代理订阅项目。
- FAQ 覆盖常见的 Surge 用户误解。
- `LICENSE`、`CONTRIBUTING.md`、`SECURITY.md` 和 `CODE_OF_CONDUCT.md` 已存在。
- Issue 模板和 PR 模板已存在。
- 如果启用了 GitHub Actions，检查工作流需要通过。
- release tag 指向目标提交。

## 隐私

- `.env` 已被忽略。
- 没有提交 Surge profiles。
- 没有提交订阅 URL、节点凭据、请求日志、DNS dump、event dump、真实域名、真实 IP、个人路径或通知目标。
- 示例配置只使用示例值。
- 发布前检查截图和终端片段。

## 验证

运行：

```bash
scripts/check
scripts/surge-sentry version
scripts/surge-sentry feedback --print
```

然后检查：

```bash
git status --short
git tag --list
gh release list --repo rexchen2024/surge-sentry --limit 5
```

## 对外描述

把项目描述为 Surge Sentry，而不是 Surge profile 或代理订阅。

承诺保持收窄：

- 健康巡检静默
- 安全自愈
- Hermes 路线用于常驻巡检、低噪声通知和后台沉淀
- Codex 路线用于安装检查、Surge 配置诊断、异常复盘、流量监控解读和项目维护
- 不自动遥测
- 没有用户确认，不做永久 Surge 变更
