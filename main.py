import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Load environment variables from .env before anything reads them
load_dotenv()

import database as db
import semantic_model as sm
from retriever import SchemaRetriever
from validator import validate_sql

app = FastAPI(title="Text-to-SQL MVP Backend API", version="1.0.0")

# Setup domains directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOMAINS_DIR = os.path.join(BASE_DIR, "domains")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(DOMAINS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Initialize domains and retriever
sm.init_default_domains(DOMAINS_DIR)
retriever = SchemaRetriever()

# Try to load cached index on startup
retriever.load_cache()


class QueryExecutionRequest(BaseModel):
    sql: str


class QueryRequest(BaseModel):
    question: str


class DomainUpdateRequest(BaseModel):
    yaml: str


class IndexResponse(BaseModel):
    message: str
    indexed_tables: int


@app.on_event("startup")
def startup_event():
    # If the index is empty, build it
    if not retriever.index:
        try:
            build_index_internal()
        except Exception as e:
            print(f"Failed to build index on startup: {e}")


def build_index_internal() -> int:
    """Internal function to parse domains and build the index."""
    documents = []
    for filename in os.listdir(DOMAINS_DIR):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            filepath = os.path.join(DOMAINS_DIR, filename)
            try:
                domain_data = sm.load_domain(filepath)
                docs = sm.serialize_domain_tables(domain_data)
                documents.extend(docs)
            except Exception as e:
                print(f"Error loading domain file {filename}: {e}")

    retriever.build_index(documents)
    return len(documents)


