# Architecture & Component Flow

A technical reference for the Text-to-SQL MVP: what each component does, its
inputs and outputs, and how a request flows end-to-end. For installation/usage
see `README.md`; for change history see `changelog/CHANGELOG.md`.

---

## 1. High-level idea

The app answers **natural-language questions** about a multi-domain SQLite
database by:

1. Embedding human-written **schema descriptions** (the "semantic layer").
2. Retrieving the schema most relevant to the question (RAG).
3. Asking **Gemini** to write SQL using only that schema.
4. **Validating** the SQL (read-only, whitelisted tables, enforced `LIMIT`).
5. Executing it and returning rows.

```
                 ┌──────────────────────────────────────────────────────────┐
                 │                        main.py (FastAPI)                   │
                 │                                                            │
  user question ─┼─► retriever ─► schema context ─► Gemini ─► SQL ─► validator│─► rows
                 │      ▲                                          │          │
                 │      │ embeddings                               ▼          │
                 │  schema_index.json                          database.py    │
                 └──────────────────────────────────────────────────────────┘
                        ▲                                          ▲
            semantic_model.py + domains/*.yaml              sandbox.db (SQLite)
```

---

## 2. Components

### `main.py` — orchestrator / HTTP API (FastAPI)
The entry point. Wires every other component together and exposes the REST API.

- **Input:** HTTP requests; environment (`GEMINI_API_KEY` via `.env`, loaded by `load_dotenv()`).
- **Output:** JSON responses; serves the `static/` frontend at `/`.
- **Startup:** `init_default_domains()` → `retriever.load_cache()` → build index if empty.
- **Depends on:** `database`, `semantic_model`, `retriever`, `validator`, `google.genai`.

### `semantic_model.py` — the semantic layer (schema *meaning*)
Turns domain YAML files into embeddable, search-friendly text. **Knows what the
columns mean**, not the data.

- **Input:** `domains/*.yaml` (domain → tables → columns, each with a description).
- **Output:** list of `{"domain", "table", "text"}` documents, where `text` is a
  single descriptive string per table (e.g. `"Domain: hr_payroll. ... Table Name:
  departments. ... Columns: department_id (...), budget (...)."`).
- **Key functions:** `init_default_domains()` (bootstrap YAMLs), `load_domain()`
  (read one YAML), `serialize_domain_tables()` (YAML → documents).
- **Note:** `DEFAULT_DOMAINS` only defines 2 of the 7 domains; the other 5 YAMLs
  live on disk in `domains/`. If `domains/` is deleted, only those 2 regenerate.

### `retriever.py` — vector search (`SchemaRetriever`)
Embeds the semantic documents and does cosine-similarity search to find the
tables relevant to a question. **Knows the math**, not the meaning.

- **Model:** `snowflake/snowflake-arctic-embed-m-v1.5` (SentenceTransformer, lazy-loaded).
- **Input:** documents from `semantic_model` (to build); a query string (to retrieve).
- **Output:** ranked `[{"domain", "table", "text", "similarity"}]`.
- **Persistence:** writes/reads `schema_index.json` (cached embeddings) so the
  model isn't re-run on every startup.
- **Key methods:** `build_index(documents)`, `retrieve(query, top_k)`,
  `load_cache()` / `save_cache()`.

### `validator.py` — safety gate (`validate_sql`)
Static checks on generated SQL **before** it touches the database.

- **Input:** raw SQL string, a `whitelist_tables` set, `max_limit` (default 100).
- **Output:** `(is_valid: bool, modified_sql: str, error_message: str)`.
- **Rules:** (1) blocks write/DDL keywords (`insert`, `update`, `drop`, …) via
  word-boundary regex; (2) every table after `FROM`/`JOIN` must be in the
  whitelist; (3) appends or caps a `LIMIT`.
- `DEFAULT_WHITELIST_TABLES` is only a fallback for direct callers — `/api/query`
  passes its own retrieval-derived whitelist; `/api/execute` passes the full DB schema.

### `database.py` — data layer (SQLite)
Owns the actual database: schema creation, the **synthetic seed data**, query
execution, and raw-schema introspection. **Knows the data.**

