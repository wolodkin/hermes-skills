# Multilingual search (user language + English + Latin)

Collection data mixes **German field labels**, **English annotations**, and **Latin scientific names** (especially `Taxon`, `Familie`, `Taxonomie`, `Synonyme`). A single-term filter in the user's language often misses rows.

## Strategy

1. **Understand** the user's term in their language.
2. **Expand** to English and Latin (scientific) variants before querying.
3. **Combine** variants in one `str.contains` with regex alternation (`|`).
4. **Search multiple columns** that may hold the concept (not only `Taxon`).

## Building `--where` patterns

Use regex alternation (pandas `str.contains` is regex by default):

```text
Taxon.str.contains('wood|lign|lignu|xyl', case=False, na=False)
```

Wider search across likely text columns:

```text
(
  Taxon.str.contains('wood|lign|lignu|xyl', case=False, na=False)
  | Substrat.str.contains('wood|lign|lignu|xyl', case=False, na=False)
  | Bemerkung.str.contains('wood|lign|lignu|xyl', case=False, na=False)
  | Fundortbeschreibung.str.contains('wood|lign|lignu|xyl', case=False, na=False)
)
```

Escape regex metacharacters in literal terms: `. * + ? [ ] ( ) { } ^ $ | \`

## Latin hints

| User concept | Also try (Latin / scientific stems) |
|--------------|-------------------------------------|
| wood | `lign`, `xyl`, `lignum` |
| water / aquatic | `aqua`, `aquat`, `hydro` |
| moss | `musc`, `bryoph` |
| fungus | `fung`, `myco` |
| algae | `alg`, `phyc` |
| type specimen | `holotyp`, `isotyp`, `syntyp`, `paratyp` (also German `Holotyp`) |
| Germany | often in locality JSON; also `Germania`, `Deutschland` in free text |

Scientific names in `Taxon` are usually already Latin — include the user's term **and** English glosses **and** common stems.

## Attempt budget (3 tries)

| Try | Action |
|-----|--------|
| 1 | Broad OR across EN + LA (+ user language if non-English) on 2–4 text columns |
| 2 | Narrow columns or fewer stems if too many false positives |
| 3 | `--distinct Taxon` or `--count-only` to validate; if still empty, report no match |

## Helper script

```bash
python3 scripts/suggest_search_terms.py --term "Holz" --lang de
```

Returns JSON with `terms[]` and a ready-made `where_or_pattern` for copy into `query_collection.py`.