@app.post("/api/index", response_model=IndexResponse)
def reindex_schemas():
    """Reads all YAML files from the domains directory and updates the vector store index."""
    try:
        count = build_index_internal()
        return IndexResponse(message="Index built successfully.", indexed_tables=count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@app.get("/api/retrieve")
def retrieve_tables(
    query: str = Query(..., description="Natural language question/query"),
    top_k: int = 5,
):
    """Retrieves top_k relevant tables/domains matching the user's natural language query."""
    try:
        results = retriever.retrieve(query, top_k=top_k)
        return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@app.post("/api/execute")
def execute_sql(payload: QueryExecutionRequest):
    """Validates and executes a SQL query against the database."""
    raw_schema = db.get_raw_schema()
    whitelist = set(raw_schema.keys())

    is_valid, modified_sql, error_msg = validate_sql(
        payload.sql, whitelist_tables=whitelist
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Validation failed: {error_msg}")

    try:
        results = db.execute_query(modified_sql)
        return {
            "original_sql": payload.sql,
            "executed_sql": modified_sql,
            "row_count": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Database execution error: {str(e)}"
        )


@app.get("/api/domains")
def list_domains():
    """Lists all available domains by scanning the domains directory.

    Returns each domain's name, human-readable description, and table count so the
    frontend can render the domain tabs dynamically instead of hardcoding them.
    """
    domains = []
    for filename in sorted(os.listdir(DOMAINS_DIR)):
        if not (filename.endswith(".yaml") or filename.endswith(".yml")):
            continue
        filepath = os.path.join(DOMAINS_DIR, filename)
        name = os.path.splitext(filename)[0]
        try:
            data = sm.load_domain(filepath) or {}
            domains.append(
                {
                    "name": data.get("domain", name),
                    "description": data.get("description", ""),
                    "table_count": len(data.get("tables", {})),
                }
            )
        except Exception as e:
            print(f"Error loading domain file {filename}: {e}")
    return {"domains": domains}


@app.get("/api/domain/{domain_name}")
def get_domain_yaml(domain_name: str):
    """Retrieves the raw YAML content for a given domain."""
    filepath = os.path.join(DOMAINS_DIR, f"{domain_name}.yaml")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Domain configuration not found")
    try:
        with open(filepath, "r") as f:
            content = f.read()

        # Parse it to get tables count etc.
        data = sm.load_domain(filepath)
        tables = list(data.get("tables", {}).keys())

        return {"domain": domain_name, "yaml": content, "tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read domain: {str(e)}")


@app.post("/api/domain/{domain_name}")
def update_domain_yaml(domain_name: str, payload: DomainUpdateRequest):
    """Updates the YAML configuration file for a given domain."""
    filepath = os.path.join(DOMAINS_DIR, f"{domain_name}.yaml")
    try:
        # Validate that YAML is syntactically correct
        import yaml

        parsed = yaml.safe_load(payload.yaml)
        if not parsed or not isinstance(parsed, dict):
            raise ValueError("YAML content must resolve to a valid dictionary.")

        with open(filepath, "w") as f:
            f.write(payload.yaml)

        return {"message": "Domain updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML config: {str(e)}")


@app.post("/api/query")
def api_query(payload: QueryRequest):
    """
    Translates natural language to SQL using schema context, validates it, and executes it.
    Requires GEMINI_API_KEY (loaded from .env); there is no mock fallback.
    """
    question = payload.question

    # 1. Query SchemaRetriever to get top matching tables.
    #    Pull a wider candidate set so cross-domain / multi-table joins are possible.
    top_matches = retriever.retrieve(question, top_k=8)

    # Expand retrieval to every table belonging to a matched domain. A single table
    # match (e.g. "departments") is rarely answerable alone; including its sibling
    # tables (employees, salaries, performance_reviews, ...) gives the LLM enough
    # context to build joins instead of returning "Insufficient context".
    matched_domains = {m["domain"] for m in top_matches}
    expanded = [e for e in retriever.index if e["domain"] in matched_domains]

    # Extract retrieved context and whitelisted tables from the expanded set
    retrieved_context = "\n\n".join([e["text"] for e in expanded])
    retrieved_tables = {e["table"].lower() for e in expanded}

    # Fallback to full database tables whitelist if retrieval yielded nothing
    if not retrieved_tables:
        raw_schema = db.get_raw_schema()
        retrieved_tables = set(raw_schema.keys())
        retrieved_context = "\n\n".join(
            [e["text"] for e in retriever.index]
        )

    # 2. Construct the prompt
    prompt = f"""You are a SQLite expert. Convert the following user question into a valid SQL query.
Use ONLY the tables and columns defined in the schema below.

--- SCHEMA CONTEXT ---
{retrieved_context}

--- RULES ---
1. Use ONLY read-only SELECT queries.
2. Only query the tables present in the Schema Context above.
3. Return ONLY the raw SQL query. Do not wrap it in markdown code blocks, do not explain the query.
4. If you cannot answer the question using the schema, output 'ERROR: Insufficient context'.

Question: {question}
SQL:"""

    api_key = os.environ.get("GEMINI_API_KEY")

    # 3. Call Gemini (required — no mock fallback)
    if not api_key or api_key == "your-google-api-key-here":
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not configured. Set it in the .env file.",
        )

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        generated_sql = response.text.strip()
        # Clean up markdown code blocks if any
        if generated_sql.startswith("```"):
            lines = generated_sql.splitlines()
            if len(lines) >= 2:
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
            generated_sql = "\n".join(lines).strip()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {str(e)}")

    # 4. Validate SQL
    is_valid, validated_sql, validation_error = validate_sql(
        generated_sql, whitelist_tables=retrieved_tables
    )

    # 5. Execute query if valid
    results = []
    columns = []
    if is_valid:
        try:
            results = db.execute_query(validated_sql)
            if results:
                columns = list(results[0].keys())
        except Exception as e:
            validation_error = f"Execution failed: {str(e)}"
            is_valid = False

    return {
        "question": question,
        "retrieved_context": retrieved_context,
        "prompt": prompt,
        "generated_sql": generated_sql,
        "validated_sql": validated_sql if is_valid else "",
        "validation_error": validation_error,
        "results": results,
        "columns": columns,
    }


@app.get("/api/schema")
def get_database_schema():
    """Returns the raw SQLite database schema information."""
    try:
        schema = db.get_raw_schema()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Schema retrieval failed: {str(e)}"
        )


# Mount static files for UI serving
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def read_root():
    """Serves the main application dashboard."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse(
        "<h2>Frontend static files not found. Check static/index.html existence.</h2>"
    )


if __name__ == "__main__":
    import uvicorn

    db.seed_database()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
