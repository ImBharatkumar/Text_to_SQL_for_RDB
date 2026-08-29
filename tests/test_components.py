import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.core.database as db
import app.core.semantic_model as sm
from app.core.validator import validate_sql
from app.retrieval.retriever import SchemaRetriever

def test_database():
    print("\n--- Testing Database ---")
    db.seed_database()
    schema = db.get_raw_schema()
    print("Tables found in DB schema:", list(schema.keys()))
    assert "claims" in schema
    assert "sales" in schema
    
    # Test query execution
    results = db.execute_query("SELECT count(*) as cnt FROM members")
    print("Members count:", results[0]["cnt"])
    assert results[0]["cnt"] > 0
    print("Database check: PASS")

def test_validator():
    print("\n--- Testing Validator ---")
    # Valid query
    is_valid, mod_sql, err = validate_sql("SELECT * FROM claims")
    print(f"Valid SELECT query: {is_valid}, SQL: {mod_sql}")
    assert is_valid
    assert "LIMIT 100" in mod_sql
    
    # Banned keyword
    is_valid, mod_sql, err = validate_sql("DELETE FROM claims WHERE claim_id = 'C001'")
    print(f"Banned DELETE query: {is_valid}, Error: {err}")
    assert not is_valid
    assert "Violation" in err
    
    # Non-whitelisted table
    is_valid, mod_sql, err = validate_sql("SELECT * FROM users")
    print(f"Non-whitelisted table: {is_valid}, Error: {err}")
    assert not is_valid
    assert "Access Violation" in err
    print("Validator check: PASS")

def test_semantic_model_and_retriever():
    print("\n--- Testing Semantic Model & Retriever ---")
    # Setup temp/default domains
    domains_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "domains")
    os.makedirs(domains_dir, exist_ok=True)
    sm.init_default_domains(domains_dir)
    
    # Check domain files
    files = os.listdir(domains_dir)
    print("Domain files initialized:", files)
    assert len(files) >= 2
    
    # Load and serialize
    all_docs = []
    for filename in files:
        filepath = os.path.join(domains_dir, filename)
        domain_data = sm.load_domain(filepath)
        docs = sm.serialize_domain_tables(domain_data)
        all_docs.extend(docs)
        
    print(f"Serialized {len(all_docs)} tables into documents.")
    
    # Retriever testing
    retriever = SchemaRetriever()
    print("Building retriever index (this may download the snowflake-arctic-embed model)...")
    retriever.build_index(all_docs)
    
    # Test retrieve
    query = "Find information about customer orders and laptops"
    print(f"Retrieving for query: '{query}'")
    results = retriever.retrieve(query, top_k=2)
    for idx, r in enumerate(results):
        print(f"Match {idx+1}: {r['domain']}.{r['table']} (Similarity: {r['similarity']:.4f})")
    
    # Should retrieve retail_sales/sales table as the top match
    assert len(results) > 0
    assert results[0]['table'] == 'sales'
    print("Semantic Model & Retriever check: PASS")

if __name__ == "__main__":
    test_database()
    test_validator()
    try:
        test_semantic_model_and_retriever()
        print("\nAll unit tests passed successfully!")
    except Exception as e:
        print(f"\nFailed during model/retriever testing: {e}")
        print("Note: If packages are still installing, wait for installation to finish first.")
