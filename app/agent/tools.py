from typing import List, Dict, Any
from app.core import database as db
from app.core import validator as val
from app.retrieval.retriever import SchemaRetriever

# Lazy global retriever instance
_retriever_instance = None

def get_retriever():
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = SchemaRetriever()
        _retriever_instance.load_cache()
    return _retriever_instance

def search_schema(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Searches schema vector index for matching tables and columns."""
    retriever = get_retriever()
    return retriever.retrieve(query, top_k=top_k)

def inspect_table(table_name: str) -> Dict[str, Any]:
    """Returns raw SQLite schema definition for a table."""
    raw_schema = db.get_raw_schema()
    tbl = table_name.lower()
    if tbl in raw_schema:
        return {tbl: raw_schema[tbl]}
    return {"error": f"Table '{table_name}' not found in database schema."}

def sample_column_values(table_name: str, column_name: str, limit: int = 5) -> List[Any]:
    """Samples distinct non-null values from a table column."""
    raw_schema = db.get_raw_schema()
    tbl = table_name.lower()
    if tbl not in raw_schema:
        return []
    sql = f"SELECT DISTINCT {column_name} FROM {tbl} WHERE {column_name} IS NOT NULL LIMIT {limit};"
    is_valid, mod_sql, err = val.validate_sql(sql, whitelist_tables=set(raw_schema.keys()))
    if not is_valid:
        return []
    try:
        rows = db.execute_query(mod_sql)
        return [r[column_name] for r in rows if column_name in r]
    except Exception:
        return []

def query_sql(sql: str) -> List[Dict[str, Any]]:
    """Validates and executes read-only SQL query against the database."""
    raw_schema = db.get_raw_schema()
    whitelist = set(raw_schema.keys())
    is_valid, modified_sql, error_msg = val.validate_sql(sql, whitelist_tables=whitelist)
    if not is_valid:
        raise ValueError(f"SQL Validation Error: {error_msg}")
    return db.execute_query(modified_sql)
