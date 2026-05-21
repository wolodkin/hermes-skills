# datacurator query language

Use `query_collection.py` only. CLI flags are in English. **Search terms** should cover the user's language plus **English and Latin/scientific** variants (see [multilingual-search.md](multilingual-search.md)).

## Multilingual OR search (recommended)

```bash
python3 scripts/suggest_search_terms.py --term "Holz" --lang de
# use where_clause from JSON output:

python3 scripts/query_collection.py \
  --collection "Algae and Protists" \
  --where "(Taxon.str.contains('Holz|wood|lign|lignu|xyl', case=False, na=False) | Substrat.str.contains('Holz|wood|lign|lignu|xyl', case=False, na=False))" \
  --limit 30
```

## Basic filter

```bash
python3 scripts/query_collection.py \
  --collection "Algae and Protists" \
  --where "Taxon.str.contains('Azadinium', case=False, na=False)" \
  --limit 20
```

## Column selection

```bash
python3 scripts/query_collection.py \
  --collection "Algae and Protists" \
  --where "Typus == 'Holotypus'" \
  --select "Taxon,Barcode,Typus,Fundortbeschreibung" \
  --limit 50
```

## Count

```bash
python3 scripts/query_collection.py \
  --collection "Algae and Protists" \
  --where "Familie.str.contains('Botrychloridaceae', case=False, na=False)" \
  --count-only
```

## Group by

```bash
python3 scripts/query_collection.py \
  --collection "Algae and Protists" \
  --groupby "Typus" \
  --agg count \
  --limit 20
```

JSON aggregation:

```bash
python3 scripts/query_collection.py \
  --collection "Algae and Protists" \
  --groupby "Familie" \
  --agg '{"Taxon":"nunique"}'
```

## Distinct values

```bash
python3 scripts/query_collection.py \
  --collection "Algae and Protists" \
  --distinct "Typus" \
  --limit 15
```

## Data quality

Null or empty (`-`) rows for a column:

```bash
python3 scripts/query_collection.py \
  --collection "Algae and Protists" \
  --nulls "Geographische Breite" \
  --limit 30
```

Invalid or missing coordinates:

```bash
python3 scripts/query_collection.py \
  --collection "Algae and Protists" \
  --invalid-coords \
  --limit 30
```

## Safety

- Read-only: CSV files are never modified.
- Forbidden in `--where`: `import`, `exec`, `open`, `__`, etc.
- Default `--limit` 100, max 1000 (see `config.json`).
