#!/usr/bin/env python3
"""Build datacurator system prompt from template + collection descriptions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    COLLECTIONS_MARKER,
    discover_collections,
    emit_error,
    format_collections_block,
    load_config,
    load_state,
    save_state,
)


def _ensure_discovery(cfg: dict, state: dict) -> dict:
    root = Path(cfg["csv_source_folder_global_path"])
    need = (
        not state.get("collections")
        or state.get("source_root") != str(root.resolve())
    )
    if need:
        result = discover_collections(root)
        state["source_root"] = result["source_root"]
        state["collections"] = result["collections"]
        state["last_discovery_at"] = result.get("discovered_at")
        state["discovery_errors"] = result.get("errors", [])
        if not result.get("collections"):
            emit_error(
                "No collections found. Check csv_source_folder_global_path in config.json."
            )
        save_state(state)
    return state


def build_prompt(cfg: dict) -> str:
    tmpl_path = Path(cfg["prompt_template_path"])
    if not tmpl_path.is_file():
        emit_error(f"Prompt template not found: {tmpl_path}")

    template = tmpl_path.read_text(encoding="utf-8")
    if COLLECTIONS_MARKER not in template:
        emit_error(f"Template must contain {COLLECTIONS_MARKER}")

    state = _ensure_discovery(cfg, load_state())
    block = format_collections_block(state["collections"], cfg)
    return template.replace(COLLECTIONS_MARKER, block)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build datacurator system prompt")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-run discovery before building prompt",
    )
    args = parser.parse_args()

    try:
        cfg = load_config()
        if args.refresh:
            root = Path(cfg["csv_source_folder_global_path"])
            result = discover_collections(root)
            state = load_state()
            state["source_root"] = result["source_root"]
            state["collections"] = result["collections"]
            state["last_discovery_at"] = result.get("discovered_at")
            state["discovery_errors"] = result.get("errors", [])
            save_state(state)

        prompt = build_prompt(cfg)
        max_chars = int(cfg.get("prompt", {}).get("max_total_chars", 2_097_152))
        if len(prompt) > max_chars:
            prompt = prompt[: max_chars - 80] + "\n…\n# prompt truncated to prompt.max_total_chars\n"
            print(
                f"warning: prompt truncated to {max_chars} chars",
                file=sys.stderr,
            )
        sys.stdout.write(prompt)
    except SystemExit:
        raise
    except Exception as e:
        emit_error(str(e))


if __name__ == "__main__":
    main()
