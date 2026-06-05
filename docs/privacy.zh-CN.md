# 隐私说明

[English](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/privacy.md) | [简体中文](https://github.com/rexchen2024/surge-hermes-guardian/blob/main/docs/privacy.zh-CN.md)

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
- 每次提交前运行 `scripts/surge-hermes-guardian redact-check`。

