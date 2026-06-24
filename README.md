# ArcticSQL — Text-to-SQL Semantic Layer MVP

A **Text-to-SQL** MVP built for non-technical analysts to query databases safely and accurately — powered by **Snowflake Arctic Embed** for semantic schema retrieval and **Gemini** for SQL generation.

---

## 🧠 The Problem

Sending 100+ raw tables to an LLM results in poor SQL quality. The model cannot reliably decide which tables matter, how they join, and which business terms map to which columns.

## ✅ The Solution

A **two-stage** pipeline:
1. **Retrieve** — semantically match the user's natural language question to the relevant domain/tables using `snowflake/snowflake-arctic-embed-m-v1.5`.
2. **Generate** — pass only that narrowed schema context to the LLM for SQL generation.

---

## 🏗️ Architecture

```
User Question
     │
     ▼
┌─────────────────────────────┐
│  Snowflake Arctic Embed     │  ← semantic schema retrieval
│  (Retriever Layer)          │    from domain YAML metadata
└─────────────────────────────┘
     │  top-k table matches + schema text
     ▼
┌─────────────────────────────┐
│  Prompt Builder             │  ← constrained context only
│  (Generation Layer)         │
└─────────────────────────────┘
     │  structured prompt
     ▼
┌─────────────────────────────┐
│  Gemini (gemini-2.5-flash)  │  ← SQL generation
│  (or Mock Fallback)         │
└─────────────────────────────┘
     │  raw SQL
     ▼
┌─────────────────────────────┐
│  SQL Validator              │  ← read-only enforcement,
│  (Validation Layer)         │    table whitelist, LIMIT guard
└─────────────────────────────┘
     │  safe SQL
     ▼
┌─────────────────────────────┐
│  SQLite Database            │  ← query execution
└─────────────────────────────┘
     │  rows
     ▼
  Web Dashboard (Table + Chart view)
```

---

## 📁 Project Structure

```
txt_sql/
├── pyproject.toml           # uv-compatible package config
├── main.py                  # FastAPI server (all API endpoints)
├── database.py              # SQLite connection, seeding, query execution
├── semantic_model.py        # Domain YAML management and serialization
├── retriever.py             # Snowflake Arctic Embed semantic retrieval
├── validator.py             # SQL safety validation
├── domains/
│   ├── healthcare_claims.yaml   # Semantic model: claims, payers, members, payments
│   └── retail_sales.yaml        # Semantic model: orders, products, sales
├── static/
│   ├── index.html           # Dashboard UI
│   ├── index.css            # Glassmorphic dark mode styling
│   └── app.js               # Frontend logic + Chart.js visualizations
├── test_components.py       # Unit tests: DB, validator, retriever
└── test_pipeline.py         # Integration tests: full API query flow
```

---

## 🚀 Quick Start

### 1. Install dependencies using `uv`

```bash
uv sync
```

Or with pip fallback:

```bash
pip install -e .
```

### 2. Set your Gemini API Key (required)

The app calls Gemini for SQL generation and has **no mock fallback** — a valid key is required.

Copy the example env file and fill in your key:

```bash
cp .env.example .env
```

Then edit `.env`:

```dotenv
GEMINI_API_KEY=your-google-api-key
```

The key is loaded automatically at startup via `python-dotenv`. The `.env` file is git-ignored.

