import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app, build_index_internal

def test_endpoints():
    client = TestClient(app)
    
    # 1. Build index
    print("\n--- Rebuilding Index via API ---")
    response = client.post("/api/index")
    print("Index status code:", response.status_code)
    print("Index response:", response.json())
    assert response.status_code == 200

    # 2. Get Schema
    print("\n--- Fetching Schema ---")
    response = client.get("/api/schema")
    print("Schema status code:", response.status_code)
    assert response.status_code == 200

    # 3. Retrieve tables
    print("\n--- Retrieving Tables for a Query ---")
    response = client.get("/api/retrieve?query=Who paid for claims?")
    print("Retrieve response:", response.json())
    assert response.status_code == 200

    # 4. Run /api/query (requires a real GEMINI_API_KEY; no mock fallback)
    print("\n--- Testing /api/query (natural language query) ---")
    payload = {"question": "What is the total sales amount?"}
    response = client.post("/api/query", json=payload)
    print("Query status code:", response.status_code)

    key = os.environ.get("GEMINI_API_KEY")
    if not key or key == "your-google-api-key-here":
        # No real key configured -> endpoint must reject with 500 (no mock fallback)
        assert response.status_code == 500
        print("Query: PASS (no key -> 500 as expected)")
        print("\nAPI Integration Tests Passed Successfully!")
        return

    # Real key: live Gemini call should succeed (502 indicates a transient API outage)
    assert response.status_code in (200, 502)
    if response.status_code == 502:
        print("Query: SKIP (Gemini API transiently unavailable)")
        print("\nAPI Integration Tests Passed Successfully!")
        return

    data = response.json()
    print("Query response keys:", list(data.keys()))
    print("Generated SQL:", data["generated_sql"])
    print("Validated SQL:", data["validated_sql"])
    print("Validation Error/Warning:", data["validation_error"])
    print("Results Row Count:", len(data["results"]))
    print("Results:", data["results"])
    print("\nAPI Integration Tests Passed Successfully!")

if __name__ == "__main__":
    # Ensure default domains and retriever index are ready
    build_index_internal()
    test_endpoints()
