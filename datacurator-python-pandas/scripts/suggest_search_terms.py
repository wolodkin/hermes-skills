#!/usr/bin/env python3
"""Suggest English/Latin search variants and a pandas where-pattern for query_collection.py."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Curated expansions: lowercase key -> extra EN/LA stems (not exhaustive).
TERM_EXPANSIONS: dict[str, list[str]] = {
    "holz": ["wood", "lign", "lignu", "xyl", "timber"],
    "wasser": ["water", "aqua", "aquat", "hydro", "marine", "lake", "river"],
    "moos": ["moss", "musc", "bryoph"],
    "pilz": ["fungus", "fungi", "myco", "mycet"],
    "alge": ["alga", "algae", "phyc", "protist"],
    "holzsubstrat": ["wood", "lign", "xyl", "substrat"],
    "typ": ["typus", "holotyp", "isotyp", "syntyp", "paratyp", "lectotyp"],
    "holotyp": ["holotypus", "holotype"],
    "deutschland": ["germany", "germania", "deutschland"],
    "island": ["iceland", "island", "isl"],
}

DEFAULT_SEARCH_COLUMNS = [
    "Taxon",
    "Familie",
    "Synonyme",
    "Taxonomie",
    "Substrat",
    "Habitat",
    "Fundortbeschreibung",
    "Bemerkung",
    "Bemerkung zum Organismus",
    "Endwirt",
    "Zwischenwirt",
]

REGEX_SPECIAL = re.compile(r"[.^$*+?()[\]{}|\\]")


def escape_regex(term: str) -> str:
    return REGEX_SPECIAL.sub(lambda m: "\\" + m.group(0), term)


def expand_term(term: str, lang: str | None) -> list[str]:
    raw = term.strip()
    if not raw:
        return []
    variants: set[str] = {raw, raw.lower()}
    if raw.lower() != raw:
        variants.add(raw.lower())
    key = raw.lower()
    if key in TERM_EXPANSIONS:
        variants.update(TERM_EXPANSIONS[key])
    return sorted(variants, key=len)


def build_or_pattern(terms: list[str]) -> str:
    escaped = [escape_regex(t) for t in terms if t]
    return "|".join(escaped)


def build_where_clause(columns: list[str], pattern: str) -> str:
    safe = pattern.replace("'", "\\'")
    parts = [
        f"{col}.str.contains('{safe}', case=False, na=False)" for col in columns
    ]
    if len(parts) == 1:
        return parts[0]
    return "(" + " | ".join(parts) + ")"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Suggest EN/LA search terms and a query_collection --where pattern"
    )
    parser.add_argument("--term", required=True, help="User search concept")
    parser.add_argument(
        "--lang",
        default=None,
        help="User language hint (de, en, …); term is always kept",
    )
    parser.add_argument(
        "--columns",
        default=None,
        help="Comma-separated columns (default: common text fields)",
    )
    args = parser.parse_args()

    terms = expand_term(args.term, args.lang)
    pattern = build_or_pattern(terms)
    columns = (
        [c.strip() for c in args.columns.split(",") if c.strip()]
        if args.columns
        else DEFAULT_SEARCH_COLUMNS
    )
    where = build_where_clause(columns, pattern)

    print(
        json.dumps(
            {
                "ok": True,
                "input_term": args.term,
                "lang": args.lang,
                "terms": terms,
                "where_or_pattern": pattern,
                "columns": columns,
                "where_clause": where,
                "usage": (
                    'python3 scripts/query_collection.py --collection "NAME" '
                    f'--where \'{where}\' --limit 50'
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
