#!/usr/bin/env python3
"""Phase 1: discover collection folders (one CSV + one TXT each)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
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
        state["last_discovery_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        emit_json(result, 0 if result.get("ok") else 1)
    except Exception as e:
        emit_error(str(e))


if __name__ == "__main__":
    main()
