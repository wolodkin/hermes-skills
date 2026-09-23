"""Shared utilities for the datacurator Hermes skill (MCP csv-database)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
STATE_PATH = Path.home() / ".hermes" / "state" / "datacurator.json"
COLLECTIONS_MARKER = "{{COLLECTIONS_BLOCK}}"

DEFAULT_TEXT_COLUMNS = [
    "Taxon",
    "Familie",
    "Substrat",
    "Habitat",
    "Fundortbeschreibung",
    "Bemerkung",
    "Bemerkung zum Organismus",
    "Synonyme",
    "Adm. Einheit",
    "Administrative Einheit",
    "Taxonomie",
    "Kontinent",
]


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


def table_name_for_csv(csv_path: Path) -> str:
    """Match mcp-csv-database: stem with - and spaces -> _."""
    return csv_path.stem.replace("-", "_").replace(" ", "_")


def _pair_csv_txt(folder: Path) -> tuple[Path, Path] | str:
    csv_files = sorted(folder.glob("*.csv"))
    txt_files = sorted(folder.glob("*.txt"))
    if not csv_files or not txt_files:
        return (
            f"{folder.name}: need at least one .csv and one .txt "
            f"(found {len(csv_files)} csv, {len(txt_files)} txt)"
        )

    csv_by_stem = {f.stem: f for f in csv_files}
    txt_by_stem = {f.stem: f for f in txt_files}
    common = sorted(set(csv_by_stem) & set(txt_by_stem))
    csv_only = sorted(set(csv_by_stem) - set(txt_by_stem))
    txt_only = sorted(set(txt_by_stem) - set(csv_by_stem))

    if len(common) != 1:
        parts = [f"{folder.name}: expected exactly one matching csv/txt stem pair"]
        if len(common) > 1:
            parts.append(f"multiple pairs: {common}")
        if csv_only:
            parts.append(f"csv without txt: {csv_only}")
        if txt_only:
            parts.append(f"txt without csv: {txt_only}")
        if not common and not csv_only and not txt_only:
            parts.append(f"stems mismatch: csv={sorted(csv_by_stem)} txt={sorted(txt_by_stem)}")
        return "; ".join(parts)

    stem = common[0]
    return (csv_by_stem[stem], txt_by_stem[stem])


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

        paired = _pair_csv_txt(folder)
        if isinstance(paired, str):
            errors.append(paired)
            continue

        csv_path, txt_path = paired
        csv_path = csv_path.resolve()
        description = txt_path.read_text(encoding="utf-8").strip()
        table_name = table_name_for_csv(csv_path)
        size_mb = round(csv_path.stat().st_size / (1024 * 1024), 2)

        collections.append(
            {
                "name": folder.name,
                "folder": str(folder.resolve()),
                "csv_file": csv_path.name,
                "csv_path": str(csv_path),
                "txt_path": str(txt_path.resolve()),
                "table_name": table_name,
                "description": description,
                "file_size_mb": size_mb,
            }
        )

    return {
        "ok": len(errors) == 0 or len(collections) > 0,
        "source_root": str(source_root.resolve()),
        "collections": collections,
        "errors": errors,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
    }


def get_collection(state: dict[str, Any], name: str) -> dict[str, Any]:
    for col in state.get("collections", []):
        if col["name"] == name:
            return col
    raise KeyError(f"Collection not found: {name}")


def _truncate_description(text: str, max_chars: int | None) -> str:
    if not max_chars or len(text) <= max_chars:
        return text
    note = "\n…\n[description truncated; full text in collection .txt on disk]\n"
    keep = max(0, max_chars - len(note))
    return text[:keep] + note


def format_collections_block(collections: list[dict[str, Any]], cfg: dict[str, Any]) -> str:
    prompt_cfg = cfg.get("prompt", {})
    desc_max = prompt_cfg.get("description_max_chars")
    if desc_max is not None:
        desc_max = int(desc_max)
    per_col_cap = int(prompt_cfg.get("max_chars_per_collection", 16_000))
    total_cap = int(prompt_cfg.get("max_total_chars", 2_097_152))

    blocks: list[str] = []
    total_len = 0

    for col in collections:
        desc = _truncate_description(col.get("description", ""), desc_max)
        lines = [
            f'- name: "{col["name"]}"',
            f'  table_name: "{col["table_name"]}"',
            f'  csv_file: "{col.get("csv_file", "")}"',
            f'  folder: "{col["folder"]}"',
            f'  mcp_load: load_csv_folder("{col["folder"]}")',
            f'  load_status: unknown',
        ]
        if col.get("file_size_mb") is not None:
            lines.append(f'  file_size_mb: {col["file_size_mb"]}')
        lines.append("  description: |")
        for dline in desc.splitlines():
            lines.append(f"    {dline}")

        chunk = "\n".join(lines)
        if len(chunk) > per_col_cap:
            chunk = chunk[: per_col_cap - 1] + "…"
        if total_len + len(chunk) > total_cap:
            lines.append(
                '  note: "further collections omitted (max_total_chars); run discover_collections.py"'
            )
            blocks.append("\n".join(lines[:8]))
            break
        blocks.append(chunk)
        total_len += len(chunk)

    return "\n".join(blocks)
