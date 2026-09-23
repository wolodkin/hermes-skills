# Multilingual search (SQL / MCP)

Data mixes German labels, English text, and Latin scientific names. Search with several variants and multiple columns.

## Strategy

1. Keep the user's term if it may appear verbatim (e.g. German locality).
2. Add English and Latin/scientific stems.
3. Use SQL `LOWER("Column") LIKE '%term%'` with OR across columns.
4. Run `suggest_search_terms.py` for a starting SQL example.

## Helper

```bash
python3 scripts/suggest_search_terms.py --term "Holz" --lang de --table annotated_02
```

## Example SQL

```sql
SELECT "AQUiLA-ID", "Taxon", "Substrat", "Bemerkung"
FROM annotated_02
WHERE (
  LOWER("Taxon") LIKE '%holz%' OR LOWER("Taxon") LIKE '%wood%'
  OR LOWER("Taxon") LIKE '%lign%' OR LOWER("Substrat") LIKE '%holz%'
  OR LOWER("Substrat") LIKE '%wood%'
)
LIMIT 100;
```

## Latin / concept hints

| Concept | Also try |
|---------|----------|
| wood | lign, xyl, lignum, Holz |
| water | aqua, aquat, hydro, Wasser |
| Germany | Deutschland, Germany, Germania (JSON keys and free text) |
| type specimen | holotyp, isotyp, Holotypus |
| algae | algae, alg, phyc, Algen |

## Three attempts

| Try | Action |
|-----|--------|
| 1 | Broad OR across EN + LA + user language on 3–5 text columns |
| 2 | Narrow columns or fewer stems if noisy |
| 3 | DISTINCT or GROUP BY; if still empty, report no match |

Escape single quotes in SQL literals by doubling: `'O''Reilly'`.
