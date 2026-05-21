#!/usr/bin/env python3
"""Build enriched system prompt from template + discovery/profile/sample state."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    COLLECTIONS_MARKER,
    discover_collections,
    diverse_sample,
    emit_error,
    format_collections_block,
    get_collection,
    is_large_csv,
    load_config,
    load_dataframe_for_collection,
    load_state,
    profile_collection_csv,
    save_state,
)
from pathlib import Path


def _run_script(name: str) -> None:
    script = Path(__file__).resolve().parent / name
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True)


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
        if not result.get("collections"):
            emit_error(
                "No collections found. Check csv_source_folder_global_path in config.json."
            )
        save_state(state)
    return state


def _ensure_profile(cfg: dict, state: dict, name: str) -> dict:
    profiles = state.setdefault("profiles", {})
    if name not in profiles:
        col = get_collection(state, name)
        profiles[name] = profile_collection_csv(Path(col["csv_path"]), cfg)
        save_state(state)
    return profiles[name]


def _ensure_sample(cfg: dict, state: dict, name: str) -> dict:
    samples = state.setdefault("samples", {})
    if name not in samples:
        col = get_collection(state, name)
        n = int(cfg.get("profiling", {}).get("prompt_sample_rows", 3))
        df = load_dataframe_for_collection(col, cfg, sample_only=True)
        samples[name] = diverse_sample(df, n)
        if is_large_csv(Path(col["csv_path"]), cfg):
            samples[name]["sample_scope"] = "from_head_or_profile_sample_rows_not_full_file"
        save_state(state)
    return samples[name]


def build_prompt(cfg: dict, refresh: bool = False) -> str:
    tmpl_path = Path(cfg["prompt_template_path"])
    if not tmpl_path.is_file():
        emit_error(f"Prompt template not found: {tmpl_path}")

    template = tmpl_path.read_text(encoding="utf-8")
    if COLLECTIONS_MARKER not in template:
        emit_error(f"Template must contain {COLLECTIONS_MARKER}")

    state = load_state()
    if refresh:
        state.pop("profiles", None)
        state.pop("samples", None)

    state = _ensure_discovery(cfg, state)
    profiles: dict = {}
    samples: dict = {}

    for col in state["collections"]:
        name = col["name"]
        profiles[name] = _ensure_profile(cfg, state, name)
        samples[name] = _ensure_sample(cfg, state, name)

    block = format_collections_block(state["collections"], profiles, samples, cfg)
    return template.replace(COLLECTIONS_MARKER, block)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build datacurator system prompt")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Recompute profiles and samples",
    )
    args = parser.parse_args()

    try:
        cfg = load_config()
        prompt = build_prompt(cfg, refresh=args.refresh)
        max_chars = int(cfg.get("prompt", {}).get("max_total_chars", 2_097_152))
        if len(prompt) > max_chars:
            prompt = prompt[: max_chars - 80] + "\n…\n# prompt truncated to prompt.max_total_chars (~2 MiB)\n"
            print(
                f"warning: prompt truncated to {max_chars} chars (~2 MiB cap)",
                file=sys.stderr,
            )
        sys.stdout.write(prompt)
    except SystemExit:
        raise
    except Exception as e:
        emit_error(str(e))


if __name__ == "__main__":
    main()
