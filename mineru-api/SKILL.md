---
name: mineru-api
description: 使用 MinerU 云 API 解析 PDF、Office、图片或 HTML 文档，并通过轮询或批量接口获取结果。
license: MIT
compatibility: opencode
metadata:
  category: documents
  transport: https
  auth: bearer-token
---

# MinerU API Skill

## What I do

- 调用 MinerU API 解析 PDF、Office、图片或 HTML 文档
- 覆盖单文件 URL、批量 URL、本地文件批量上传、结果轮询
- 重点产出 `task_id` / `batch_id`、任务状态、`full_zip_url` 以及可交付 markdown

## Use me when

- 用户要把 PDF、Word、PPT、图片或 HTML 解析成结构化结果
- 用户要拿到 markdown / json 为主的解析产物
- 用户要做异步提交、轮询、批量处理或回调对接

优先不要用我：

- 用户只需要读取本地纯文本或现成 markdown
- 用户没有 Token，也不希望真的调用 MinerU API
- 用户给的是 GitHub / AWS 等国外直链，且当前网络环境大概率不可达

## Before you start

真实调用前先确认：

1. 是否有 MinerU Token
2. 是单文件还是批量
3. 输入来自 URL 还是本地文件
4. 是否只要 markdown/json，还是还要 `docx` / `html` / `latex`
5. 是否需要回调而不是轮询

如果缺少 Token、输入 URL 或本地文件路径，先向用户索取，不要假设。

## Token storage

不要把 Token 写进仓库、`SKILL.md`、脚本源码或命令历史。

推荐顺序：

1. 环境变量 `MINERU_API_TOKEN`
2. `MINERU_API_TOKEN_FILE`
3. `skills/mineru-api/.env.mineru.local`
4. `~/.config/mineru/token`
5. 交互式输入，仅用于临时手工执行

本仓库里最顺手的放法是 `mineru-api/.env.mineru.local`。

## Parallel and batch orchestration

这是默认规则。
并行时重点不是“多发请求”，而是“避免重复提交、输出互相覆盖、轮询把 API 打爆”。

### Minimum rules

1. 每个文档都要有稳定 `data_id`
2. 提交前先查任务表，避免同一文档被多个 worker 重复提交
3. 每个文档独立输出到 `./tmp/mineru/<run_id>/<data_id>/`
4. 同一个 token 下，把活跃提交和轮询控制在低个位数
5. 轮询间隔默认 `3-10` 秒，并加一点 jitter
6. 如果能用 batch，就优先用 batch，而不是让每个 worker 各自高频轮询

### Choose the right shape first

- 少量、彼此独立的文档：低并发单任务
- 一组公网 URL：优先 `POST /extract/task/batch`
- 一组本地文件：优先 `POST /file-urls/batch`
- 已经拿到 `full_zip_url`：不要重复提交，直接下载和清洗

### Safe patterns with playwright-cli

如果要和 `playwright-cli` 并行配合，默认这样分工：

1. `playwright-cli` worker 负责登录、找链接、下载文件
2. 协调器负责给文档分配 `data_id` 和输出目录
3. `mineru-api` worker 负责批量提交、轮询、下载 `full_zip_url`
4. 清洗阶段按文档独立输出，不共享 `assets/` 或 `manifest.json`

如果已经在用 `playwright-cli` 的并行规范，可以先生成统一计划文件：

```bash
python playwright-cli/scripts/parallel_run_manifest.py \
  --run-id run42 \
  --tool opencode \
  --agent-id a1 \
  --agent-id a2 \
  --source https://example.com/a.pdf \
  --source ./downloads/b.pdf \
  --output ./tmp/run42/parallel-plan.json
```

然后让浏览器 worker 使用里面的 `workers[*]`，让 MinerU worker 使用里面的 `documents[*]`。

更多细节见：`references/parallel-orchestration.md`

## Quick start

### A. 单文件 URL

1. `POST https://mineru.net/api/v4/extract/task`
2. 记录 `data.task_id`
3. `GET https://mineru.net/api/v4/extract/task/{task_id}` 轮询
4. 直到 `state=done`
5. 下载 `full_zip_url`

