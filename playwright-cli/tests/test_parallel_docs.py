import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PlaywrightParallelDocsTests(unittest.TestCase):
    def test_skill_mentions_critical_parallel_rules(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## Parallel safety for multi-agent work", text)
        self.assertIn("这是默认且优先的规则", text)
        self.assertIn("一个 worker 只拥有一个自己的 session", text)
        self.assertIn("不要对共享环境执行 `close-all` 或 `kill-all`", text)
        self.assertIn("references/coordinator-template.md", text)
        self.assertIn("references/README.md", text)
        self.assertIn("scripts/parallel_run_manifest.py", text)

        self.assertLess(
            text.index("## Parallel safety for multi-agent work"),
            text.index("## Quick start"),
        )

    def test_parallel_reference_covers_isolation_and_handoff(self):
        text = (ROOT / "references" / "parallel-workflows.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("一个 worker 一个 session", text)
        self.assertIn("`PLAYWRIGHT_CLI_SESSION`", text)
        self.assertIn("`state-save`", text)
        self.assertIn("close-all", text)
        self.assertIn("parallel_run_manifest.py", text)

    def test_coordinator_template_covers_unique_resources(self):
        text = (ROOT / "references" / "coordinator-template.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("session  = pw-<tool>-<run_id>-<agent_id>", text)
        self.assertIn("worker 只能关闭自己的 session", text)
        self.assertIn("每个 worker 的 profile 路径是否唯一", text)
        self.assertIn("parallel_run_manifest.py", text)


if __name__ == "__main__":
    unittest.main()
