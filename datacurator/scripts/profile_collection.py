#!/usr/bin/env python3
"""Phase 2: profile a collection CSV."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    emit_error,
    emit_json,
    get_collection,
    load_config,
    load_state,
    profile_collection_csv,
    save_state,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile a datacurator collection")
    parser.add_argument("--collection", required=True, help="Collection folder name")
    args = parser.parse_args()

    try:
        cfg = load_config()
        state = load_state()
        if not state.get("collections"):
            emit_error("No collections in state. Run discover_collections.py first.")
        col = get_collection(state, args.collection)
        profile = profile_collection_csv(Path(col["csv_path"]), cfg)
        state.setdefault("profiles", {})[args.collection] = profile
        state["profiles_updated_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        emit_json({"ok": True, "collection": args.collection, "profile": profile})
    except KeyError as e:
        emit_error(str(e))
    except Exception as e:
        emit_error(str(e))


if __name__ == "__main__":
    main()
