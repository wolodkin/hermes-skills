#!/usr/bin/env python3
"""Phase 3: diverse sample rows from a collection."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    diverse_sample,
    emit_error,
    emit_json,
    get_collection,
    load_config,
    load_dataframe_for_collection,
    load_state,
    save_state,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sample diverse rows from a collection")
    parser.add_argument("--collection", required=True, help="Collection folder name")
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Number of sample rows (default from config)",
    )
    args = parser.parse_args()

    try:
        cfg = load_config()
        state = load_state()
        if not state.get("collections"):
            emit_error("No collections in state. Run discover_collections.py first.")
        col = get_collection(state, args.collection)
        n = args.n or int(cfg.get("profiling", {}).get("sample_rows_default", 8))
        df = load_dataframe_for_collection(col, cfg, sample_only=True)
        sample = diverse_sample(df, n)
        state.setdefault("samples", {})[args.collection] = sample
        state["samples_updated_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        emit_json({"ok": True, "collection": args.collection, **sample})
    except KeyError as e:
        emit_error(str(e))
    except Exception as e:
        emit_error(str(e))


if __name__ == "__main__":
    main()
