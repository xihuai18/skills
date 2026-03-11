# Parallel and Session Guide for playwright-cli

## 适用场景

这份说明专门给这些场景用：

- 多个 subagent 同时跑网页任务
- 多个 OpenCode / Codex / Claude Code session 共用一台机器
- 一个协调器把网页任务拆给多个 worker
- 需要长期保留登录态或做文件式交接

## 最小安全模型

默认先满足这 4 条：

1. 一个 worker 一个 session
2. 一个 worker 一个 profile 目录
3. 一个 worker 一个 artifact / download 目录
4. 只有 session owner 才负责关闭自己的 session

如果做不到这 4 条，就很容易出现状态串线、登录态互相污染、截图写乱、错误清理掉别人的浏览器。

## 命名与目录约定

```text
session   = pw-<tool>-<run_id>-<agent_id>
root      = ./tmp/playwright/<run_id>/<agent_id>
profile   = <root>/profile
artifacts = <root>/artifacts
downloads = <root>/downloads
state     = <root>/state.json
```

推荐目录树：

```text
tmp/
  playwright/
    run42/
      a1/
        profile/
        artifacts/
        downloads/
        state.json
      a2/
        profile/
        artifacts/
        downloads/
        state.json
```

## 协调器最小流程

协调器至少要负责：

1. 分配 `run_id` 和 `agent_id`
2. 为每个 worker 生成 `session/profile/artifacts/downloads/state`
3. 明确谁负责 cleanup
4. 明确交接只靠文件、URL、日志，不靠 live session

如果不想手工拼这些字段，可以直接生成：

```bash
python playwright-cli/scripts/parallel_run_manifest.py --help
```

给 worker 的最小输入应包含：

```json
{
  "run_id": "run42",
  "agent_id": "a1",
  "session": "pw-<tool>-run42-a1",
  "profile_dir": "./tmp/playwright/run42/a1/profile",
  "artifact_dir": "./tmp/playwright/run42/a1/artifacts",
  "download_dir": "./tmp/playwright/run42/a1/downloads",
  "state_file": "./tmp/playwright/run42/a1/state.json"
}
```

## Session 与状态管理

这些情况不要继续依赖默认 session：

- 同时操作两个网站或两个账号
- 一个任务要长期保留登录态
- 你需要让用户稍后继续接管同一个浏览器上下文
- 同一台机器上有多个 subagent 或多个 coding session 同时跑

状态保存建议：

- 需要跨浏览器重启复用状态：`--persistent`
- 需要显式导出登录态：`state-save auth.json`
- 需要恢复状态：`state-load auth.json`
- 并行环境里，`auth.json` 也要按 worker 隔离
- 真正需要共享状态时，共享 `state-save` 产物，不要共享 live session

## 并行模式

### 模式 1：完全隔离

每个 worker 都从自己的浏览器上下文开始，只共享任务说明，不共享浏览器状态。

适合：

- 多账号并测
- 多网站并查
- 并行抓取证据

### 模式 2：文件式交接

worker A 完成登录或准备动作后，只交接这些稳定产物：

- `state-save` 导出的状态文件
- 截图或 snapshot
- 当前 URL
- 下载好的文件
- console / network / trace artifact

worker B 只消费这些文件，不直接接管 A 的 live session。

适合：

- 先登录，再换 worker 做后续验证
- 先抓证据，再换 worker 生成测试

## 环境变量与清理规则

`PLAYWRIGHT_CLI_SESSION` 只适合在“当前 shell 只服务一个 worker”时使用。

不安全用法：

- 一个父 shell 导出同一个 `PLAYWRIGHT_CLI_SESSION`，再 fork 出多个 worker 共用它
- 不同工具实例继承到同一个 session 名

清理优先级从安全到危险：

1. `playwright-cli -s=<my-session> close`
2. 协调器根据自己分配的前缀逐个关闭自己的 session
3. `close-all`
4. `kill-all`

`close-all` 和 `kill-all` 只适合：

- 你独占整台工作机
- 你明确确认当前没有别的 worker 在跑
- 这是紧急清场，不是普通收尾

## 常见故障与原因

- A worker 登录后，B worker 看不到登录态：它们不是同一个 profile，或没有正确 `state-save` / `state-load`
- B worker 点了 A worker 的 `e17` 失败：ref 不是跨 session 的稳定标识
- 截图互相覆盖：多个 worker 写进同一个目录，且没显式命名
- 浏览器突然全没了：有人在共享环境里执行了 `close-all` 或 `kill-all`
- headed 输入跑偏：另一个窗口抢了焦点
