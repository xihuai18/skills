#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path


SESSION_TEMPLATE = "pw-{tool}-{run_id}-{agent_id}"
PLAYWRIGHT_ROOT_TEMPLATE = "./tmp/playwright/{run_id}/{agent_id}"
MINERU_ROOT_TEMPLATE = "./tmp/mineru/{run_id}/{data_id}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a shared run manifest for parallel playwright-cli and MinerU workflows."
        )
    )
    parser.add_argument("--run-id", required=True, help="Stable run identifier.")
    parser.add_argument(
        "--tool",
        default="opencode",
        help="Tool name used in generated session names. Default: opencode.",
    )
    parser.add_argument(
        "--agent-id",
        action="append",
        dest="agent_ids",
        required=True,
        help="Worker identifier. Repeat for multiple workers, e.g. --agent-id a1 --agent-id a2.",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Document URL or local file path. Repeat to create MinerU jobs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the generated manifest JSON.",
    )
    return parser.parse_args()


def build_worker(run_id: str, tool: str, agent_id: str) -> dict[str, str]:
    root = PLAYWRIGHT_ROOT_TEMPLATE.format(run_id=run_id, agent_id=agent_id)
    return {
        "agent_id": agent_id,
        "session": SESSION_TEMPLATE.format(tool=tool, run_id=run_id, agent_id=agent_id),
        "root_dir": root,
        "profile_dir": f"{root}/profile",
        "artifact_dir": f"{root}/artifacts",
        "state_file": f"{root}/state.json",
        "download_dir": f"{root}/downloads",
    }


def build_document(run_id: str, source: str, index: int) -> dict[str, str | int]:
    data_id = f"{run_id}-doc-{index:03d}"
    output_dir = MINERU_ROOT_TEMPLATE.format(run_id=run_id, data_id=data_id)
    return {
        "index": index,
        "source": source,
        "data_id": data_id,
        "output_dir": output_dir,
        "job_file": f"{output_dir}/job.json",
        "raw_zip": f"{output_dir}/raw.zip",
        "raw_dir": f"{output_dir}/raw",
        "clean_markdown": f"{output_dir}/clean.md",
        "asset_dir": f"{output_dir}/assets",
        "manifest_file": f"{output_dir}/manifest.json",
    }


def build_manifest(args: argparse.Namespace) -> dict[str, object]:
    workers = [
        build_worker(args.run_id, args.tool, agent_id) for agent_id in args.agent_ids
    ]
    documents = [
        build_document(args.run_id, source, index)
        for index, source in enumerate(args.source, start=1)
    ]
    return {
        "run_id": args.run_id,
        "tool": args.tool,
        "workers": workers,
        "documents": documents,
    }


def main() -> int:
    args = parse_args()
    manifest = build_manifest(args)
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
