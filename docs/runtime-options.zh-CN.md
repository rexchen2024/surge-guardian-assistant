# 运行方式

[繁體中文](https://github.com/rexchen1803/surge-sentry/blob/main/docs/runtime-options.zh-TW.md) | [English](https://github.com/rexchen1803/surge-sentry/blob/main/docs/runtime-options.md)

Surge Sentry 的核心循环只有一套，但有三种实际运行方式。

## 1. 先选运行方式

**1. 终端**

适合只想在本机终端检查 Surge 的用户。最轻量，只运行本地脚本和 `surge-cli`。

**2. Hermes Agent**

适合常驻巡检、异常通知和后台沉淀。健康时静默，重要问题再唤醒 AI。

[查看 Hermes 安装](hermes-edition.zh-CN.md)

**3. Codex**

适合开源项目式使用：安装检查、Surge 配置诊断、异常复盘、流量监控解读和维护项目。健康巡检仍走本地脚本，避免每次检查都启动模型任务。

[查看 Codex 安装](codex-edition.zh-CN.md)

## 2. 通用一键安装

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/rexchen1803/surge-sentry/main/install.sh)" -- --setup
```

安装脚本会把项目安装到 `~/.surge-sentry`，检查 Surge 环境，并进入首次配置。

## 3. 验证是否可用

```bash
cd ~/.surge-sentry
scripts/surge-sentry doctor
scripts/surge-sentry tick
```

`doctor` 用来检查 Surge 命令、日志和本地配置。`tick` 是一次正式巡检；健康时只会输出：

```json
{"wakeAgent": false}
```

## 4. 极简本地怎么运行

本地模式可以用 launchd、cron 或其他调度器定时运行：

```bash
/path/to/surge-sentry/scripts/surge-sentry tick >> "$HOME/Library/Logs/surge-sentry.log" 2>&1
```

本地模式仍然支持：

1. 日志和事件检查。
2. 外部资源重试。
3. DNS 刷新。
4. 策略复测。
5. 小范围运行时临时规则。
6. 临时规则清理和状态对账。

不会自动发生：

1. 模型分析。
2. 聊天式解释。
3. Hermes memory 跨会话学习。
4. Telegram、Discord、Matrix、微信、飞书、Signal 等 Hermes 渠道通知。

## 5. 自动更新

只要安装目录还是 Git 仓库，后续就可以继续从 GitHub 获取更新。自动更新说明见 [升级](updating.zh-CN.md)。

## 6. 固定时段噪声窗口

Surge Sentry 不会内置任何人的个人维护窗口。它会记录 DNS、DIRECT 域名失败和代理异常是否总是在相同星期/时间段附近重复出现；当重复次数达到阈值时，会把它作为候选模式提示用户确认：这可能是路由器定时重启、运营商维护或其他固定周期事件。

确认之后，可以只在本地 `.env` 里配置：

```bash
MAINTENANCE_WINDOWS="thu 05:00-05:10:dns,direct_domain_failure,proxy"
```

这只会在指定窗口内压制指定类型的瞬时噪声。这个设置应保留在本地，不要把个人时间表提交到公开仓库。

## 7. 流量风险分析

Surge Sentry 有两种流量能力，都只读取本机 Surge 的流量统计 SQLite，不抓包、不保存请求内容。

第一种是日常低负担风险分析。适合监控某个代理策略当日是否明显超过月配额的日均预算，以及是否有本应直连的媒体域名仍在走代理。

相关配置应只放本地 `.env`：

```bash
TRAFFIC_ANALYSIS_ENABLED=1
TRAFFIC_POLICY_PATTERNS="%Monitored%,%Backup%"
TRAFFIC_MONTHLY_CAP_GB=1024
TRAFFIC_RESET_DAY=19
TRAFFIC_DIRECT_HOST_PATTERNS="*emby*,example-media.test"
TRAFFIC_DIRECT_LEAK_MIN_GB=1
```

判断逻辑：

1. 当日被监控策略流量超过 `月额度 / 当前账期天数 * TRAFFIC_DAILY_WARN_RATIO` 时提示。
2. 超过 `TRAFFIC_DAILY_CRITICAL_RATIO` 时按高风险提示。
3. 命中 `TRAFFIC_DIRECT_HOST_PATTERNS` 且超过阈值时，优先指出“可能可直连却走了代理”的浪费来源。
4. Apple TV、F1 直播等大流量不单独视为错误；只有超过预算或命中直连优先模式时才提醒。

第二种是项目式流量监控。适合你临时想知道“一场比赛/一次观影/一次下载到底花了多少流量”的场景。比如 F1 正赛、世界杯 Fox 直播、Apple TV 电影、远程同步或大文件下载。

开始前保存基线：

```bash
scripts/surge-sentry traffic start f1-race --note "Apple TV F1 正赛"
```

进行中查看：

```bash
scripts/surge-sentry traffic status f1-race
```

结束后生成最终报告并归档：

```bash
scripts/surge-sentry traffic end f1-race
```

输出会包含本阶段新增消耗、按策略汇总、Top 域名、下载/上传拆分和请求数。它的价值不是替代 Surge 的统计界面，而是把“开始、进行中、结束”的基线和差值保存下来，让你更容易看清真实场景里的流量消耗。

也可以给世界杯 Fox 或 Apple TV 单独命名：

```bash
scripts/surge-sentry traffic start world-cup-fox --note "Fox 世界杯直播"
scripts/surge-sentry traffic start apple-tv-movie --note "Apple TV 电影"
```

如需只看某些策略，可以指定 Surge 策略名匹配：

```bash
scripts/surge-sentry traffic start f1-race --policy-patterns "%US%,%Proxy%"
```

## 8. 安全边界

不管选择哪种运行方式，Surge Sentry 都只默认执行低风险动作。自动动作只包括读取状态、更新外部资源、刷新 Surge DNS 缓存、策略复测、添加或清理运行时临时规则。

永久 profile 编辑、证书、DNS 记录、服务器、MITM、Rewrite、Scripting、Replica、reload、restart、profile 选择和策略组选择，都必须先得到用户确认。
