# ArcticSQL — Text-to-SQL & Python Sandbox Agent Harness

A modular **Text-to-SQL & Python Sandbox Agent System** built for non-technical analysts to query multi-domain databases safely, accurately, and interactively — powered by **Snowflake Arctic Embed** for semantic schema retrieval, **Gemini** for SQL generation, and an **Autonomous Python Sandbox Agent** with self-repair capabilities.

---

## 🧠 The Problem & Evolution

1. **Baseline Text-to-SQL**: Sending raw database schemas to an LLM leads to high error rates, missing join logic, and prompt bloat.
2. **Stage 1 (Semantic Retrieval)**: Uses `snowflake/snowflake-arctic-embed-m-v1.5` to retrieve only the relevant domain schema context before SQL generation.
3. **Stage 2 (Agent + Harness)**: Introduces a **Python Code Execution Sandbox Agent** that dynamically writes code, inspects schema, samples column values, executes queries safely, and self-corrects on runtime errors.

---

## 🏗️ Architecture

```
User Question
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Python Sandbox Agent Loop                 │
│  (ReAct Code-Interpreter with Iterative Self-Repair)        │
│                                                             │
│  ┌───────────────────────┐       ┌──────────────────────┐   │
│  │ app.plugins.llm       │ ──►   │ app.agent.sandbox    │   │
│  │ (Gemini Code Gen)     │       │ (Python Runtime)     │   │
│  └───────────────────────┘       └──────────────────────┘   │
│              ▲                               │              │
│              │ (Error feedback loop)         │ helper tools │
│              └───────────────────────────────┘              │
└──────────────────────────────┬──────────────────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
┌──────────────┐       ┌──────────────┐        ┌──────────────┐
│ search_schema│       │ inspect_table│        │  query_sql   │
│ (Retriever)  │       │ (Raw Schema) │        │ (Validator)  │
└──────────────┘       └──────────────┘        └──────────────┘
                                                       │
                                                       ▼
                                             ┌──────────────────┐
                                             │ SQLite Database  │
                                             └──────────────────┘
```

---

## 📁 Project Structure

```
txt_sql/
├── app/                        # Main application package
│   ├── __init__.py
│   ├── main.py                 # FastAPI web app & REST API endpoints
│   ├── core/                   # Core DB, schema, and security rules
│   │   ├── database.py         # SQLite data access & synthetic seed engine
│   │   ├── semantic_model.py   # Domain YAML semantic schema parser
│   │   └── validator.py        # Static SQL security validator & table whitelist
│   ├── retrieval/              # Schema indexing & vector retrieval
│   │   └── retriever.py        # SentenceTransformer vector retriever & index cache
│   ├── agent/                  # Python Sandbox & Agent Reasoning engine
│   │   ├── sandbox.py          # Isolated Python code execution environment
│   │   ├── tools.py            # Pre-built Python helper tools (query_sql, search_schema, inspect_table)
│   │   └── agent.py            # Code-generation agent loop with error self-correction
│   └── plugins/                # Extensible LLM & tool plugin wrappers
│       └── llm.py              # LLM provider wrapper (Gemini, open models, etc.)
├── domains/                    # Domain schema YAML configurations (7 domains)
│   ├── healthcare_claims.yaml
│   ├── retail_sales.yaml
│   ├── finance_banking.yaml
│   ├── ecommerce.yaml
│   ├── hr_payroll.yaml
│   ├── logistics.yaml
│   └── education.yaml
├── static/                     # Frontend UI dashboard
│   ├── index.html              # Dashboard UI
│   ├── index.css               # Dark mode styling
│   └── app.js                  # Frontend logic & visualization
├── tests/                      # Unit & integration test suite
│   ├── test_api.py
│   ├── test_components.py
│   └── test_pipeline.py
├── evaluate.py                 # Ground truth evaluation & benchmark harness
├── ARCHITECTURE.md             # Detailed architecture reference
├── README.md                   # System documentation & setup guide
├── AGENTS.md                   # Development rules & guidelines
└── pyproject.toml              # Project dependencies & environment configuration
```

---

## 🚀 Quick Start

### 1. Install dependencies using `uv` or virtualenv

```bash
uv sync
```

Or using python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Set your Gemini API Key

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Set `GEMINI_API_KEY` in `.env`:

```dotenv
GEMINI_API_KEY=your-google-api-key
```

### 3. Start the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agent_query` | Autonomous Python Sandbox Agent (code generation + self-repair) |
| `POST` | `/api/query` | Single-pass Natural Language → SQL → execution |
| `POST` | `/api/execute` | Validate and execute a raw SQL query |
| `GET` | `/api/retrieve?query=...` | Semantic schema vector retrieval |
| `POST` | `/api/index` | Re-build the semantic vector index from domain YAMLs |
| `GET` | `/api/schema` | View raw SQLite database table schemas |
| `GET` | `/api/domain/{name}` | Read a domain YAML config |
| `POST` | `/api/domain/{name}` | Update a domain YAML config |

---

## 🧪 Running Tests & Evaluation Harness

```bash
# Unit & component tests
.venv/bin/python tests/test_components.py

# Full API integration tests
.venv/bin/python tests/test_pipeline.py
.venv/bin/python tests/test_api.py

# Golden dataset evaluation harness
.venv/bin/python evaluate.py
```

---

## 🛡️ Security & Sandbox Controls

- **Read-Only SQL Enforcement**: `validator.py` blocks write commands (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, etc.) and enforces table whitelisting.
- **Python Execution Isolation**: `PythonSandbox` runs in a clean scope capturing `stdout`, `stderr`, and execution errors to safely allow agent self-repair loops.