### B. 本地文件批量上传

1. `POST https://mineru.net/api/v4/file-urls/batch`
2. 对返回的预签名 URL 执行 `PUT`
3. 记录 `batch_id`
4. `GET https://mineru.net/api/v4/extract-results/batch/{batch_id}` 轮询

### C. URL 批量解析

1. `POST https://mineru.net/api/v4/extract/task/batch`
2. 记录 `batch_id`
3. `GET https://mineru.net/api/v4/extract-results/batch/{batch_id}` 轮询

## Helper script

优先使用 `scripts/mineru_to_markdown.py` 获取可交付 markdown。

它会：

- 提交 URL 或本地 PDF
- 自动轮询直到拿到 `full_zip_url`
- 下载并解压原始结果
- 输出清洗后的 markdown、`assets/` 和 `manifest.json`

最常见用法：

```bash
export MINERU_API_TOKEN='your-token'
python skills/mineru-api/scripts/mineru_to_markdown.py \
  --pdf ./paper.pdf \
  --output ./out/paper
```

如果输入是公网 URL：

```bash
export MINERU_API_TOKEN='your-token'
python skills/mineru-api/scripts/mineru_to_markdown.py \
  --url 'https://cdn-mineru.openxlab.org.cn/demo/example.pdf' \
  --output ./out/example
```

如果你已经有结果 ZIP：

```bash
python skills/mineru-api/scripts/mineru_to_markdown.py \
  --zip ./result.zip \
  --output ./out/result
```

这个脚本更像“单文档处理器”，不是通用并行调度器；大批量任务应由外层协调器分配 `data_id`、提交任务、轮询结果，再逐个调用脚本清洗。

## Golden rules

- 真实调用前先告诉用户：这是异步 API，需要轮询或等待回调
- 成功提交至少要拿到 `task_id` 或 `batch_id`
- 成功完成至少要拿到 `full_zip_url`
- 需要可交付 markdown 时，优先用 `scripts/mineru_to_markdown.py`
- 用户明确提到并行处理时，先设计 `data_id`、任务表、输出目录和轮询策略，再决定是单任务并发还是 batch API

## API quick reference

所有核心请求都需要：

```text
Authorization: Bearer <TOKEN>
Content-Type: application/json
Accept: */*
```

常用接口：

- `POST https://mineru.net/api/v4/extract/task`
- `GET https://mineru.net/api/v4/extract/task/{task_id}`
- `POST https://mineru.net/api/v4/file-urls/batch`
- `POST https://mineru.net/api/v4/extract/task/batch`
- `GET https://mineru.net/api/v4/extract-results/batch/{batch_id}`

常用字段：

- `url`
- `model_version`: `pipeline` / `vlm` / `MinerU-HTML`
- `data_id`
- `page_ranges`
- `callback` + `seed`
- `full_zip_url`

## Common failures

- `A0202`：Token 错误
- `A0211`：Token 过期
- `-500` / `-10002`：请求体或 `Content-Type` 错误
- `-60005`：文件大小超限
- `-60006`：页数超限
- `-60008`：URL 读取超时
- `-60018`：每日解析额度达到上限

## Pointers

- 并行编排：`mineru-api/references/parallel-orchestration.md`
- references 导航：`mineru-api/references/README.md`
- 清洗脚本：`mineru-api/scripts/mineru_to_markdown.py`
- 与 `playwright-cli` 共享计划文件：`playwright-cli/scripts/parallel_run_manifest.py`

## Tests

```bash
python -m unittest "mineru-api/tests/test_mineru_to_markdown.py" "mineru-api/tests/test_parallel_docs.py"
```

## How to help the user well

- 默认先选最简单的工作流：单文件 URL > URL 批量 > 本地文件批量上传
- 如果用户只是要“怎么接入”，优先给最小可用 curl 或脚本示例
- 如果用户已经拿到 `full_zip_url`，下一步转到下载、解压和读取结果文件，不要继续重复轮询
