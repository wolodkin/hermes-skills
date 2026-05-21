"""Shared utilities for the datacurator Hermes skill."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SKILL_DIR = Path(__file__).resolve().parent.parent
STATE_PATH = Path.home() / ".hermes" / "state" / "datacurator.json"
COLLECTIONS_MARKER = "{{COLLECTIONS_BLOCK}}"
DEFAULT_KEY_COLUMNS = [
    "AQUiLA-ID",
    "Taxon",
    "Barcode",
    "Familie",
    "Fundortbeschreibung",
    "Typus",
    "Sammler",
    "Katalognummer",
]
FORBIDDEN_QUERY_TOKENS = re.compile(
    r"\b(import|exec|eval|open|__|os\.|sys\.|subprocess|globals|locals|compile|getattr|setattr|delattr)\b",
    re.IGNORECASE,
)


def skill_dir() -> Path:
    return SKILL_DIR


def load_config() -> dict[str, Any]:
    path = SKILL_DIR / "config.json"
    if not path.is_file():
        raise FileNotFoundError(f"config.json not found at {path}")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    root = cfg.get("csv_source_folder_global_path", "")
    if root and not Path(root).is_absolute():
        cfg["csv_source_folder_global_path"] = str((SKILL_DIR / root).resolve())
    tmpl = cfg.get("prompt_template", "./prompt_template.txt")
    if tmpl and not Path(tmpl).is_absolute():
        cfg["prompt_template_path"] = str((SKILL_DIR / tmpl).resolve())
    else:
        cfg["prompt_template_path"] = tmpl
    return cfg


def load_state() -> dict[str, Any]:
    if not STATE_PATH.is_file():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def emit_json(payload: dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


def emit_error(message: str, exit_code: int = 1) -> None:
    emit_json({"ok": False, "error": message}, exit_code)


def discover_collections(source_root: Path) -> dict[str, Any]:
    if not source_root.is_dir():
        return {
            "ok": False,
            "source_root": str(source_root),
            "collections": [],
            "errors": [f"Source folder does not exist: {source_root}"],
        }

    collections: list[dict[str, Any]] = []
    errors: list[str] = []

    for folder in sorted(source_root.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        csv_files = sorted(folder.glob("*.csv"))
        txt_files = sorted(folder.glob("*.txt"))
        name = folder.name

        if len(csv_files) != 1 or len(txt_files) != 1:
            errors.append(
                f"{name}: expected exactly one .csv and one .txt, "
                f"found {len(csv_files)} csv and {len(txt_files)} txt"
            )
            continue

        description = txt_files[0].read_text(encoding="utf-8").strip()
        csv_path = csv_files[0].resolve()
        size_mb = round(csv_path.stat().st_size / (1024 * 1024), 2)
        collections.append(
            {
                "name": name,
                "folder": str(folder.resolve()),
                "csv_path": str(csv_path),
                "txt_path": str(txt_files[0].resolve()),
                "description": description,
                "file_size_mb": size_mb,
            }
        )

    return {
        "ok": len(errors) == 0 or len(collections) > 0,
        "source_root": str(source_root.resolve()),
        "collections": collections,
        "errors": errors,
    }


def _read_csv_with_sep(csv_path: Path, **kwargs: Any) -> pd.DataFrame:
    for sep in (",", ";", "\t"):
        try:
            df = pd.read_csv(csv_path, sep=sep, low_memory=False, dtype=str, **kwargs)
            if df.shape[1] > 1:
                return df
        except Exception:
            continue
    return pd.read_csv(csv_path, low_memory=False, dtype=str, **kwargs)


def read_csv_ro(csv_path: Path) -> pd.DataFrame:
    return _read_csv_with_sep(csv_path)


def read_csv_sample(csv_path: Path, max_rows: int) -> pd.DataFrame:
    return _read_csv_with_sep(csv_path, nrows=max_rows)


def count_csv_rows(csv_path: Path) -> int:
    with csv_path.open("rb") as f:
        lines = sum(1 for _ in f)
    return max(0, lines - 1)


def csv_file_size_mb(csv_path: Path) -> float:
    return csv_path.stat().st_size / (1024 * 1024)


def is_large_csv(csv_path: Path, cfg: dict[str, Any]) -> bool:
    threshold = float(cfg.get("profiling", {}).get("large_file_threshold_mb", 2))
    return csv_file_size_mb(csv_path) >= threshold


def load_dataframe_for_collection(
    collection: dict[str, Any], cfg: dict[str, Any] | None = None, *, sample_only: bool = False
) -> pd.DataFrame:
    path = Path(collection["csv_path"])
    if sample_only:
        profiling = (cfg or {}).get("profiling", {})
        cap = int(profiling.get("profile_sample_rows", 20_000))
        if is_large_csv(path, cfg or {}):
            return read_csv_sample(path, cap)
    return read_csv_ro(path)


def load_dataframe(collection: dict[str, Any]) -> pd.DataFrame:
    return read_csv_ro(Path(collection["csv_path"]))


def profile_collection_csv(csv_path: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    mb = round(csv_file_size_mb(csv_path), 2)
    large = is_large_csv(csv_path, cfg)
    profiling = cfg.get("profiling", {})
    if not large:
        df = read_csv_ro(csv_path)
        profile = profile_dataframe(df, cfg)
        profile["file_size_mb"] = mb
        profile["large_file"] = False
        profile["profile_mode"] = "full"
        return profile

    row_count = count_csv_rows(csv_path)
    sample_n = min(int(profiling.get("profile_sample_rows", 20_000)), row_count)
    df = read_csv_sample(csv_path, sample_n)
    profile = profile_dataframe(df, cfg)
    profile["row_count"] = row_count
    profile["file_size_mb"] = mb
    profile["large_file"] = True
    profile["profile_mode"] = "sampled"
    profile["profile_sample_rows"] = sample_n
    profile["stats_approximate"] = sample_n < row_count
    return profile


def get_collection(state: dict[str, Any], name: str) -> dict[str, Any]:
    for col in state.get("collections", []):
        if col["name"] == name:
            return col
    raise KeyError(f"Collection not found: {name}")


def load_dataframe(collection: dict[str, Any]) -> pd.DataFrame:
    return read_csv_ro(Path(collection["csv_path"]))


def profile_dataframe(df: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    profiling = cfg.get("profiling", {})
    max_top = int(profiling.get("max_top_values", 10))
    high_null_pct = float(profiling.get("high_null_threshold_pct", 90))

    columns_meta: list[dict[str, Any]] = []
    categorical_top: dict[str, list[dict[str, Any]]] = {}
    numeric_summary: dict[str, dict[str, Any]] = {}
    empty_columns: list[str] = []
    high_null_columns: list[str] = []
    json_like_columns: list[str] = []

    for col in df.columns:
        series = df[col]
        null_mask = series.isna() | (series.astype(str).str.strip() == "")
        null_count = int(null_mask.sum())
        non_null = len(df) - null_count
        null_pct = round(100.0 * null_count / len(df), 2) if len(df) else 0.0
        n_unique = int(series.nunique(dropna=True))

        col_meta: dict[str, Any] = {
            "name": col,
            "dtype": str(series.dtype),
            "null_count": null_count,
            "null_pct": null_pct,
            "non_null_count": non_null,
            "n_unique": n_unique,
        }
        if non_null:
            str_lens = series.astype(str).str.len()
            col_meta["max_str_len"] = int(str_lens.max())
        columns_meta.append(col_meta)

        if null_pct >= 100:
            empty_columns.append(col)
        elif null_pct >= high_null_pct:
            high_null_columns.append(col)

        if non_null:
            sample_vals = series[~null_mask].astype(str).head(50)
            brace_ratio = (
                sample_vals.str.contains(r"\{", regex=True).sum() / len(sample_vals)
            )
            if brace_ratio > 0.3:
                json_like_columns.append(col)

        if 0 < n_unique <= max_top:
            vc = series[~null_mask].value_counts().head(max_top)
            categorical_top[col] = [
                {"value": str(v), "count": int(c)} for v, c in vc.items()
            ]

        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().sum() > 0:
            numeric_summary[col] = {
                "min": float(numeric.min()),
                "max": float(numeric.max()),
                "mean": round(float(numeric.mean()), 4),
            }

    duplicate_rows = int(df.duplicated().sum())
    memory_bytes = int(df.memory_usage(deep=True).sum())

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": columns_meta,
        "numeric_summary": numeric_summary,
        "categorical_top_values": categorical_top,
        "duplicate_rows": duplicate_rows,
        "empty_columns": empty_columns,
        "high_null_columns": high_null_columns,
        "json_like_columns": json_like_columns,
        "memory_bytes": memory_bytes,
        "profiled_at": datetime.now(timezone.utc).isoformat(),
    }


def _row_fingerprint(row: pd.Series, active_cols: list[str]) -> tuple[str, ...]:
    parts: list[str] = []
    for col in active_cols:
        val = row.get(col, "")
        if pd.isna(val) or str(val).strip() in ("", "-", "nan"):
            parts.append("")
        else:
            s = str(val).strip()[:200]
            parts.append(s)
    return tuple(parts)


def _fingerprint_distance(a: tuple[str, ...], b: tuple[str, ...]) -> int:
    return sum(1 for x, y in zip(a, b) if x != y)


def diverse_sample(
    df: pd.DataFrame,
    n: int,
    key_columns: list[str] | None = None,
) -> dict[str, Any]:
    if len(df) == 0:
        return {"sample_rows": [], "columns_included": [], "method": "empty"}

    fill_rate = df.notna() & (df.astype(str).apply(lambda s: s.str.strip() != "-"))
    col_fill = fill_rate.mean()
    active_cols = [c for c in df.columns if col_fill.get(c, 0) > 0.3]
    if not active_cols:
        active_cols = list(df.columns[: min(10, len(df.columns))])

    prefer = key_columns or DEFAULT_KEY_COLUMNS
    display_cols = [c for c in prefer if c in df.columns]
    if len(display_cols) < 3:
        display_cols = active_cols[:8]

    non_null_counts = fill_rate.sum(axis=1)
    start_idx = int(non_null_counts.idxmax())
    selected_indices = [start_idx]
    fingerprints = [_row_fingerprint(df.loc[start_idx], active_cols)]

    remaining = [i for i in df.index if i != start_idx]

    while len(selected_indices) < n and remaining:
        best_idx = None
        best_dist = -1
        for idx in remaining:
            fp = _row_fingerprint(df.loc[idx], active_cols)
            min_dist = min(_fingerprint_distance(fp, s) for s in fingerprints)
            if min_dist > best_dist:
                best_dist = min_dist
                best_idx = idx
        if best_idx is None:
            break
        selected_indices.append(best_idx)
        fingerprints.append(_row_fingerprint(df.loc[best_idx], active_cols))
        remaining.remove(best_idx)

    rows = []
    for idx in selected_indices:
        row = df.loc[idx, display_cols]
        rows.append({k: ("" if pd.isna(v) else str(v)) for k, v in row.items()})

    return {
        "sample_rows": rows,
        "columns_included": display_cols,
        "method": "max_fill_start_then_max_min_distance",
        "n_requested": n,
        "n_returned": len(rows),
    }


def _truncate_cell(value: Any, max_len: int) -> str:
    s = "" if pd.isna(value) else str(value).strip()
    if len(s) <= max_len:
        return s.replace('"', "'")
    return s[: max_len - 1] + "…"


def profile_summary_text(profile: dict[str, Any], cfg: dict[str, Any] | None = None) -> str:
    parts = [
        f"{profile['row_count']} rows",
        f"{profile['column_count']} columns",
        f"{profile.get('file_size_mb', '?')} MB on disk",
    ]
    if profile.get("large_file"):
        parts.append("LARGE_FILE: use scripts only, never inline full CSV")
    if profile.get("profile_mode") == "sampled":
        parts.append(
            f"stats from first {profile.get('profile_sample_rows', '?')} rows (approximate)"
        )
    if profile.get("duplicate_rows"):
        parts.append(f"{profile['duplicate_rows']} duplicate rows")
    if profile.get("high_null_columns"):
        cols = profile["high_null_columns"][:5]
        suffix = "…" if len(profile["high_null_columns"]) > 5 else ""
        parts.append(f"high null: {', '.join(cols)}{suffix}")
    if profile.get("json_like_columns"):
        cols = profile["json_like_columns"][:3]
        parts.append(f"ontology/json-like: {', '.join(cols)}")

    profiling = (cfg or {}).get("profiling", {})
    max_cols = int(profiling.get("prompt_max_columns_listed", 53))
    col_names = [c["name"] for c in profile.get("columns", [])[:max_cols]]
    if col_names:
        parts.append("columns: " + ", ".join(col_names))

    key_cols = profiling.get("prompt_key_columns_for_top_values", DEFAULT_KEY_COLUMNS)
    tops = profile.get("categorical_top_values", {})
    for kc in key_cols:
        if kc in tops and tops[kc]:
            vals = ", ".join(f"{x['value']}({x['count']})" for x in tops[kc][:5])
            parts.append(f"top {kc}: {vals}")

    return "; ".join(parts)


def validate_where(expr: str, column_names: list[str]) -> None:
    if FORBIDDEN_QUERY_TOKENS.search(expr):
        raise ValueError("Query expression contains forbidden tokens")
    if "`" in expr:
        raise ValueError("Backticks are not allowed in query expressions")


def apply_query(
    df: pd.DataFrame,
    *,
    where: str | None = None,
    select: list[str] | None = None,
    groupby: str | None = None,
    agg: str | None = None,
    count_only: bool = False,
    distinct: str | None = None,
    nulls: str | None = None,
    invalid_coords: bool = False,
    limit: int = 100,
) -> dict[str, Any]:
    work = df.copy()
    column_names = list(work.columns)

    if where:
        validate_where(where, column_names)
        work = work.query(where, engine="python")

    if nulls:
        if nulls not in work.columns:
            raise ValueError(f"Unknown column: {nulls}")
        mask = work[nulls].isna() | (work[nulls].astype(str).str.strip().isin(("", "-")))
        work = work[mask]

    if invalid_coords:
        lat_cols = [c for c in ("Latitude", "Geographische Breite") if c in work.columns]
        lon_cols = [c for c in ("Longitude", "Geographische Länge") if c in work.columns]
        if lat_cols and lon_cols:
            lat = pd.to_numeric(work[lat_cols[0]], errors="coerce")
            lon = pd.to_numeric(work[lon_cols[0]], errors="coerce")
            bad = lat.isna() | lon.isna() | (lat.abs() > 90) | (lon.abs() > 180)
            work = work[bad]

    if distinct:
        if distinct not in work.columns:
            raise ValueError(f"Unknown column: {distinct}")
        vc = work[distinct].value_counts(dropna=False).head(limit)
        rows = [
            {"value": str(v), "count": int(c)} for v, c in vc.items()
        ]
        return {
            "mode": "distinct",
            "column": distinct,
            "rows": rows,
            "row_count": len(rows),
            "truncated": len(vc) >= limit,
        }

    if groupby:
        if groupby not in work.columns:
            raise ValueError(f"Unknown column: {groupby}")
        grouped = work.groupby(groupby, dropna=False)
        if agg == "count" or agg is None:
            result = grouped.size().reset_index(name="count")
        else:
            try:
                agg_spec = json.loads(agg)
            except json.JSONDecodeError:
                raise ValueError("agg must be 'count' or JSON like {\"Taxon\":\"nunique\"}")
            result = grouped.agg(agg_spec).reset_index()
        work = result

    if count_only:
        return {
            "mode": "count",
            "row_count": len(work),
            "rows": [],
            "truncated": False,
        }

    if select:
        cols = [c.strip() for c in select if c.strip()]
        missing = [c for c in cols if c not in work.columns]
        if missing:
            raise ValueError(f"Unknown columns: {missing}")
        work = work[cols]

    total = len(work)
    truncated = total > limit
    out = work.head(limit)
    rows = json.loads(out.to_json(orient="records", force_ascii=False))

    return {
        "mode": "rows",
        "rows": rows,
        "row_count": total,
        "truncated": truncated,
        "columns": list(out.columns),
    }


def format_collections_block(
    collections: list[dict[str, Any]],
    profiles: dict[str, Any],
    samples: dict[str, Any],
    cfg: dict[str, Any] | None = None,
) -> str:
    profiling = (cfg or {}).get("profiling", {})
    prompt_cfg = (cfg or {}).get("prompt", {})
    cell_max = int(profiling.get("prompt_sample_cell_max_len", 100))
    per_col_cap = int(profiling.get("prompt_max_chars_per_collection", 8_000))
    total_cap = int(prompt_cfg.get("max_total_chars", 2_097_152))

    blocks: list[str] = []
    total_len = 0

    for col in collections:
        name = col["name"]
        chunk_lines = [f'- name: "{name}"']
        if col.get("file_size_mb") is not None:
            chunk_lines.append(f'  file_size_mb: {col["file_size_mb"]}')
        desc = col.get("description", "").replace('"', '\\"')
        if len(desc) > 2000:
            desc = desc[:1999] + "…"
        chunk_lines.append(f'  description: "{desc}"')
        prof = profiles.get(name)
        if prof:
            summary = profile_summary_text(prof, cfg).replace('"', '\\"')
            chunk_lines.append(f'  profile_summary: "{summary}"')
        samp = samples.get(name)
        if samp and samp.get("sample_rows"):
            chunk_lines.append("  sample_rows:  # preview only — query scripts for facts")
            for row in samp["sample_rows"]:
                parts = [
                    f'"{k}": "{_truncate_cell(v, cell_max)}"' for k, v in row.items()
                ]
                chunk_lines.append(f"    - {{{', '.join(parts)}}}")

        chunk = "\n".join(chunk_lines)
        if len(chunk) > per_col_cap:
            chunk = chunk[: per_col_cap - 1] + "…"
        if total_len + len(chunk) > total_cap:
            chunk_lines_short = chunk_lines[:4]
            chunk_lines_short.append(
                '  note: "further collections omitted from prompt (max_total_chars); use discover_collections.py"'
            )
            blocks.append("\n".join(chunk_lines_short))
            break
        blocks.append(chunk)
        total_len += len(chunk)

    return "\n".join(blocks)
