---
name: playwright-cli
description: 使用 playwright-cli 做网页导航、表单交互、截图、录屏、网络调试、多标签和会话管理。
license: Apache-2.0
compatibility: opencode
metadata:
  category: browser-automation
  requires_cli: '@playwright/cli'
  workflow: cli-first
---

# Playwright CLI Skill

## What I do

- 用 `playwright-cli` 驱动真实浏览器完成网页任务
- 适合登录、表单填写、截图、抓取页面信息、调试前端问题
- 比 MCP 更偏 CLI 工作流：命令短、上下文更轻、适合 coding agent 持续调用

## Before you start

需要先具备这些前提：

1. Node.js 18+
2. 已安装 CLI

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
```

3. 如果全局命令不可用，可改用：

```bash
npx playwright-cli --help
```

4. 如果用户想直接使用上游仓库自带 skill，可以执行：

```bash
playwright-cli install --skills
```

## When to use me

优先使用我：

- 用户要操作真实网页
- 用户要填写表单、登录、切标签、上传文件
- 用户要生成截图、PDF、trace、video 或排查控制台 / 网络请求
- 用户明确要求使用 `playwright-cli`
- 用户要在 CI、SSH 或远程无界面环境里跑真实网页流程

不要优先使用我：

- 用户只需要静态抓取 HTML 文本
- 本地已有 Playwright 测试且用户只要修代码，不需要真实浏览器交互
- 环境里没有安装 `@playwright/cli` 且用户不希望安装任何额外工具

## Core mental model

`playwright-cli` 的基本流程是：

1. `open` 或 `goto`
2. `snapshot` 获取元素引用
3. 使用形如 `e15` 的 ref 做 `click` / `fill` / `check` / `select`
4. 在关键节点保存 artifact
5. `close` 或保留 session 继续工作

重要习惯：

- 导航后先 `snapshot`
- 页面结构变化后再 `snapshot`
- 不要猜 ref；要根据最新 snapshot 操作
- `screenshot` 适合交付物，`snapshot` 才是主工作流

## Quick start

```bash
playwright-cli open https://playwright.dev
playwright-cli snapshot
playwright-cli click e15
playwright-cli type "locator"
playwright-cli press Enter
playwright-cli screenshot
playwright-cli close
```

## Headless mode first

`playwright-cli` 默认就是 headless；`open --help` 只有 `--headed`，没有单独的 `--headless` 开关。
所以 agent 的默认策略应是：先按 headless 跑通，再在确有必要时切到 headed。

优先保持 headless 的场景：

- 远程 shell、CI、SSH 或容器里没有可见桌面
- 任务目标是抓证据，而不是人工盯着页面
- agent 要长时间、低干扰地反复调用浏览器
- 需要把 artifact 留到文件里供用户复查

推荐命令链：

```bash
playwright-cli -s=bug-123 open https://example.com/login
playwright-cli -s=bug-123 snapshot --filename=01-login.yaml
playwright-cli -s=bug-123 fill e5 "user@example.com"
playwright-cli -s=bug-123 screenshot --filename=02-filled.png
playwright-cli -s=bug-123 console warning
playwright-cli -s=bug-123 network
playwright-cli -s=bug-123 close
```

headless 下的关键习惯：

- 用 `snapshot` 决定下一步，用 `screenshot` / `console` / `network` 留证据
- 对要交付给用户的 artifact 指定 `--filename`，避免时间戳文件难以追踪
- 需要观察实时画面时，先试 `playwright-cli show`；只有确实需要人工看着操作，再改成 `open --headed`
- 如果要让 headless 行为在重复任务里显式可见，用配置文件固定 `launchOptions.headless: true`

更多细节见：`references/headless-mode.md`

## Commands to reach for first

### Open and navigate

```bash
playwright-cli open
playwright-cli open https://example.com
playwright-cli open https://example.com --headed
playwright-cli goto https://example.com/login
playwright-cli reload
playwright-cli go-back
playwright-cli go-forward
```

### Inspect and interact

```bash
playwright-cli snapshot
playwright-cli click e3
playwright-cli dblclick e7
playwright-cli fill e5 "user@example.com"
playwright-cli type "hello"
playwright-cli press Enter
playwright-cli hover e4
playwright-cli select e9 "option-value"
playwright-cli check e12
playwright-cli uncheck e12
playwright-cli drag e2 e8
playwright-cli upload ./document.pdf
playwright-cli eval "document.title"
playwright-cli eval "el => el.textContent" e5
```

### Save artifacts

```bash
playwright-cli screenshot
playwright-cli screenshot e5
playwright-cli screenshot --filename=page.png
playwright-cli pdf --filename=page.pdf
playwright-cli console
playwright-cli console warning
playwright-cli network
```

### Debug deeper

```bash
playwright-cli run-code "async page => await page.title()"
playwright-cli tracing-start
playwright-cli tracing-stop
playwright-cli video-start
playwright-cli video-stop demo.webm
playwright-cli route "**/*.jpg" --status=404
playwright-cli route-list
playwright-cli unroute
```

## Sessions

命名 session 很重要，尤其是并行任务或需要长期保留登录态时。

```bash
playwright-cli -s=todo-app open https://demo.playwright.dev/todomvc/ --persistent
playwright-cli -s=todo-app snapshot
playwright-cli -s=todo-app click e21
playwright-cli -s=todo-app close
```

常用命令：

```bash
playwright-cli list
playwright-cli close-all
playwright-cli kill-all
playwright-cli show
```

注意：`close-all` 和 `kill-all` 只适合你独占当前机器或独占当前浏览器工作区时使用。
如果有多个 subagent、多个 coding session，或多个工具实例并行跑浏览器，普通 worker 不要把这两个命令当日常清理手段。

如果用户希望 agent 默认使用同一个 session，也可以配合环境变量：

```bash
PLAYWRIGHT_CLI_SESSION=todo-app claude .
```

但在并行环境里，这个环境变量只能在“单个 worker 自己的 shell”里使用，不能让多个 worker 共享同一个值。

## Persistence and state

- 默认 profile 在内存里，浏览器关掉就丢失
- `--persistent` 会把 profile 落盘，适合需要跨重启保留状态
- `state-save` / `state-load` 适合显式保存与恢复登录态

常用命令：

```bash
playwright-cli state-save auth.json
playwright-cli state-load auth.json
playwright-cli cookie-list
playwright-cli localstorage-list
playwright-cli sessionstorage-list
```

更多细节见：`references/session-management.md`

## Parallel safety for multi-agent work

如果多个 subagent、多个 OpenCode / Codex / Claude Code session 会在同一台机器上同时调用 `playwright-cli`，要把下面这些当成硬规则。

### Quick start checklist

如果你只想先安全跑起来，先照这个最小清单做：

1. 先分配唯一 `run_id` 和 `agent_id`
2. 用 `pw-<tool>-<run_id>-<agent_id>` 生成 session 名
3. 给这个 worker 单独准备 `profile/`、`artifacts/`、`state.json`
4. 所有命令都显式带 `-s=<session>`
5. 收尾时只关闭自己的 session，不要动 `close-all`

如果你想直接生成一份可分发给 worker 的计划文件，可以先跑：

```bash
python playwright-cli/scripts/parallel_run_manifest.py \
  --run-id run42 \
  --tool opencode \
  --agent-id a1 \
  --agent-id a2 \
  --source https://example.com/a.pdf \
  --source https://example.com/b.pdf \
  --output ./tmp/run42/parallel-plan.json
