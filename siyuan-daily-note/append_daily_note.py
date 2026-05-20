#!/usr/bin/env python3
"""
Append a line to today's SiYuan daily note (one document per UTC day).

State file: ~/.hermes/state/siyuan-daily-note.json
Env:       ~/.hermes/.env (SIYUAN_TOKEN, SIYUAN_URL)
"""

from __future__ import annotations

import html
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path.home() / ".hermes" / "state" / "siyuan-daily-note.json"
ENV_PATH = Path.home() / ".hermes" / ".env"
DEFAULT_NOTEBOOK = "Daily Notes"
# Tag label for SiYuan textmark (appendBlock markdown does not create real tags)
DEFAULT_TAG = "HermInE"


def load_env() -> None:
    if not ENV_PATH.is_file():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def siyuan_post(base_url: str, token: str, endpoint: str, data: dict) -> dict:
    url = f"{base_url.rstrip('/')}{endpoint}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {endpoint}: {err_body}") from e


def load_state() -> dict:
    if not STATE_PATH.is_file():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def doc_exists(base_url: str, token: str, doc_id: str) -> bool:
    """getDocByID is unavailable on some instances; getHPathByID works."""
    try:
        result = siyuan_post(
            base_url, token, "/api/filetree/getHPathByID", {"id": doc_id}
        )
    except RuntimeError:
        return False
    return result.get("code") == 0


def dailynote_attr_name(ymd: str) -> str:
    """SiYuan native daily-note attribute (see siyuan-note/siyuan#9807)."""
    return f"custom-dailynote-{ymd}"


def has_dailynote_attribute(
    base_url: str, token: str, doc_id: str, ymd: str
) -> bool:
    attr = dailynote_attr_name(ymd)
    stmt = (
        "SELECT 1 FROM attributes "
        f"WHERE block_id = '{doc_id}' AND name = '{attr}' AND value = '{ymd}' "
        "LIMIT 1"
    )
    result = siyuan_post(base_url, token, "/api/query/sql", {"stmt": stmt})
    if result.get("code") != 0:
        return False
    return bool(result.get("data"))


def ensure_dailynote_attribute(
    base_url: str, token: str, doc_id: str, ymd: str
) -> None:
    if has_dailynote_attribute(base_url, token, doc_id, ymd):
        return
    attr = dailynote_attr_name(ymd)
    result = siyuan_post(
        base_url,
        token,
        "/api/attr/setBlockAttrs",
        {"id": doc_id, "attrs": {attr: ymd}},
    )
    if result.get("code") != 0:
        raise RuntimeError(
            f"setBlockAttrs failed for {attr}: {result.get('msg', result)}"
        )


def find_day_doc_by_attribute(
    base_url: str, token: str, ymd: str
) -> str | None:
    attr = dailynote_attr_name(ymd)
    stmt = (
        "SELECT block_id FROM attributes "
        f"WHERE name = '{attr}' AND value = '{ymd}' "
        "ORDER BY block_id LIMIT 1"
    )
    result = siyuan_post(base_url, token, "/api/query/sql", {"stmt": stmt})
    if result.get("code") != 0:
        return None
    rows = result.get("data") or []
    if not rows:
        return None
    return rows[0].get("block_id")


def find_day_doc_id(
    base_url: str, token: str, notebook_id: str, hpath: str
) -> str | None:
    """Resolve today's document via SQL (createDocWithMd is not always idempotent)."""
    stmt = (
        "SELECT id FROM blocks "
        f"WHERE box = '{notebook_id}' AND type = 'd' AND hpath = '{hpath}' "
        "ORDER BY created ASC LIMIT 1"
    )
    result = siyuan_post(base_url, token, "/api/query/sql", {"stmt": stmt})
    if result.get("code") != 0:
        return None
    rows = result.get("data") or []
    if not rows:
        return None
    return rows[0].get("id")


def resolve_notebook_id(
    base_url: str, token: str, notebook_name: str
) -> str:
    result = siyuan_post(base_url, token, "/api/notebook/lsNotebooks", {})
    if result.get("code") != 0:
        raise RuntimeError(f"lsNotebooks failed: {result.get('msg', result)}")
    notebooks = result.get("data", {}).get("notebooks", [])
    for nb in notebooks:
        if nb.get("name") == notebook_name:
            return nb["id"]
    raise RuntimeError(f'Notebook "{notebook_name}" not found')


