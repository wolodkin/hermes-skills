#!/usr/bin/env python3
"""Phase 4: read-only queries on a collection DataFrame."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    apply_query,
    emit_error,
    emit_json,
    get_collection,
    load_config,
    load_dataframe,
    load_state,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query a datacurator collection")
    parser.add_argument("--collection", required=True)
    parser.add_argument("--where", default=None, help="pandas query expression")
    parser.add_argument("--select", default=None, help="Comma-separated columns")
    parser.add_argument("--groupby", default=None)
    parser.add_argument("--agg", default=None, help='count or JSON e.g. {"Taxon":"nunique"}')
    parser.add_argument("--count-only", action="store_true")
    parser.add_argument("--distinct", default=None, help="Column for value_counts")
    parser.add_argument("--nulls", default=None, help="Column to list null/empty rows")
    parser.add_argument("--invalid-coords", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    try:
        cfg = load_config()
        qcfg = cfg.get("query", {})
        limit = args.limit or int(qcfg.get("default_limit", 100))
        max_limit = int(qcfg.get("max_limit", 1000))
        limit = min(limit, max_limit)

        state = load_state()
        if not state.get("collections"):
            emit_error("No collections in state. Run discover_collections.py first.")
        col = get_collection(state, args.collection)
        df = load_dataframe(col)
        select = [c.strip() for c in args.select.split(",")] if args.select else None

        result = apply_query(
            df,
            where=args.where,
            select=select,
            groupby=args.groupby,
            agg=args.agg,
            count_only=args.count_only,
            distinct=args.distinct,
            nulls=args.nulls,
            invalid_coords=args.invalid_coords,
            limit=limit,
        )
        emit_json({"ok": True, "collection": args.collection, **result})
    except KeyError as e:
        emit_error(str(e))
    except Exception as e:
        emit_error(str(e))


if __name__ == "__main__":
    main()
