# Parallel Orchestration with MinerU API

## 最小任务表

并行时至少维护这样一份任务表，可以是 JSONL、CSV 或数据库：

```json
{
  "data_id": "paper-001",
  "source": "https://example.com/a.pdf",
  "task_id": null,
  "batch_id": "batch-123",
  "state": "pending",
  "output_dir": "./tmp/mineru/run42/paper-001"
}
```

这样做的目的：

- 避免重复提交
- 让轮询 worker 知道该查谁
- 失败时能续跑

## 协调器最小职责

如果浏览器 worker 和 MinerU worker 会同时跑，最好有一个轻量协调器统一负责：

- 分配 `run_id`
- 为每个文档生成稳定 `data_id`
- 记录 `source -> data_id -> output_dir`
- 决定哪些走 batch，哪些走低并发单任务
- 控制全局轮询频率

推荐输出目录：

```text
./tmp/mineru/<run_id>/<data_id>/
```

## 输出目录建议

```text
tmp/
  mineru/
    run42/
      run42-doc-001/
        job.json
        raw.zip
        raw/
        clean.md
        assets/
        manifest.json
```

不要让两个文档共用同一个 `assets/` 或 `manifest.json`。

## 轮询建议

- 基础轮询间隔先用 `3-10` 秒
- 多个 worker 时给每个 worker 加随机 jitter
- 网络错误或 `5xx` 时指数退避
- 对 `failed` 保留错误和上下文，不要直接丢弃

## 与 playwright-cli 的分工建议

### 浏览器侧负责

- 登录
- 打开受权限保护的页面
- 获取真实下载链接
- 下载 PDF / Office 文件到本地

### MinerU 侧负责

- 统一提交解析
- 统一轮询
- 下载 `full_zip_url`
- 清洗 markdown 和资源

### 最稳的交接物

- URL 列表
- 本地文件路径列表
- `data_id -> source` 映射
- 下载好的文件

不要把浏览器 live session 当作 MinerU worker 的输入依赖。

## 一个易用的组合模板

### 阶段 1: 浏览器 worker

- 每个 worker 用自己的 `session/profile/download dir`
- 把发现的 URL 或下载好的本地文件写入任务队列
- 队列记录至少包含 `source`、`data_id`、`output_dir`

如果想少做手工命名，可以先生成统一计划文件：

```bash
python playwright-cli/scripts/parallel_run_manifest.py --help
```

这份 JSON 里：

- `workers[*]` 给浏览器 worker 用
- `documents[*]` 给 MinerU worker 用

### 阶段 2: MinerU worker

- 读取队列
- URL 多时优先 batch
- 本地文件多时优先 `/file-urls/batch`
- 把 `task_id` 或 `batch_id` 回写到任务表

### 阶段 3: 轮询和清洗

- 用少量 worker 轮询，不要每个 agent 自己猛轮询
- 下载结果 zip 到各自 `output_dir`
- 逐文档调用 `scripts/mineru_to_markdown.py` 清洗

### 阶段 4: 验证或回归

- 如需 UI 验证，再由新的浏览器 worker 读取产出的 markdown 或资源目录
- 仍然保持 `one worker = one session/profile/artifact dir`