def ensure_day_document(
    base_url: str,
    token: str,
    notebook_id: str,
    day_path: str,
) -> str:
    payload = {
        "notebook": notebook_id,
        "path": day_path,
        "markdown": "",
    }
    result = siyuan_post(base_url, token, "/api/filetree/createDocWithMd", payload)
    if result.get("code") != 0:
        raise RuntimeError(f"createDocWithMd failed: {result.get('msg', result)}")
    doc_id = result.get("data")
    if not doc_id:
        raise RuntimeError("createDocWithMd returned no document ID")
    return doc_id


def normalize_tag_label(tag: str) -> str:
    """Map daily_tag config (#HermInE#, (#HermInE)) to SiYuan tag label HermInE."""
    label = tag.strip()
    if label.startswith("(") and label.endswith(")"):
        label = label[1:-1].strip()
    label = label.strip("#")
    if not label:
        raise ValueError(f"invalid daily_tag: {tag!r}")
    return label


def build_paragraph_dom(text: str, tag_label: str) -> str:
    """DOM for appendBlock: markdown #tag# is not parsed as inline tags via API."""
    body = html.escape(text, quote=True)
    tag = html.escape(tag_label, quote=True)
    return (
        '<motion.div class="p" data-type="NodeParagraph">'
        f'<span data-type="text">{body}</span><br />'
        f'<span data-type="tag" data-info="">{tag}</span>'
        "</motion.div>"
    )


def append_entry(
    base_url: str,
    token: str,
    doc_id: str,
    text: str,
    tag_label: str,
) -> None:
    content = build_paragraph_dom(text, tag_label)
    result = siyuan_post(
        base_url,
        token,
        "/api/block/appendBlock",
        {"parentID": doc_id, "data": content, "dataType": "dom"},
    )
    if result.get("code") != 0:
        raise RuntimeError(f"appendBlock failed: {result.get('msg', result)}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: append_daily_note.py <text to append>", file=sys.stderr)
        return 1

    user_text = sys.argv[1].strip()
    if not user_text:
        print("Error: empty text", file=sys.stderr)
        return 1

    load_env()
    token = os.environ.get("SIYUAN_TOKEN", "").strip()
    base_url = os.environ.get("SIYUAN_URL", "").strip()
    if not token or not base_url:
        print("Error: SIYUAN_TOKEN and SIYUAN_URL must be set in ~/.hermes/.env", file=sys.stderr)
        return 1

    state = load_state()
    notebook_name = state.get("notebook_name") or DEFAULT_NOTEBOOK
    tag_raw = state.get("daily_tag") or DEFAULT_TAG
    try:
        tag_label = normalize_tag_label(tag_raw)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    ymd = f"{year}{month}{day}"
    day_path = f"/daily note/{year}/{month}/{year}-{month}-{day}.sy"
    hpath = day_path.removesuffix(".sy")

    notebook_id = resolve_notebook_id(base_url, token, notebook_name)

    doc_id = state.get("doc_ids", {}).get(ymd)
    if doc_id and not doc_exists(base_url, token, doc_id):
        doc_id = None

    if not doc_id:
        doc_id = find_day_doc_by_attribute(base_url, token, ymd)

    if not doc_id:
        doc_id = find_day_doc_id(base_url, token, notebook_id, hpath)

    if not doc_id:
        doc_id = ensure_day_document(base_url, token, notebook_id, day_path)

    ensure_dailynote_attribute(base_url, token, doc_id, ymd)

    try:
        append_entry(base_url, token, doc_id, user_text, tag_label)
    except RuntimeError:
        doc_id = find_day_doc_by_attribute(base_url, token, ymd)
        if not doc_id:
            doc_id = find_day_doc_id(base_url, token, notebook_id, hpath)
        if not doc_id:
            doc_id = ensure_day_document(base_url, token, notebook_id, day_path)
        ensure_dailynote_attribute(base_url, token, doc_id, ymd)
        append_entry(base_url, token, doc_id, user_text, tag_label)

    new_state = {
        "notebook_name": notebook_name,
        "daily_tag": tag_raw,
        "doc_ids": {ymd: doc_id},
    }
    save_state(new_state)

    print(
        json.dumps(
            {
                "ok": True,
                "doc_id": doc_id,
                "path": day_path,
                "ymd": ymd,
                "attr": dailynote_attr_name(ymd),
                "tag": tag_label,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
