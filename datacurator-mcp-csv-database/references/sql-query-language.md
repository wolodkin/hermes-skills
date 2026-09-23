# SQL query patterns (mcp-csv-database / SQLite)

Table name comes from the CSV file stem (e.g. `annotated_02.csv` → `annotated_02`). Confirm with `list_loaded_tables`.

Always quote column names: `"AQUiLA-ID"`, `"Adm. Einheit"`.

## Filter by primary key

```sql
SELECT * FROM annotated_02
WHERE "AQUiLA-ID" = 'sesam-1422085'
LIMIT 10;
```

## Substring search (JSON / text cells)

```sql
SELECT "AQUiLA-ID", "Taxon", "Fundortbeschreibung"
FROM annotated_02
WHERE (
  LOWER("Taxon") LIKE '%azadinium%'
  OR LOWER("Familie") LIKE '%botrychloridaceae%'
)
LIMIT 50;
```

## Count matching a filter (when the user asks "how many")

```sql
SELECT COUNT(*) AS n FROM annotated_02
WHERE LOWER("Adm. Einheit") LIKE '%deutschland%';
```

## Distinct values

```sql
SELECT DISTINCT "Typus" FROM annotated_02
WHERE "Typus" IS NOT NULL AND "Typus" != '-'
LIMIT 30;
```

## Group by

```sql
SELECT "Familie", COUNT(*) AS n
FROM annotated_02
GROUP BY "Familie"
ORDER BY n DESC
LIMIT 20;
```

## Missing data

Treat `NULL`, `''`, and `'-'` as missing in filters:

```sql
SELECT COUNT(*) FROM annotated_02
WHERE "Geographische Breite" IS NULL
   OR TRIM("Geographische Breite") IN ('', '-');
```

Or use MCP `analyze_missing_data('annotated_02')`.

## Pagination (large matches)

```sql
SELECT "AQUiLA-ID", "Taxon"
FROM annotated_02
WHERE LOWER("Adm. Einheit") LIKE '%deutschland%'
LIMIT 100 OFFSET 0;
```

Increase `OFFSET` for further pages; summarize for the user instead of dumping all pages into chat.

## MCP call

Pass SQL to `execute_sql_query` with an explicit `limit` argument. Skill config suggests default 100 and max 1000 per call as guidance for the agent.
