# OpenCode Skills Collection

Reusable, testable OpenCode skills for real-world agent workflows.

这个目录已经按“可单独开源”的方向整理，放的是可直接复用、可改写、可测试的 OpenCode skills。

当前包含：

- `mineru-api`：MinerU 云解析 API + markdown 清洗脚本
- `playwright-cli`：`@playwright/cli` 浏览器自动化工作流

## 目录结构

```text
skills/
  README.md
  .gitignore
  mineru-api/
    SKILL.md
    .gitignore
    .env.mineru.local.example
    scripts/
    tests/
  playwright-cli/
    SKILL.md
    references/
    tests/
```

## How to install in OpenCode

这个目录默认不会被 OpenCode 自动扫描。

要让 OpenCode 读取这里的 skill，有两种常用方式：

## 方式 1：在 `opencode.json` 里加入 `skills.paths`

```jsonc
{
  "skills": {
    "paths": ["./skills"],
  },
}
```

## 方式 2：把某个 skill 复制到项目默认目录

例如：

```text
.opencode/skills/mineru-api/SKILL.md
.opencode/skills/playwright-cli/SKILL.md
```

## 当前包含的 skill

- `skills/mineru-api/SKILL.md`：MinerU 云端文档解析 API 的调用与结果处理说明
- `skills/mineru-api/scripts/mineru_to_markdown.py`：把本地 PDF / 远程 PDF / 原始 ZIP 整理成干净 markdown + `assets/`
- `skills/playwright-cli/SKILL.md`：`playwright-cli` 的安装、页面交互、会话与测试工作流说明

## Open source notes

- 本目录不包含真实 API key 或其他 secret
- `skills/mineru-api/.env.mineru.local` 只用于本地开发，已被忽略
- Python 缓存和其他本地生成文件已通过 `skills/.gitignore` 排除
- 如果你把本目录拆成独立仓库，建议保留当前目录结构不变
- License: `MIT`, see `skills/LICENSE`

## Suggested repository metadata

- Repository name: `opencode-skills`
- Description: `Reusable OpenCode skills for MinerU and playwright-cli workflows`
- Suggested topics: `opencode`, `skills`, `agent`, `playwright`, `mineru`, `automation`

## 使用前置条件

- `mineru-api` 需要 MinerU Bearer Token
- `playwright-cli` 需要先安装 `@playwright/cli`

推荐的 MinerU Token 存放方式：

- `MINERU_API_TOKEN`
- `MINERU_API_TOKEN_FILE`
- `skills/mineru-api/.env.mineru.local`
- `~/.config/mineru/token`
- 未入库的 `.env.mineru.local` 或 `.env.local`

不要把 Token 提交进仓库。

如果你正在直接使用本仓库里的 MinerU skill，优先把 token 放到：`skills/mineru-api/.env.mineru.local`

这个目录里现在已经带了：

- `skills/mineru-api/.gitignore`
- `skills/mineru-api/.env.mineru.local.example`

建议复制模板后再填写：

```bash
cp skills/mineru-api/.env.mineru.local.example skills/mineru-api/.env.mineru.local
```

## 测试

MinerU helper 自带一个最小单元测试：

```bash
python -m unittest "skills/mineru-api/tests/test_mineru_to_markdown.py"
```

它会验证：

- 资源按阅读顺序重命名
- markdown 引用被同步改写
- 资源文件和 `manifest.json` 被正确生成

Playwright skill 也带了一个最小 smoke test：

```bash
python -m unittest "skills/playwright-cli/tests/test_playwright_cli_smoke.py"
```

它会验证：

- `playwright-cli` 已安装且帮助信息正常
- 能打开页面、生成 snapshot、读取标题并关闭浏览器

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
```

如果你想直接使用上游仓库自带的 Playwright skill，也可以执行：

```bash
playwright-cli install --skills
```

但如果你希望 skill 内容由本仓库统一维护，还是建议使用这里的版本，并通过 `skills.paths` 暴露给 OpenCode。

## Publish checklist

如果你准备把 `skills/` 单独开源，至少确认：

- `SKILL.md` frontmatter 里的 `name` 与目录名一致
- `mineru-api` 的本地 token 文件没有被带上
- 两个测试都能通过
- README、license、repo 描述已经补齐