> Get a free API key at [https://aistudio.google.com](https://aistudio.google.com)

### 3. Start the server

```bash
python main.py
```

Or via `uvicorn` directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Open the dashboard

Navigate to **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/query` | Natural language → SQL → results |
| `POST` | `/api/execute` | Validate and execute a raw SQL query |
| `GET` | `/api/retrieve?query=...` | Semantic schema retrieval only |
| `POST` | `/api/index` | Re-build the semantic vector index from domain YAMLs |
| `GET` | `/api/schema` | View raw SQLite database table schemas |
| `GET` | `/api/domain/{name}` | Read a domain YAML config |
| `POST` | `/api/domain/{name}` | Update a domain YAML config |

### Example — `/api/query`

**Request:**
```json
POST /api/query
{
  "question": "What is the total sales amount?"
}
```

**Response:**
```json
{
  "question": "What is the total sales amount?",
  "retrieved_context": "Domain: retail_sales. Table Name: sales...",
  "prompt": "You are a SQLite expert...",
  "generated_sql": "SELECT SUM(quantity * price) AS total_sales FROM sales",
  "validated_sql": "SELECT SUM(quantity * price) AS total_sales FROM sales LIMIT 100;",
  "validation_error": null,
  "results": [{"total_sales": 1650.0}],
  "columns": ["total_sales"]
}
```

---

## 🗂️ Semantic Domain Models

Business semantics are defined in editable **YAML files** under `domains/`. These can be edited directly in the web dashboard sidebar and saved via the `POST /api/domain/{name}` endpoint, which re-validates YAML syntax before writing.

```yaml
domain: healthcare_claims
description: Healthcare claims database containing member information, claims, payers, and payments.
tables:
  claims:
    description: Healthcare claims submitted by providers for services.
    columns:
      claim_id: Unique identifier for the claim.
      member_id: Member who received the services, matches members.member_id.
      payer_id: Payer responsible for the claim, matches payers.payer_id.
      service_date: Date when services were rendered.
      amount: Total dollar amount of the claim.
      status: Current status of the claim (e.g., Paid, Pending, Denied).
```

---

## 🛡️ Security & Validation

The `validator.py` module enforces the following before any SQL is executed:

- ❌ **Blocks write and admin commands**: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `REPLACE`, `GRANT`, `REVOKE`, `VACUUM`, `PRAGMA`, `REINDEX`
- ✅ **Table whitelist**: Only tables retrieved from the semantic context are allowed in `FROM` and `JOIN` clauses.
- 📏 **Row limit**: Automatically appends `LIMIT 100` if no limit is present, and downgrades any limit exceeding 100 to 100.

---

## 🧪 Running Tests

```bash
# Unit tests (database, validator, retriever)
python test_components.py

# Full integration pipeline test (API endpoints)
python test_pipeline.py
```

### Expected Output (`test_components.py`)

```
--- Testing Database ---
Tables found in DB schema: ['members', 'payers', 'claims', 'payments', 'sales']
Members count: 4
Database check: PASS

--- Testing Validator ---
Valid SELECT query: True, SQL: SELECT * FROM claims LIMIT 100;
Banned DELETE query: False, Error: Security Violation: Command 'DELETE' is not allowed.
Non-whitelisted table: False, Error: Access Violation: Table 'users' is not in the whitelist.
Validator check: PASS

--- Testing Semantic Model & Retriever ---
Domain files initialized: ['healthcare_claims.yaml', 'retail_sales.yaml']
Serialized 5 tables into documents.
Building retriever index (this may download the snowflake-arctic-embed model)...
Match 1: retail_sales.sales (Similarity: 0.5724)
Match 2: healthcare_claims.members (Similarity: 0.4037)
Semantic Model & Retriever check: PASS

All unit tests passed successfully!
```

---

## 🔧 Configuration

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key for SQL generation. **Required** — loaded from `.env`. The `/api/query` endpoint returns HTTP 500 if it is missing and HTTP 502 if the Gemini call fails. |

> **Embedding model**: Fixed to `snowflake/snowflake-arctic-embed-m-v1.5` in `retriever.py`. The model is downloaded on first use and cached locally by `sentence-transformers`.

> **Top-K retrieval**: The `/api/query` endpoint retrieves the top **2** most relevant table documents per query (`top_k=2` in `api_query`). The `/api/retrieve` endpoint defaults to **3**.

---

## 📦 Stack

| Component | Technology |
|-----------|------------|
| Web Framework | [FastAPI](https://fastapi.tiangolo.com) |
| Package Manager | [uv](https://github.com/astral-sh/uv) |
| Embedding Model | [snowflake/snowflake-arctic-embed-m-v1.5](https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v1.5) via `sentence-transformers` |
| SQL Generation | [Gemini (gemini-2.5-flash)](https://aistudio.google.com) via `google-genai` |
| Database | SQLite (via Python's built-in `sqlite3`) |
| Frontend | Vanilla HTML + CSS + JS + [Chart.js](https://www.chartjs.org) |
| Schema Metadata | YAML domain files (editable via dashboard sidebar) |

---

## 🗺️ Roadmap

- [ ] PostgreSQL + pgvector support for larger vector indexes
- [ ] Arctic-Text2SQL-R1-7B local model integration via Ollama
- [ ] Multi-domain query routing (cross-domain joins)
- [ ] Query history and caching layer
- [ ] User-defined business glossary (synonyms, aliases)
- [ ] Audit log for all executed queries
