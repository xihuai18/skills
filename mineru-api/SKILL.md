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

- 帮用户把 MinerU 文档解析能力接到实际工作流里
- 覆盖单文件 URL 解析、批量本地文件上传、批量 URL 解析、结果轮询
- 产出重点是 `task_id` / `batch_id`、任务状态、`full_zip_url` 以及后续结果下载建议

## When to use me

在这些场景优先使用我：

- 用户要把 PDF、Word、PPT、图片或 HTML 解析成结构化结果
- 用户要拿到 markdown / json 为主的解析产物
- 用户要做异步提交、轮询、批量处理或回调对接

这些场景不要优先使用我：

- 用户只需要读取本地纯文本或现成 markdown
- 用户没有 Token，也不希望真的调用 MinerU API
- 用户给的是 GitHub / AWS 等国外直链，且当前网络环境大概率不可达

## Before you start

真实调用 API 前先确认：

1. 是否有 MinerU Token
2. 是单文件还是批量
3. 输入来自 URL 还是本地文件
4. 目标格式是否只要默认 markdown/json，还是还要 `docx` / `html` / `latex`
5. 是否需要回调而不是轮询

如果缺少 Token、输入文件地址或本地文件路径，先向用户索取，不要假设。

## Token storage

不要把 Token 写进仓库、`SKILL.md`、脚本源码或命令历史。

推荐顺序：

1. 环境变量 `MINERU_API_TOKEN`
2. `MINERU_API_TOKEN_FILE` 指向一个本地 secret 文件
3. skill 目录里的 `skills/mineru-api/.env.mineru.local`
4. 默认 token 文件 `~/.config/mineru/token`
5. 交互式输入，仅用于临时手工执行

如果你就是在这个仓库里使用本 skill，最顺手的放法就是当前 skill 目录里的：`.env.mineru.local`

文件内容示例：

```dotenv
MINERU_API_TOKEN=your-token
```

这个目录下已经提供：

- `.gitignore`：忽略 `.env.mineru.local`
- `.env.mineru.local.example`：示例模板

## Helper script

这个 skill 自带一个脚本：`scripts/mineru_to_markdown.py`

它会：

- 调用 MinerU API 提交 URL 或本地 PDF
- 自动轮询直到拿到 `full_zip_url`
- 下载并解压原始结果
- 读取 markdown 与 `content_list.json`
- 输出一个更干净的 markdown 文件
- 把被引用的图片 / 表格 / 公式等资源复制到 `assets/`
- 按资源在文档里的出现顺序重命名，例如 `001-image.jpg`、`002-table.jpg`

### Script input modes

- `--pdf ./paper.pdf`：本地 PDF，自动申请上传 URL、上传文件、轮询结果
- `--url https://.../paper.pdf`：已有公网 URL，直接提交单任务
- `--zip ./result.zip`：已经下载好的 MinerU 结果 ZIP，只做清洗
- `--raw-dir ./raw`：已经解压好的 MinerU 原始目录，只做清洗

### Script output contract

默认会在 `--output` 指定目录写出：

- 一个清洗后的 markdown 文件，默认沿用原 markdown 文件名
- 一个 `assets/` 目录，只放 markdown 实际引用到的资源
- 一个 `manifest.json`，记录原始资源路径和重命名结果

资源排序规则：

- 优先读取 `*_content_list.json` 的阅读顺序
- 再用 markdown 中的实际引用补齐
- 对相同资源去重
- 最终按第一次出现的顺序编号

这意味着：如果原始图片名是 UUID / hash，看起来很乱，脚本仍会输出稳定文件名。

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

如果你已经有 `full_zip_url` 下载下来的原始 ZIP，也可以只做清洗：

```bash
python skills/mineru-api/scripts/mineru_to_markdown.py \
  --zip ./result.zip \
  --output ./out/result
```

## Default workflow

### A. 单文件 URL 解析

适合用户已经有公网可访问文件 URL 的情况。

1. `POST https://mineru.net/api/v4/extract/task`
2. 成功后记录 `data.task_id`
3. `GET https://mineru.net/api/v4/extract/task/{task_id}` 轮询
4. 直到 `state=done`
5. 从 `full_zip_url` 下载结果压缩包

### B. 本地文件批量上传解析

适合用户只有本地文件，没有公网 URL。

1. `POST https://mineru.net/api/v4/file-urls/batch` 申请上传链接
2. 对返回的每个预签名 URL 执行 `PUT` 上传文件
3. 记录 `batch_id`
4. `GET https://mineru.net/api/v4/extract-results/batch/{batch_id}` 轮询批量结果

### C. URL 批量解析

适合已有一组可访问 URL。

