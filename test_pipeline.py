import os
import sys
from fastapi.testclient import TestClient

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
import database as db

client = TestClient(app)

def test_root():
    print("Testing Root Redirect...")
    response = client.get("/")
    assert response.status_code == 200
    print("Root: PASS")

def test_api_schema():
    print("Testing DB Schema Endpoint...")
    response = client.get("/api/schema")
    assert response.status_code == 200
    data = response.json()
    assert "schema" in data
    assert "claims" in data["schema"]
    print("Schema: PASS")

def test_api_domain():
    print("Testing Domain configuration read...")
    response = client.get("/api/domain/healthcare_claims")
    assert response.status_code == 200
    data = response.json()
    assert "yaml" in data
    assert "healthcare_claims" in data["yaml"]
    print("Domain config: PASS")

def test_api_query_flow():
    print("Testing full natural-language query flow...")
    # Seed database
    db.seed_database()

    payload = {"question": "What is the total sales amount?"}
    response = client.post("/api/query", json=payload)

    key = os.environ.get("GEMINI_API_KEY")
    if not key or key == "your-google-api-key-here":
        # No real key configured -> endpoint must reject with 500 (no mock fallback)
        assert response.status_code == 500
        print("Query pipeline: PASS (no key -> 500 as expected)")
        return

    # Real key: a live Gemini call should succeed (502 indicates a transient API outage)
    assert response.status_code in (200, 502)
    if response.status_code == 502:
        print("Query pipeline: SKIP (Gemini API transiently unavailable)")
        return

    data = response.json()
    print("Question:", data["question"])
    print("Retrieved Context length:", len(data["retrieved_context"]))
    print("Generated SQL:", data["generated_sql"])
    print("Validated SQL:", data["validated_sql"])
    print("Results Row Count:", len(data["results"]))

    assert data["question"] == payload["question"]
    assert "validated_sql" in data
    print("Query pipeline: PASS")

if __name__ == "__main__":
    try:
        test_root()
        test_api_schema()
        test_api_domain()
        test_api_query_flow()
        print("\nAll integration pipeline tests passed successfully!")
    except Exception as e:
        print(f"\nIntegration pipeline test FAILED: {e}")
        sys.exit(1)