- **Input:** SQL + params (for execution).
- **Output:** `execute_query()` → list of row dicts; `get_raw_schema()` → table →
  column metadata; `seed_database()` populates `sandbox.db` (idempotent — guarded
  by `SELECT COUNT(*)`).
- **Domains seeded:** healthcare_claims, retail_sales, finance_banking, ecommerce,
  hr_payroll, logistics, education (31 tables total).

### Data / config files
| File | Role |
|------|------|
| `domains/*.yaml` | Source of truth for the semantic layer (7 domains). |
| `schema_index.json` | Cached embeddings of the serialized schema docs. |
| `sandbox.db` | The SQLite database (synthetic data). |
| `static/` | Frontend (served at `/`). |
| `.env` | Holds `GEMINI_API_KEY`. |

---

## 3. Request lifecycle — `POST /api/query`

This is the main pipeline. Step numbers map to `main.py` → `api_query()`.

| # | Step | Input | Output |
|---|------|-------|--------|
| 1 | `retriever.retrieve(question, top_k=8)` | question string | top-8 candidate tables |
| 1b | **Domain expansion** — pull *all* tables in any matched domain | matched domains | `retrieved_context` + `retrieved_tables` |
| 2 | Build prompt with schema context + rules | context + question | prompt string |
| 3 | Call Gemini (`gemini-3.5-flash`) | prompt | generated SQL (or `ERROR: Insufficient context`) |
| 4 | `validate_sql(sql, whitelist=retrieved_tables)` | SQL + whitelist | `(is_valid, validated_sql, error)` |
| 5 | `db.execute_query(validated_sql)` if valid | SQL | rows + columns |

**Response JSON:** `question`, `retrieved_context`, `prompt`, `generated_sql`,
`validated_sql`, `validation_error`, `results`, `columns`.

> Why domain expansion (step 1b)? A single table match (e.g. `departments`) is
> rarely answerable alone. Including its sibling tables gives the LLM enough
> context to build joins instead of returning `Insufficient context`, and widens
> the validation whitelist to match.

---

## 4. Other endpoints

| Endpoint | Method | Input | Output | Notes |
|----------|--------|-------|--------|-------|
| `/api/index` | POST | — | `{message, indexed_tables}` | Rebuilds the index from `domains/*.yaml`. |
| `/api/retrieve` | GET | `query`, `top_k=5` | ranked tables + similarity | Inspect retrieval directly (no LLM). |
| `/api/execute` | POST | `{sql}` | `{executed_sql, row_count, results}` | Validates against **full** DB schema, then runs. |
| `/api/domain/{name}` | GET | path name | `{domain, yaml, tables}` | Read a domain config. |
| `/api/domain/{name}` | POST | `{yaml}` | `{message}` | Update a domain YAML (validated as YAML). |
| `/api/schema` | GET | — | `{schema}` | Raw SQLite schema. |
| `/` | GET | — | `static/index.html` | Frontend dashboard. |

---

## 5. Separation of concerns (one-liners)

- **`database.py`** knows the *data*.
- **`semantic_model.py`** knows the *meaning* of the schema.
- **`retriever.py`** knows the *math* (which schema matches a question).
- **`validator.py`** knows the *rules* (what SQL is safe to run).
- **`main.py`** *orchestrates* all of the above over HTTP.

---

## 6. Known caveats

- **Model id:** `main.py` calls `model="gemini-3.5-flash"`. Verify this matches a
  currently available Gemini model; an invalid id surfaces as an HTTP 502.
- **Index staleness:** editing a `domains/*.yaml` does **not** auto-reindex — call
  `POST /api/index` (or delete `schema_index.json`) to pick up changes.
- **`DEFAULT_DOMAINS` incompleteness:** only 2 of 7 domains are self-healing (see
  `semantic_model.py` note above).
- **Regex SQL parsing:** `validator.py` uses regex, not a real SQL parser — fine
  for standard queries, but exotic syntax (CTEs aliased oddly, subquery-only
  `FROM`, etc.) may need a parser like `sqlglot` for production.
