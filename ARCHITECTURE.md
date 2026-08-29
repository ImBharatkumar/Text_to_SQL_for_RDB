# Architecture & Component Flow

A technical reference for the Text-to-SQL & Python Sandbox Agent System: component design, package organization, request flows, and security guardrails.

---

## 1. High-Level Architecture & Package Layout

The application is structured into the `app/` package for clean modularity and extensibility:

```
txt_sql/
├── app/
│   ├── main.py                 # FastAPI web server & REST orchestrator
│   ├── core/
│   │   ├── database.py         # SQLite connection, seeding, raw schema introspection
│   │   ├── semantic_model.py   # Domain YAML parsing and document serialization
│   │   └── validator.py        # Static SQL read-only validation & table whitelisting
│   ├── retrieval/
│   │   └── retriever.py        # Snowflake Arctic Embed vector retrieval & caching
│   ├── agent/
│   │   ├── sandbox.py          # Python code execution sandbox with stdout/stderr capture
│   │   ├── tools.py            # Pre-built agent tools (search_schema, query_sql, inspect_table)
│   │   └── agent.py            # Code-interpreter agent reasoning loop & self-repair
│   └── plugins/
│       └── llm.py              # Abstracted LLM provider plugin (Gemini / open models)
```

---

## 2. Component Responsibilities

### `app/core/database.py` — Data Layer
Owns the SQLite database (`sandbox.db`), synthetic data seeding across 7 domains (33 tables), read-only query execution, and raw schema reflection.

### `app/core/semantic_model.py` — Semantic Layer
Parses domain YAML definitions (`domains/*.yaml`) and converts tables/columns into search-friendly text documents for vector embedding.

### `app/retrieval/retriever.py` — Vector Search (`SchemaRetriever`)
Embeds semantic schema documents using `snowflake/snowflake-arctic-embed-m-v1.5` (SentenceTransformer) and performs cosine similarity search. Caches embeddings in `schema_index.json`.

### `app/core/validator.py` — Security Gate (`validate_sql`)
Enforces static read-only checks (blocking `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, etc.), restricts tables to an allowed whitelist, and caps `LIMIT`.

### `app/agent/sandbox.py` — Python Execution Runtime
Isolated in-process Python execution scope that runs generated Python code, capturing `stdout`, `stderr`, and return objects while trapping runtime exceptions.

### `app/agent/tools.py` — Agent Helper Tools
Functions exposed inside the Python sandbox:
- `search_schema(query)`: Vector similarity retrieval over schema descriptions.
- `inspect_table(table_name)`: Returns column types and details for a table.
- `query_sql(sql)`: Executes validated read-only SQL queries against SQLite.
- `sample_column_values(table_name, column_name)`: Returns distinct sample values for a column.

### `app/agent/agent.py` — Python Sandbox Agent (`PythonSandboxAgent`)
ReAct/Code-Interpreter agent loop that converts user questions into Python scripts, executes them in the sandbox, and automatically retries with error feedback if execution fails.

---

## 3. Request Lifecycles

### A. Python Sandbox Agent Request — `POST /api/agent_query`

1. **Schema Retrieval**: Vector search matches top schema candidates.
2. **Code Generation**: LLM generates Python code using helper tools (`query_sql`, `search_schema`, `inspect_table`).
3. **Sandbox Execution**: Code runs in `PythonSandbox`.
4. **Self-Correction**: On syntax/runtime/SQL errors, the error traceback is fed back to the LLM to re-generate the script (up to $N$ iterations).
5. **Response**: Returns final result, stdout output, iterations used, and execution trajectory.

---

### B. Single-Shot Query Request — `POST /api/query`

1. `retriever.retrieve(question, top_k=5)` → top candidate tables.
2. Domain expansion pulls sibling tables in matched domains.
3. Prompt constructed with narrowed schema context.
4. Gemini generates candidate SELECT SQL.
5. `validate_sql()` checks safety rules & whitelist.
6. Execution against `sandbox.db` returning results.

---

## 4. Summary of Endpoints

| Endpoint | Method | Role |
|----------|--------|------|
| `/api/agent_query` | POST | Execute question via Python Sandbox Agent with self-repair |
| `/api/query` | POST | Single-pass Text-to-SQL generation |
| `/api/execute` | POST | Execute raw validated SQL |
| `/api/retrieve` | GET | Schema vector search inspection |
| `/api/index` | POST | Reindex domain YAMLs into vector store |
| `/api/schema` | GET | Raw database schema dump |
| `/api/domain/{name}` | GET / POST | Read / Update domain YAML config |
