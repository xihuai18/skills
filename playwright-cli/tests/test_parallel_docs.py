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
        self.assertIn("references/parallel-and-sessions.md", text)
        self.assertIn("scripts/parallel_run_manifest.py", text)

        self.assertLess(
            text.index("## Parallel safety for multi-agent work"),
            text.index("## Quick start"),
        )

    def test_parallel_reference_covers_isolation_and_handoff(self):
        text = (ROOT / "references" / "parallel-and-sessions.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("默认假设你已经读过 `SKILL.md` 里的并行硬规则", text)
        self.assertIn("`PLAYWRIGHT_CLI_SESSION`", text)
        self.assertIn("`state-save`", text)
        self.assertIn("close-all", text)
        self.assertIn("parallel_run_manifest.py", text)
        self.assertIn("session   = pw-<tool>-<run_id>-<agent_id>", text)
        self.assertIn("协调器根据自己分配的前缀逐个关闭自己的 session", text)
        self.assertIn('"profile_dir": "./tmp/playwright/run42/a1/profile"', text)


if __name__ == "__main__":
    unittest.main()
