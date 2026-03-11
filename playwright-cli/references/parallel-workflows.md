# Parallel Workflows with playwright-cli

## 适用场景

这份说明专门给这些场景用：

- 多个 subagent 同时跑网页任务
- 多个 OpenCode / Codex / Claude Code session 共用一台机器
- 一个协调器把网页任务拆给多个 worker

## 先看这个最小流程

如果你不想先读完整篇，先照这 5 步跑：

1. 协调器为每个 worker 分配唯一 `session`
2. 每个 worker 使用独立 `profile/` 和 `artifacts/`
3. 每条命令都显式写 `-s=<session>`
4. 交接只传 `state-save`、截图、日志、URL、下载文件
5. 收尾时只关闭自己的 session

如果想把这套规则先固化成文件，再把文件发给多个 worker，先生成：

```bash
python playwright-cli/scripts/parallel_run_manifest.py \
  --run-id run42 \
  --tool opencode \
  --agent-id a1 \
  --agent-id a2 \
  --source https://example.com/a.pdf \
  --output ./tmp/run42/parallel-plan.json
```

## 最小安全模型

把下面这 4 条当成默认规则：

1. 一个 worker 一个 session
2. 一个 worker 一个 profile 目录
3. 一个 worker 一个 artifact 目录
4. 只有 session owner 才负责关闭自己的 session

如果做不到这 4 条，就很容易出现状态串线、登录态互相污染、截图写乱、错误清理掉别人的浏览器。

## 推荐目录约定

```text
tmp/
  playwright/
    run42/
      a1/
        profile/
        artifacts/
        state.json
      a2/
        profile/
        artifacts/
        state.json
```

## 推荐 session 约定

```text
pw-<tool>-<run_id>-<agent_id>
```

例如：

- `pw-opencode-run42-a1`
- `pw-claudecode-run42-a2`
- `pw-codex-run42-a3`

这样做的好处：

- `playwright-cli list` 时一眼能看出归属
- 协调器能按前缀筛选自己这次任务创建的 session
- 出问题时容易定位到具体 worker

## 推荐并行模式

### 模式 1：完全隔离

每个 worker 都从自己的浏览器上下文开始，只共享任务说明，不共享浏览器状态。

适合：

- 多账号并测
- 多网站并查
- 并行抓取证据

### 模式 2：文件式交接

worker A 完成登录或准备动作后，把可移交信息写出来：

- `state-save` 导出的状态文件
- 截图或 snapshot
- 当前 URL
- 下载好的文件
- console / network / trace artifact

worker B 只消费这些文件，不直接接管 A 的 live session。

适合：

- 先登录，再换 worker 做后续验证
- 先抓证据，再换 worker 生成测试

## 环境变量使用规则

`PLAYWRIGHT_CLI_SESSION` 很方便，但只适合在“当前 shell 只服务一个 worker”时使用。

安全用法：

```bash
PLAYWRIGHT_CLI_SESSION=pw-opencode-run42-a1 claude .
```

不安全用法：

- 一个父 shell 导出同一个 `PLAYWRIGHT_CLI_SESSION`，再 fork 出多个 worker 共用它
- 不同工具实例继承到同一个 session 名

## 清理规则

优先级从安全到危险：

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

## 实操模板

```bash
RUN_ID=run42
AGENT_ID=a1
SESSION="pw-opencode-${RUN_ID}-${AGENT_ID}"
ROOT="./tmp/playwright/${RUN_ID}/${AGENT_ID}"

playwright-cli -s="${SESSION}" open https://example.com \
  --persistent \
  --profile="${ROOT}/profile"

playwright-cli -s="${SESSION}" snapshot \
  --filename="${ROOT}/artifacts/01-home.yaml"

playwright-cli -s="${SESSION}" state-save "${ROOT}/state.json"

playwright-cli -s="${SESSION}" close
```

如果你是协调器，先看：`references/coordinator-template.md`
如果你想直接得到 JSON 计划文件，也可以直接用：`scripts/parallel_run_manifest.py`
