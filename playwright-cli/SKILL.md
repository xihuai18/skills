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
- 适合登录、表单填写、截图取证、前端报错排查、真实用户路径验证
- 默认按 CLI 工作流运行，比长会话浏览器控制更轻、更适合反复调用

## Use me when

- 用户要操作真实网页，而不是只抓静态 HTML
- 用户要登录、上传、切标签、下载文件、看 console 或 network
- 用户明确要求使用 `playwright-cli`
- 用户要在 CI、SSH 或远程环境里跑真实浏览器流程

优先不要用我：

- 用户只要静态文本抓取
- 本地已有 Playwright test，且用户只要求修测试代码
- 环境没装 `@playwright/cli`，且用户不希望装新工具

## Before you start

先确认：

1. Node.js 18+
2. `playwright-cli` 可执行

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
```

如果全局命令不可用：

```bash
npx playwright-cli --help
```

## Parallel safety for multi-agent work

这是默认且优先的规则。
如果多个 subagent、多个 OpenCode / Codex / Claude Code session 会在同一台机器上同时调用 `playwright-cli`，先遵守这里，再做别的。

### Quick start checklist

1. 先分配唯一 `run_id` 和 `agent_id`
2. 用 `pw-<tool>-<run_id>-<agent_id>` 生成 session 名
3. 给这个 worker 单独准备 `profile/`、`artifacts/`、`downloads/`、`state.json`
4. 所有命令都显式带 `-s=<session>`
5. 收尾时只关闭自己的 session，不要动 `close-all`

如果你想直接生成一份可分发给 worker 的计划文件，可以先跑：

```bash
python playwright-cli/scripts/parallel_run_manifest.py --help
```

### Hard rules

1. 一个 worker 只拥有一个自己的 session；永远显式传 `-s=<unique-session>`，不要依赖默认 session。
2. 一个 worker 只拥有一个自己的 profile 目录；只要用了 `--persistent` 或 `--profile`，目录就必须独占，不能共享。
3. 一个 worker 只写自己的 artifact 和 download 目录；`snapshot`、`screenshot`、`trace`、下载文件都写进独立路径。
4. session 的创建者负责清理自己的 session；普通 worker 不要对共享环境执行 `close-all` 或 `kill-all`。
5. `e15` 这类 ref 只在“同一个 session + 最新 snapshot”里有效；不要跨 session、跨 agent、跨快照传递 ref。
6. 并行时默认 headless；只有确实需要人工观察某个 worker 时，才把那个 worker 单独切到 `--headed`。
7. 交接用不可变产物，例如 `state-save` 文件、截图、trace、日志、URL、下载好的文件；不要让两个 agent 共用一个活的浏览器上下文。

### Naming convention

- session: `pw-<tool>-<run_id>-<agent_id>`
- profile dir: `./tmp/playwright/<run_id>/<agent_id>/profile`
- artifact dir: `./tmp/playwright/<run_id>/<agent_id>/artifacts`
- download dir: `./tmp/playwright/<run_id>/<agent_id>/downloads`
- state file: `./tmp/playwright/<run_id>/<agent_id>/state.json`

更多细节见：`references/parallel-and-sessions.md`

## Quick start

最小工作流：

```bash
playwright-cli open https://playwright.dev
playwright-cli snapshot
playwright-cli click e15
playwright-cli press Enter
playwright-cli screenshot
playwright-cli close
```

核心心智模型：

1. `open` 或 `goto`
2. `snapshot` 获取最新 ref
3. 用 ref 做 `click` / `fill` / `check` / `select`
4. 在关键节点保存 artifact
5. `close`，或保留 session 继续工作

重要习惯：

- 导航后先 `snapshot`
- 页面变化后再 `snapshot`
- 不要猜 ref
- `snapshot` 是主工作流，`screenshot` 是交付物

## Golden rules

- 默认 headless；不要因为没弹出窗口就判定失败
- 命名 session，不要长期依赖默认 session
- 交付给用户的 artifact 尽量显式写 `--filename`
- 需要复用状态时用 `--persistent`、`state-save`、`state-load`
- 用户明确提到多 subagent 或多 coding session 并行，第一时间分配唯一 session、profile 目录和 artifact 目录

## Common workflows

### A. 页面验证

1. `open`
2. `snapshot`
3. 按 ref 交互
4. 用 `console` / `network` / `screenshot` 留证据

### B. 登录或表单提交

1. 打开页面后先 `snapshot`
2. 用 `fill` 或 `type` 输入
3. 提交前后各做一次 `snapshot`
4. 需要复用状态时用 `state-save` 或 `--persistent`

### C. 前端问题排查

1. 重现问题
2. 立即跑 `console`
3. 必要时跑 `network`
4. 需要更深调试时用 `tracing-start` / `tracing-stop`

### D. 生成测试思路

1. 先用 CLI 真实走完用户路径
2. 固化稳定步骤和断言点
3. 再翻译成 Playwright test

更多细节见：`references/test-generation.md`

## Commands to reach for first

```bash
playwright-cli open https://example.com
playwright-cli goto https://example.com/login
playwright-cli snapshot
playwright-cli click e3
playwright-cli fill e5 "user@example.com"
playwright-cli press Enter
playwright-cli screenshot --filename=page.png
playwright-cli console
playwright-cli network
playwright-cli state-save auth.json
playwright-cli state-load auth.json
playwright-cli show
```

默认就是 headless；更多细节见：`references/headless-mode.md`

## Common mistakes

- 没有先 `snapshot` 就直接猜元素 ref
- 页面更新后继续使用旧 ref
- 以为没弹出浏览器就是失败；其实 CLI 默认就是 headless
- 应该用命名 session 却一直复用默认 session，导致状态混乱
- 在并行环境里让多个 worker 共享同一个 `PLAYWRIGHT_CLI_SESSION`
- 使用 `--persistent` 或 `--profile` 时复用同一个 profile 目录
- 把某个 session 里的元素 ref 交给另一个 session 继续操作
- 共享环境里随手执行 `close-all` 或 `kill-all`

## Pointers

- `playwright-cli/references/parallel-and-sessions.md` - 需要协调多个 worker、管理 session、做文件式交接时再读
- `playwright-cli/references/headless-mode.md` - 需要稳定 headless 行为或远程环境细节时再读
- `playwright-cli/references/test-generation.md` - 需要把真实流程翻译成 Playwright test 时再读
- 统一计划生成：`playwright-cli/scripts/parallel_run_manifest.py`

## Tests

```bash
python -m unittest "playwright-cli/tests/test_playwright_cli_smoke.py"
python -m unittest "playwright-cli/tests/test_parallel_docs.py" "playwright-cli/tests/test_parallel_run_manifest.py"
```

## How to help the user well

- 对“调试网页”任务，优先给可复现命令链，而不是只给口头描述
- 对“写测试”任务，先用 CLI 把真实用户路径走通，再总结测试步骤
- 对“截图/录屏取证”任务，明确输出文件名与保存时机
- 对并行任务，先做隔离和命名，再开始浏览器操作
