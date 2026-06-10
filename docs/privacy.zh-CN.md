# 隐私说明

[English](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/privacy.md) | [简体中文](https://github.com/rexchen2024/surge-guardian-assistant/blob/main/docs/privacy.zh-CN.md)

请把以下内容视为敏感信息：

- Surge profile 文件
- 订阅 URL
- 代理节点服务器名、端口、密码和 token
- 控制器凭据
- 请求日志、DNS dump 和原始 event dump
- 能识别私人基础设施的真实域名和 IP

发布前：

- 确保 `.env` 不进入 Git。
- 用示例值替换真实域名和 IP。
- 分享前检查截图和终端日志。
- 优先分享摘要，不要分享原始 dump。
- 每次提交前运行 `scripts/surge-guardian-assistant redact-check`。

## 反馈报告

项目不会自动上传日志、使用数据或设备信息。

用户可以主动生成一份脱敏报告：

```bash
scripts/surge-guardian-assistant feedback
```

报告默认写到本地 state 目录，权限是 `0600`。分享前请先打开看一遍。

如果想复制到 GitHub issue：

```bash
scripts/surge-guardian-assistant feedback --github-url
```

这只是生成链接，不会自动提交。

报告本身不要求真实身份。通过 GitHub 提交时，GitHub 账号是否可见由 GitHub 决定。
