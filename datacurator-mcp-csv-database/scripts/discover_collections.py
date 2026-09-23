#!/usr/bin/env python3
"""Discover Senckenberg collection folders (one stem-matched .csv + .txt per folder)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    discover_collections,
    emit_error,
    emit_json,
    load_config,
    load_state,
    save_state,
)


def main() -> None:
    try:
        cfg = load_config()
        root = Path(cfg["csv_source_folder_global_path"])
        result = discover_collections(root)
        state = load_state()
        state["source_root"] = result["source_root"]
        state["collections"] = result["collections"]
        state["last_discovery_at"] = result.get("discovered_at")
        state["discovery_errors"] = result.get("errors", [])
        save_state(state)
        emit_json(result)
    except SystemExit:
        raise
    except Exception as e:
        emit_error(str(e))


if __name__ == "__main__":
    main()
