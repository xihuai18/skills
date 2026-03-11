# Session Management with playwright-cli

## 什么时候要用命名 session

这些情况不要继续依赖默认 session：

- 同时操作两个网站或两个账号
- 一个任务要长期保留登录态
- 你需要让用户稍后继续接管同一个浏览器上下文
- 同一台机器上有多个 subagent 或多个 coding session 同时跑

## 常见模式

### 模式 1：一个任务一个 session

```bash
playwright-cli -s=checkout open https://example.com/checkout --persistent
playwright-cli -s=checkout snapshot
playwright-cli -s=checkout close
```

适合：流程明确、需要隔离状态。

### 模式 2：一个项目一个 session

```bash
playwright-cli -s=admin-panel open https://admin.example.com --persistent
playwright-cli -s=admin-panel state-save admin.json
```

适合：同一产品反复调试。

## 状态保存建议

- 需要跨浏览器重启复用状态：`--persistent`
- 需要显式导出登录态：`state-save auth.json`
- 需要恢复状态：`state-load auth.json`

如果是并行环境，再加两条：

- `auth.json` 也要按 worker 隔离，不要多个 worker 写同一个文件
- 真正需要共享状态时，共享 `state-save` 产物，不要共享一个 live session

## 共享机器上的额外规则

- 一个 worker 只用一个自己的 `-s=<session>`
- 如果用了 `--persistent` 或 `--profile`，目录必须独占
- `PLAYWRIGHT_CLI_SESSION` 只能在单 worker shell 里使用
- 普通 worker 不要执行 `close-all` 或 `kill-all`
- 交接时传文件、URL、日志，不要传 `e15` 这类 ref

## 排障建议

- session 异常时先 `playwright-cli list`
- 卡死时用 `playwright-cli close-all`
- 浏览器僵死或残留进程时再用 `playwright-cli kill-all`
- 用户想观察 agent 正在做什么时用 `playwright-cli show`

在共享环境里，上面两条要改成更保守的理解：

- 这里指的是前面排障列表里的 `close-all` 和 `kill-all`
- 先尝试只关闭自己的 session：`playwright-cli -s=<my-session> close`
- `close-all` / `kill-all` 应只由协调器或独占环境下的操作者执行