1. `POST https://mineru.net/api/v4/extract/task/batch`
2. 记录 `batch_id`
3. `GET https://mineru.net/api/v4/extract-results/batch/{batch_id}` 轮询

## Parallel and batch orchestration

当多个 agent 同时处理很多文档时，重点不是“能不能并行发请求”，而是“如何避免重复提交、输出互相覆盖、轮询把 API 打爆”。

### Choose the right shape first

- 少量、彼此独立的文档：可以用多个单任务，但要限制并发数
- 一组公网 URL：优先 `POST /extract/task/batch`
- 一组本地文件：优先 `POST /file-urls/batch`
- 已经拿到 `full_zip_url`：不要重复提交，直接进入下载和清洗

### Identity and dedup

并行时，每个文档都要有稳定标识，至少保存：

- `source`: 原始 URL 或本地路径
- `data_id`: 业务侧唯一 ID
- `task_id` 或 `batch_id`
- `output_dir`
- `state`

推荐做法：

- 先为每个文档分配稳定 `data_id`
- 真正提交前先查本地任务表，避免同一份文档被多个 worker 重复提交
- 轮询和下载阶段也继续沿用同一个 `data_id`

### Output isolation

不要让多个文档共用一个输出目录。推荐：

```text
./tmp/mineru/<run_id>/<data_id>/
```

每个 `data_id` 下单独保存：

- 原始 zip
- 解压后的 raw 目录
- 清洗后的 markdown
- `assets/`
- `manifest.json`
- 一个任务元数据文件，例如 `job.json`

### Polling discipline

没有明确官方限流数字时，先用保守策略：

- 同一个 token 下，把活跃提交和轮询控制在低个位数
- 轮询间隔默认 `3-10` 秒
- 给不同 worker 的轮询时间加一点 jitter，避免同时打到同一秒
- 遇到网络抖动、`5xx`、超时，做指数退避后再重试

如果是大批量任务，优先减少“轮询 worker 数量”，而不是让每个 worker 自己高频轮询。

### Helper script scope

`scripts/mineru_to_markdown.py` 更像“单文档处理器”，不是通用并行调度器。

- 它适合处理一个 URL、一个 PDF、一个 ZIP 或一个 raw 目录
- 如果你有很多文档，应该由外层协调器分配 `data_id`、提交任务、轮询结果、再逐个调用脚本清洗

### Safe patterns with playwright-cli

这两个 skill 可以并行配合，但交接物必须稳定、可落盘。

如果只想先快速、安全地并行起来，默认用这个分工：

1. `playwright-cli` worker 负责登录、找链接、下载文件
2. 一个协调器负责给文档分配 `data_id` 和输出目录
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

模式 A：`playwright-cli` 收集 URL，MinerU 解析

1. 多个浏览器 worker 各自访问页面、拿到文档 URL
2. 它们把 URL 和元数据写进统一任务队列文件或目录
3. 单独的 MinerU worker 读取这些 URL，按批或按小并发提交

模式 B：`playwright-cli` 下载受登录保护的文件，MinerU 批量上传

1. 浏览器 worker 用各自独立下载目录把 PDF 下载到本地
2. 协调器汇总本地文件列表
3. MinerU worker 走 `/file-urls/batch` 上传并轮询

模式 C：MinerU 先解析，浏览器 worker 再做结果验证

1. MinerU worker 产出 markdown 和资源目录
2. 浏览器 worker 用这些结果做页面比对、预览验证或回归检查

并行交接时不要共享：

- 同一个浏览器下载目录
- 同一个 MinerU 输出目录
- 同一个文档的重复提交权限

更多细节见：`references/parallel-orchestration.md`

## Auth and headers

所有核心请求都需要：

```text
Authorization: Bearer <TOKEN>
Content-Type: application/json
Accept: */*
```

如果报 `A0202` 或 `A0211`，优先检查 Token 是否错误、过期，或者是否漏掉了 `Bearer ` 前缀。

## API quick reference

### 1. 单文件 URL 创建任务

`POST https://mineru.net/api/v4/extract/task`

常用请求体字段：

- `url`：必填，文件 URL
- `model_version`：`pipeline` / `vlm` / `MinerU-HTML`
- `is_ocr`：是否启用 OCR
- `enable_formula`：是否启用公式识别
- `enable_table`：是否启用表格识别
- `language`：文档语言
- `data_id`：业务侧唯一 ID
- `extra_formats`：可选附加导出格式，支持 `docx` / `html` / `latex`
- `page_ranges`：页码范围
- `no_cache` / `cache_tolerance`：缓存控制
- `callback` + `seed`：如果要服务端回调，二者配合使用

### 2. 查询单任务结果

`GET https://mineru.net/api/v4/extract/task/{task_id}`

重点状态：

- `pending`：排队中
- `running`：解析中
- `converting`：格式转换中
- `done`：完成
- `failed`：失败