```

### Hard rules

1. 一个 worker 只拥有一个自己的 session；永远显式传 `-s=<unique-session>`，不要依赖默认 session。
2. 一个 worker 只拥有一个自己的 profile 目录；只要用了 `--persistent` 或 `--profile`，目录就必须独占，不能共享。
3. 一个 worker 只写自己的 artifact 目录；`snapshot`、`screenshot`、`video`、`trace`、下载文件都要放进独立路径，并尽量显式写 `--filename`。
4. session 的创建者负责清理自己的 session；普通 worker 不要对共享环境执行 `close-all` 或 `kill-all`。
5. `e15` 这类 ref 只在“同一个 session + 最新 snapshot”里有效；不要跨 session、跨 agent、跨快照传递 ref。
6. 并行时默认 headless；只有确实需要人工观察某个 worker 时，才把那个 worker 单独切到 `--headed`。
7. 交接用不可变产物，例如 `state-save` 文件、截图、trace、日志、URL、下载好的文件；不要让两个 agent 共用一个活的浏览器上下文。

### Naming convention

推荐统一命名，便于协调器回收、排障和追踪：

- session: `pw-<tool>-<run_id>-<agent_id>`
- profile dir: `./tmp/playwright/<run_id>/<agent_id>/profile`
- artifact dir: `./tmp/playwright/<run_id>/<agent_id>/artifacts`
- download dir: `./tmp/playwright/<run_id>/<agent_id>/downloads`
- state file: `./tmp/playwright/<run_id>/<agent_id>/state.json`

例如：

```bash
playwright-cli -s=pw-opencode-run42-a1 open https://example.com \
  --persistent \
  --profile="./tmp/playwright/run42/a1/profile"

playwright-cli -s=pw-opencode-run42-a1 snapshot \
  --filename="./tmp/playwright/run42/a1/artifacts/01-home.yaml"

