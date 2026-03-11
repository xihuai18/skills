import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "parallel_run_manifest.py"


def load_module():
    spec = importlib.util.spec_from_file_location("parallel_run_manifest", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = load_module()


class ParallelRunManifestTests(unittest.TestCase):
    def test_build_manifest_generates_unique_worker_resources(self):
        args = type(
            "Args",
            (),
            {
                "run_id": "run42",
                "tool": "opencode",
                "agent_ids": ["a1", "a2"],
                "source": ["https://example.com/a.pdf", "./downloads/b.pdf"],
                "output": None,
            },
        )()

        manifest = mod.build_manifest(args)

        self.assertEqual(manifest["run_id"], "run42")
        self.assertEqual(len(manifest["workers"]), 2)
        self.assertEqual(manifest["workers"][0]["session"], "pw-opencode-run42-a1")
        self.assertEqual(
            manifest["workers"][1]["profile_dir"], "./tmp/playwright/run42/a2/profile"
        )
        self.assertEqual(len(manifest["documents"]), 2)
        self.assertEqual(manifest["documents"][0]["data_id"], "run42-doc-001")
        self.assertEqual(
            manifest["documents"][1]["output_dir"], "./tmp/mineru/run42/run42-doc-002"
        )

    def test_build_manifest_can_be_saved_as_json_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "plan.json"
            args = type(
                "Args",
                (),
                {
                    "run_id": "run42",
                    "tool": "opencode",
                    "agent_ids": ["a1"],
                    "source": ["https://example.com/a.pdf"],
                    "output": output,
                },
            )()

            manifest = mod.build_manifest(args)
            text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
            output.write_text(text, encoding="utf-8")

            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                saved["workers"][0]["download_dir"],
                "./tmp/playwright/run42/a1/downloads",
            )
            self.assertEqual(
                saved["documents"][0]["job_file"],
                "./tmp/mineru/run42/run42-doc-001/job.json",
            )


if __name__ == "__main__":
    unittest.main()