结果字段重点看：

- `task_id`
- `state`
- `full_zip_url`
- `err_msg`
- `extract_progress`

### 3. 本地文件批量上传

`POST https://mineru.net/api/v4/file-urls/batch`

重点：

- 单次最多 200 个文件
- 先申请上传链接，再对返回 URL 执行 `PUT`
- 上传完成后系统会自动提交解析任务
- 不需要再额外调用“提交任务”接口

### 4. URL 批量提交

`POST https://mineru.net/api/v4/extract/task/batch`

重点：

- 适合一组公网 URL
- 返回 `batch_id`
- 后续统一走批量结果查询接口

### 5. 批量结果查询

`GET https://mineru.net/api/v4/extract-results/batch/{batch_id}`

批量状态除了单任务常见状态外，还可能出现：

- `waiting-file`：等待文件上传完成后再排队提交解析

## Model selection

- 默认可按 `pipeline` 理解
- 如果用户明确偏好更强视觉理解，可用 `vlm`
- 如果输入是 HTML，`model_version` 必须明确指定为 `MinerU-HTML`

## Limits and caveats

- 单文件最大 `200MB`
- 单文件页数上限 `600`
- 每账号每天有 `2000` 页最高优先级额度，超出后优先级下降
- 国外 URL 可能超时，尤其是 GitHub / AWS
- 该服务不支持“直接上传单文件”；本地文件需走批量上传拿预签名 URL

## Callback notes

如果用户希望回调而不是轮询：

- 请求体需要提供 `callback`
- 使用回调时，`seed` 必填
- 回调方要支持 `POST`、`UTF-8`、`Content-Type: application/json`
- 需要按文档规则校验 `checksum`
- 服务端收到回调后返回 `200` 才算接收成功

## Success criteria

成功提交任务至少满足：

- HTTP 成功返回
- 响应中 `code = 0`
- 单任务拿到 `task_id`，或批量拿到 `batch_id`

成功完成解析至少满足：

- `state = done`
- 拿到 `full_zip_url`
- 脚本或人工流程产出了可直接使用的 markdown 文件
- 被引用资源被整理进单独 `assets/` 目录
- 资源名按出现顺序重命名完成，且 markdown 引用已同步改写
- 生成了 `manifest.json`，能回溯原文件名和新文件名的映射

## Common failures

- `A0202`：Token 错误
- `A0211`：Token 过期
- `-500` / `-10002`：请求体或 `Content-Type` 错误
- `-60005`：文件大小超限
- `-60006`：页数超限
- `-60008`：URL 读取超时
- `-60012`：任务不存在
- `-60013`：没有权限访问该任务
- `-60018`：每日解析额度达到上限
- `-60019`：HTML 解析额度不足

## Example: single URL task

```bash
TOKEN="your-token"
FILE_URL="https://cdn-mineru.openxlab.org.cn/demo/example.pdf"

curl --location --request POST 'https://mineru.net/api/v4/extract/task' \
  --header "Authorization: Bearer ${TOKEN}" \
  --header 'Content-Type: application/json' \
  --header 'Accept: */*' \
  --data-raw "{\"url\":\"${FILE_URL}\",\"model_version\":\"vlm\"}"
```

## Example: poll task result

```bash
TOKEN="your-token"
TASK_ID="replace-me"

curl --location --request GET "https://mineru.net/api/v4/extract/task/${TASK_ID}" \
  --header "Authorization: Bearer ${TOKEN}" \
  --header 'Accept: */*'
```

## Example: apply upload URLs for local files

```bash
TOKEN="your-token"

curl --location --request POST 'https://mineru.net/api/v4/file-urls/batch' \
  --header "Authorization: Bearer ${TOKEN}" \
  --header 'Content-Type: application/json' \
  --header 'Accept: */*' \
  --data-raw '{
    "files": [{"name": "demo.pdf", "data_id": "demo-001"}],
    "model_version": "vlm"
  }'
```

## How to help the user well

- 默认先选最简单的工作流：单文件 URL > URL 批量 > 本地文件批量上传
- 真实调用前，明确告诉用户你将使用异步 API，结果需要轮询或等待回调
- 如果用户只是要“怎么接入”，优先输出最小可用 curl 示例和状态说明
- 如果用户已经拿到 `full_zip_url`，下一步重点转到下载、解压和读取结果文件，而不是继续重复轮询
- 如果用户目标是“拿到可交付 markdown”，优先让其使用 `scripts/mineru_to_markdown.py`，而不是让用户手动拼接 API + 解压 + 重命名流程
- 如果用户明确提到并行处理，先帮用户设计 `data_id`、任务表、输出目录和轮询策略，再决定是单任务并发还是 batch API
