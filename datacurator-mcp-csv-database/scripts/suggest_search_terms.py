#!/usr/bin/env python3
"""Suggest multilingual search terms and a SQL LIKE clause (no CSV reads)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import DEFAULT_TEXT_COLUMNS, emit_error, emit_json  # noqa: E402

# Minimal expansion map; agent may add more stems.
EXPANSIONS: dict[str, list[str]] = {
    "holz": ["Holz", "wood", "lign", "lignu", "xyl", "lignum"],
    "wood": ["wood", "Holz", "lign", "lignu", "xyl"],
    "wasser": ["Wasser", "water", "aqua", "aquat", "hydro"],
    "water": ["water", "Wasser", "aqua", "aquat", "hydro"],
    "deutschland": ["Deutschland", "Germany", "Germania"],
    "germany": ["Germany", "Deutschland", "Germania"],
    "hessen": ["Hessen", "Hesse"],
    "algen": ["Algae", "algae", "alg", "phyc", "Algen"],
    "algae": ["algae", "Algae", "alg", "phyc", "Algen"],
    "holotyp": ["Holotypus", "holotyp", "isotyp", "syntyp", "paratyp", "Typus"],
}


def _escape_like(term: str) -> str:
    return term.replace("'", "''").replace("%", "\\%").replace("_", "\\_")


def _unique_terms(term: str, lang: str) -> list[str]:
    key = term.strip().lower()
    found: list[str] = [term.strip()]
    if key in EXPANSIONS:
        found.extend(EXPANSIONS[key])
    else:
        for k, vals in EXPANSIONS.items():
            if key in k or k in key:
                found.extend(vals)
    seen: set[str] = set()
    out: list[str] = []
    for t in found:
        low = t.lower()
        if low not in seen and t.strip():
            seen.add(low)
            out.append(t.strip())
    if lang == "de" and term.strip() not in out:
        out.insert(0, term.strip())
    return out


def build_sql_like(
    terms: list[str],
    columns: list[str],
    table_name: str = "TABLE",
) -> str:
    patterns = [f"%{_escape_like(t)}%" for t in terms]
    col_clauses: list[str] = []
    for col in columns:
        col_q = f'"{col}"'
        or_parts = [f"LOWER({col_q}) LIKE LOWER('{p}')" for p in patterns]
        col_clauses.append("(" + " OR ".join(or_parts) + ")")
    where = " OR ".join(col_clauses)
    return (
        f"SELECT \"AQUiLA-ID\", \"Taxon\", \"Fundortbeschreibung\" "
        f"FROM {table_name} WHERE ({where}) LIMIT 100"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Suggest SQL LIKE search terms")
    parser.add_argument("--term", required=True, help="User search concept")
    parser.add_argument("--lang", default="de", help="User language code (de, en, …)")
    parser.add_argument(
        "--table",
        default="annotated_02",
        help="SQLite table name for example SQL",
    )
    parser.add_argument(
        "--columns",
        default=",".join(DEFAULT_TEXT_COLUMNS[:8]),
        help="Comma-separated column names",
    )
    args = parser.parse_args()

    try:
        cols = [c.strip() for c in args.columns.split(",") if c.strip()]
        terms = _unique_terms(args.term, args.lang)
        payload = {
            "ok": True,
            "term": args.term,
            "lang": args.lang,
            "terms": terms,
            "columns": cols,
            "sql_example": build_sql_like(terms, cols, args.table),
            "mcp_hint": (
                "Call execute_sql_query with your SQL and an explicit limit. "
                "Adjust table name from list_loaded_tables / collection table_name."
            ),
        }
        emit_json(payload)
    except SystemExit:
        raise
    except Exception as e:
        emit_error(str(e))


if __name__ == "__main__":
    main()