playwright-cli -s=pw-opencode-run42-a1 screenshot \
  --filename="./tmp/playwright/run42/a1/artifacts/02-home.png"
```

### Coordinator pattern

最稳的并行方式不是“大家自己随便开浏览器”，而是有一个协调器先分配这些资源：

1. `run_id`
2. `session`
3. `profile dir`
4. `artifact dir`
5. 任务边界和清理责任

推荐模式：

- 协调器分配唯一 `session` 和目录
- worker 只操作自己名下的 session
- 需要交接时，worker 先 `state-save` 或保存 artifact
- 下一个 worker 用 `state-load`、文件、URL、日志继续，而不是强占前一个 worker 的 live session

最小模板见：`references/coordinator-template.md`
需要可直接生成 JSON 计划时，见：`scripts/parallel_run_manifest.py`

### Unsafe patterns to avoid

这些写法在并行场景里经常出问题：

- 多个 worker 都用默认 session
- 多个 worker 共享同一个 `PLAYWRIGHT_CLI_SESSION`
- 多个 worker 共享同一个 `--profile` 目录
- A agent 把 `snapshot` 里的 `e12` 直接交给 B agent 去点
- 某个 worker 为了“清干净环境”直接执行 `playwright-cli close-all`
- 多个 headed 浏览器同时跑，需要键盘输入时互相抢焦点

更多细节见：`references/parallel-workflows.md`

## Recommended workflow patterns

### A. 真实页面验证

1. `open` 到目标页面
2. `snapshot`
3. 按 ref 执行交互
4. 在关键节点用 `console` / `network` / `screenshot` 留证据
5. 输出用户可复现的步骤

### B. 表单提交或登录

1. 打开页面后先 `snapshot`
2. 用 `fill` / `type` 输入
3. 提交前后各做一次 `snapshot`
4. 若需要保留状态，用 `state-save` 或 `--persistent`

### C. 前端报错排查

1. 重现问题
2. 立即跑 `console`
3. 必要时跑 `network`
4. 如需更深信息，用 `tracing-start` / `tracing-stop`

### D. 生成测试思路

1. 先用 CLI 真实走完用户流程
2. 固化稳定步骤和断言点
3. 再把它们翻译成 Playwright test

更多细节见：`references/test-generation.md`

## Open parameters

```bash
playwright-cli open --browser=chrome
playwright-cli open --browser=firefox
playwright-cli open --browser=webkit
playwright-cli open --browser=msedge
playwright-cli open --extension
playwright-cli open --persistent
playwright-cli open --profile=/path/to/profile
playwright-cli open --config=my-config.json
```

## Success criteria

一个任务完成得好，通常至少满足：

- 页面交互步骤可复现
- 关键证据被记录下来，例如 snapshot、screenshot、console、network、trace 或 video
- 如果要交付测试，交付的是稳定步骤，不依赖过时 ref

## Common mistakes

- 没有先 `snapshot` 就直接猜元素 ref
- 页面更新后继续使用旧 ref
- 以为没弹出浏览器就是失败；其实 CLI 默认就是 headless
- 应该用命名 session 却一直复用默认 session，导致状态混乱
- 在并行环境里让多个 worker 共享同一个 `PLAYWRIGHT_CLI_SESSION`
- 使用 `--persistent` 或 `--profile` 时复用同一个 profile 目录
- 把某个 session 里的元素 ref 交给另一个 session 继续操作
- 共享环境里随手执行 `close-all` 或 `kill-all`
- 在 headless 下需要精确输入却直接 `type`，没有先聚焦或改用 `fill <ref> <text>`
- 明明要交付证据，却只做了交互没保存 artifact
- 环境里没装 `@playwright/cli`，却直接假设 `playwright-cli` 可执行

## Local fallback

如果用户的环境里没有全局二进制，可改用：

```bash
npx playwright-cli open https://example.com
npx playwright-cli snapshot
```

## Tests

这个 skill 在仓库里带了一个最小 smoke test：

```bash
python -m unittest "playwright-cli/tests/test_playwright_cli_smoke.py"
```

它会验证两件事：

- `playwright-cli --help` 可用
- 默认 headless 流程 `open -> snapshot -> eval -> screenshot -> close` 可跑通，并产出 artifact

## How to help the user well

- 对“调试网页”任务，优先给可复现命令链，而不是只给口头描述
- 对“写测试”任务，先用 CLI 把真实用户路径走通，再总结测试步骤
- 对“截图/录屏取证”任务，明确输出文件名与保存时机
- 如果用户明确提到多页面、多账号或长期会话，第一时间启用命名 session
- 如果用户明确提到多 subagent 或多 coding session 并行，第一时间分配唯一 session、profile 目录和 artifact 目录
