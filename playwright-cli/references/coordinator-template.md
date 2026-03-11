# Coordinator Template for Parallel playwright-cli Runs

## 目标

这份模板给协调器或父 agent 用，用来在多 worker 并行时先把命名、目录和职责定下来。

如果你不想手工拼这些字段，也可以直接生成：

```bash
python playwright-cli/scripts/parallel_run_manifest.py \
  --run-id run42 \
  --tool opencode \
  --agent-id a1 \
  --agent-id a2 \
  --output ./tmp/run42/parallel-plan.json
```

## Step 1: 分配运行标识

先给这次并行任务一个 `run_id`，再给每个 worker 一个 `agent_id`。

推荐：

- `run_id`: `run42`
- `agent_id`: `a1`, `a2`, `a3`

## Step 2: 为每个 worker 生成资源

每个 worker 都要有自己的一套：

- session
- profile 目录
- artifacts 目录
- state 文件

公式：

```text
session  = pw-<tool>-<run_id>-<agent_id>
root     = ./tmp/playwright/<run_id>/<agent_id>
profile  = <root>/profile
artifacts= <root>/artifacts
downloads= <root>/downloads
state    = <root>/state.json
```

这个公式与 `scripts/parallel_run_manifest.py` 的输出保持一致。

## Step 3: 把资源交给 worker

给 worker 的最小输入应包含：

```json
{
  "run_id": "run42",
  "agent_id": "a1",
  "session": "pw-<tool>-run42-a1",
  "root": "./tmp/playwright/run42/a1",
  "profile_dir": "./tmp/playwright/run42/a1/profile",
  "artifact_dir": "./tmp/playwright/run42/a1/artifacts",
  "download_dir": "./tmp/playwright/run42/a1/downloads",
  "state_file": "./tmp/playwright/run42/a1/state.json"
}
```

其中 `<tool>` 由协调器决定，例如 `opencode`、`claudecode` 或其他调用方标识。

## Step 4: Worker command template

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
```

## Step 5: Cleanup contract

协调器要提前说清楚：

- worker 只能关闭自己的 session
- worker 不得执行 `close-all` 或 `kill-all`
- 需要全局清理时，只由协调器执行

## Step 6: Handoff contract

worker 之间只交接这些稳定产物：

- `state.json`
- screenshot
- snapshot
- trace / video
- 当前 URL
- 下载好的文件

不要交接：

- 默认 session
- 共享 profile 目录
- `e15` 这类元素 ref

## 最小开工检查

协调器发任务前，最好快速确认：

- 每个 worker 的 session 是否唯一
- 每个 worker 的 profile 路径是否唯一
- 每个 worker 的 artifact 路径是否唯一
- 是否明确谁负责最终清理
