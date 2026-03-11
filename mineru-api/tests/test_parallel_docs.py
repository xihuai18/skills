import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MineruParallelDocsTests(unittest.TestCase):
    def test_skill_mentions_parallel_orchestration(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## Parallel and batch orchestration", text)
        self.assertIn("`data_id`", text)
        self.assertIn("轮询间隔默认 `3-10` 秒", text)
        self.assertIn("`playwright-cli` worker 负责登录、找链接、下载文件", text)
        self.assertIn("playwright-cli/scripts/parallel_run_manifest.py", text)

    def test_parallel_reference_covers_queue_and_cleanup_shape(self):
        text = (ROOT / "references" / "parallel-orchestration.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("`source -> data_id -> output_dir`", text)
        self.assertIn("URL 多时优先 batch", text)
        self.assertIn("scripts/mineru_to_markdown.py", text)
        self.assertIn("不要把浏览器 live session 当作 MinerU worker 的输入依赖", text)
        self.assertIn("workers[*]", text)
        self.assertIn("documents[*]", text)


if __name__ == "__main__":
    unittest.main()
