import os
import sys
import time
import json
from typing import List, Dict, Any, Set
from fastapi.testclient import TestClient

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
import app.core.database as db

# Initialize the test client
client = TestClient(app)

# Helper to normalize and compare SQL result sets
def results_match(res1: List[Dict[str, Any]], res2: List[Dict[str, Any]]) -> bool:
    if len(res1) != len(res2):
        return False
        
    def serialize_row(row):
        # Convert values to strings, sort keys to be column name/order agnostic
        return tuple(sorted((k, str(v) if v is not None else "") for k, v in row.items()))
        
    rows1 = [serialize_row(r) for r in res1]
    rows2 = [serialize_row(r) for r in res2]
    
    # Compare frequencies of each row (order/column agnostic)
    return sorted(rows1) == sorted(rows2)

# Golden Dataset
EVAL_DATASET = [
    {
        "id": 1,
        "question": "Show products that are below reorder level and sitting in warehouses over 80% full",
        "expected_sql": """
            SELECT p.name AS product_name, i.quantity_on_hand, i.reorder_level, w.warehouse_name, w.current_utilization
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            JOIN warehouses w ON i.warehouse_id = w.warehouse_id
            WHERE i.quantity_on_hand < i.reorder_level AND w.current_utilization > 80.0
        """,
        "expected_tables": {"products", "inventory", "warehouses"}
    },
    {
        "id": 2,
        "question": "Compare each department's total payroll against its budget",
        "expected_sql": """
            SELECT d.department_name, SUM(s.base_salary + COALESCE(s.bonus, 0)) AS total_payroll, d.budget
            FROM departments d
            JOIN employees e ON d.department_id = e.department_id
            JOIN salaries s ON e.employee_id = s.employee_id
            GROUP BY d.department_id
        """,
        "expected_tables": {"departments", "employees", "salaries"}
    },
    {
        "id": 3,
        "question": "Reconcile each healthcare claim against payments received",
        "expected_sql": """
            SELECT c.claim_id, m.first_name, m.last_name, p.name AS payer_name, c.amount AS claim_amount, SUM(COALESCE(pm.amount, 0)) AS total_paid
            FROM claims c
            JOIN members m ON c.member_id = m.member_id
            JOIN payers p ON c.payer_id = p.payer_id
            LEFT JOIN payments pm ON c.claim_id = pm.claim_id
            GROUP BY c.claim_id
        """,
        "expected_tables": {"claims", "members", "payers", "payments"}
    },
    {
        "id": 4,
        "question": "Find customers who have a platinum credit card and also have an active loan",
        "expected_sql": """
            SELECT DISTINCT bc.customer_id, bc.first_name, bc.last_name
            FROM bank_customers bc
            JOIN credit_cards cc ON bc.customer_id = cc.customer_id
            JOIN loans l ON bc.customer_id = l.customer_id
            WHERE cc.card_type = 'Platinum' AND l.status = 'Active'
        """,
        "expected_tables": {"bank_customers", "credit_cards", "loans"}
    },
    {
        "id": 5,
        "question": "List courses taught by Professors with their average student GPA",
        "expected_sql": """
            SELECT c.course_name, i.first_name || ' ' || i.last_name AS instructor_name, AVG(s.gpa) AS avg_gpa
            FROM courses c
            JOIN instructors i ON c.instructor_id = i.instructor_id
            JOIN enrollments e ON c.course_id = e.course_id
            JOIN students s ON e.student_id = s.student_id
            WHERE i.rank = 'Professor'
            GROUP BY c.course_id
        """,
        "expected_tables": {"courses", "instructors", "enrollments", "students"}
    },
    {
        "id": 6,
        "question": "Get products with an average rating of 4 or higher and check their stock levels",
        "expected_sql": """
            SELECT p.product_id, p.name, AVG(r.rating) AS avg_rating, SUM(i.quantity_on_hand) AS total_stock
            FROM products p
            JOIN reviews r ON p.product_id = r.product_id
            LEFT JOIN inventory i ON p.product_id = i.product_id
            GROUP BY p.product_id
            HAVING AVG(r.rating) >= 4.0
        """,
        "expected_tables": {"products", "reviews", "inventory"}
    },
    {
        "id": 7,
        "question": "Find the names of Electronics products stored in warehouses that have shipments handled by FastFreight Co.",
        "expected_sql": """
            SELECT DISTINCT p.name AS product_name, w.warehouse_name, s.shipment_id, c.carrier_name
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
            JOIN warehouses w ON i.warehouse_id = w.warehouse_id
            JOIN shipments s ON w.warehouse_id = s.origin_warehouse_id
            JOIN carriers c ON s.carrier_id = c.carrier_id
            WHERE p.category = 'Electronics' AND c.carrier_name = 'FastFreight Co.'
        """,
        "expected_tables": {"products", "inventory", "warehouses", "shipments", "carriers"}
    },
    {
        "id": 8,
        "question": "Identify the top 3 customers by total spending, showing their email and registration date",
        "expected_sql": """
            SELECT c.email, c.registration_date, SUM(o.total_amount) AS total_spent
            FROM ec_customers c
            JOIN orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_id
            ORDER BY total_spent DESC
            LIMIT 3
        """,
        "expected_tables": {"ec_customers", "orders"}
    },
    {
        "id": 9,
        "question": "Find employees who had their leave requests rejected and list their managers",
        "expected_sql": """
            SELECT e.first_name || ' ' || e.last_name AS employee_name, m.first_name || ' ' || m.last_name AS manager_name, lr.leave_type, lr.days_requested
            FROM employees e
            JOIN leave_requests lr ON e.employee_id = lr.employee_id
            LEFT JOIN employees m ON e.manager_id = m.employee_id
            WHERE lr.status = 'Rejected'
        """,
        "expected_tables": {"employees", "leave_requests"}
    },
    {
        "id": 10,
        "question": "Calculate the total deposits and withdrawals for each account type",
        "expected_sql": """
            SELECT a.account_type, t.transaction_type, SUM(t.amount) AS total_amount
            FROM accounts a
            JOIN transactions t ON a.account_id = t.account_id
            GROUP BY a.account_type, t.transaction_type
        """,
        "expected_tables": {"accounts", "transactions"}
    }
]

def run_evaluation():
    print("=== STARTING TEXT-TO-SQL EVALUATION ===")
    
    # 1. Seed database to ensure clean, consistent data
    db.seed_database()
    print("Database seeded successfully.")

    # Force rebuild index so the system has the updated YAML tables
    print("Rebuilding Schema index via /api/index...")
    idx_resp = client.post("/api/index")
    if idx_resp.status_code != 200:
        print(f"  [WARNING] Reindexing failed: {idx_resp.text}")
    else:
        print(f"  [SUCCESS] Indexed {idx_resp.json().get('indexed_tables')} tables.")

    # Check for GEMINI_API_KEY
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your-google-api-key-here":
        print("ERROR: GEMINI_API_KEY is not set or is invalid in .env file.")
        sys.exit(1)

    results = []
    
    total_queries = len(EVAL_DATASET)
    retrieval_successes = 0
    sql_valid_successes = 0
    execution_successes = 0
    accuracy_successes = 0
    
    for item in EVAL_DATASET:
        qid = item["id"]
        question = item["question"]
        expected_sql = item["expected_sql"].strip()
        expected_tables = item["expected_tables"]
        
        print(f"\nEvaluating Query {qid}/{total_queries}: '{question}'...")
        
        # Execute expected SQL to get ground truth
        try:
            expected_results = db.execute_query(expected_sql)
        except Exception as e:
            print(f"  [ERROR] Ground truth expected SQL failed to execute: {e}")
            expected_results = []
            
        start_time = time.time()
        
        # Send post request to /api/query
        response = client.post("/api/query", json={"question": question})
        duration = time.time() - start_time
        
        if response.status_code != 200:
            print(f"  [ERROR] API request failed with status code {response.status_code}")
            try:
                error_detail = response.json().get("detail", "Unknown error")
            except Exception:
                error_detail = response.text
                
            results.append({
                "id": qid,
                "question": question,
                "expected_sql": expected_sql,
                "generated_sql": "",
                "validated_sql": "",
                "retrieved_tables": [],
                "expected_tables": list(expected_tables),
                "retrieval_match": False,
                "sql_valid": False,
                "execution_success": False,
                "accuracy_match": False,
                "error": f"API error (status {response.status_code}): {error_detail}",
                "duration_sec": duration
            })
            continue
            
        data = response.json()
        generated_sql = data.get("generated_sql", "").strip()
        validated_sql = data.get("validated_sql", "").strip()
        validation_error = data.get("validation_error", "")
        actual_results = data.get("results", [])
        retrieved_context = data.get("retrieved_context", "")
        
        # Determine retrieved tables from context
        retrieved_tables = []
        for t in db.get_raw_schema().keys():
            # Check if Table Name matches in retrieved context
            if f"table name: {t}" in retrieved_context.lower():
                retrieved_tables.append(t)
                
        # 1. Retrieval Match Status (did retriever cover all expected tables?)
        retrieved_set = set(retrieved_tables)
        retrieval_match = expected_tables.issubset(retrieved_set)
        if retrieval_match:
            retrieval_successes += 1
            
        # 2. SQL Validation Status (did it generate valid SQL passing validation?)
        sql_valid = len(validated_sql) > 0 and not validation_error
        if sql_valid:
            sql_valid_successes += 1
            
        # 3. SQL Execution Status (did the validated SQL run successfully?)
        # Wait, if sql_valid is true, the server tried to run it.
        # Let's check if the API encountered an execution error (meaning validation_error starts with "Execution failed:")
        execution_success = sql_valid and not (validation_error and "Execution failed" in validation_error)
        if execution_success:
            execution_successes += 1
            
        # 4. Execution Result Accuracy (does execution output match ground truth?)
        accuracy_match = False
        if execution_success:
            accuracy_match = results_match(actual_results, expected_results)
            if accuracy_match:
                accuracy_successes += 1
                
        print(f"  Retrieval Match: {retrieval_match} (Found: {retrieved_tables})")
        print(f"  SQL Generated: {len(generated_sql) > 0} | Valid: {sql_valid}")
        print(f"  Execution: {execution_success}")
        print(f"  Accuracy Match: {accuracy_match}")
        
        results.append({
            "id": qid,
            "question": question,
            "expected_sql": expected_sql,
            "generated_sql": generated_sql,
            "validated_sql": validated_sql,
            "retrieved_tables": retrieved_tables,
            "expected_tables": list(expected_tables),
            "retrieval_match": retrieval_match,
            "sql_valid": sql_valid,
            "execution_success": execution_success,
            "accuracy_match": accuracy_match,
            "error": validation_error,
            "duration_sec": duration
        })
        
    # Calculate rates
    retrieval_rate = (retrieval_successes / total_queries) * 100
    sql_valid_rate = (sql_valid_successes / total_queries) * 100
    execution_rate = (execution_successes / total_queries) * 100
    accuracy_rate = (accuracy_successes / total_queries) * 100
    
    print("\n=== EVALUATION COMPLETED ===")
    print(f"Retrieval Match Rate: {retrieval_rate:.1f}% ({retrieval_successes}/{total_queries})")
    print(f"SQL Validity Rate:    {sql_valid_rate:.1f}% ({sql_valid_successes}/{total_queries})")
    print(f"Execution Success:    {execution_rate:.1f}% ({execution_successes}/{total_queries})")
    print(f"Accuracy Rate:        {accuracy_rate:.1f}% ({accuracy_successes}/{total_queries})")
    
    # Write Markdown Report
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation_report.md")
    
    with open(report_path, "w") as f:
        f.write("# Text-to-SQL Pipeline Evaluation Report\n\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Model Evaluated**: `gemini-2.5-flash`\n")
        f.write(f"**Total Queries**: {total_queries}\n\n")
        
        f.write("## Overall Metrics\n\n")
        f.write("| Metric | Successes | Rate |\n")
        f.write("| :--- | :---: | :---: |\n")
        f.write(f"| **Schema Retrieval Match Rate** | {retrieval_successes} / {total_queries} | **{retrieval_rate:.1f}%** |\n")
        f.write(f"| **SQL Validity Rate** | {sql_valid_successes} / {total_queries} | **{sql_valid_rate:.1f}%** |\n")
        f.write(f"| **Execution Success Rate** | {execution_successes} / {total_queries} | **{execution_rate:.1f}%** |\n")
        f.write(f"| **Execution Result Accuracy Rate** | {accuracy_successes} / {total_queries} | **{accuracy_rate:.1f}%** |\n\n")
        
        f.write("## Detailed Results\n\n")
        
        for r in results:
            f.write(f"### Query {r['id']}: {r['question']}\n\n")
            f.write(f"- **Expected Tables**: `{', '.join(r['expected_tables'])}`\n")
            f.write(f"- **Retrieved Tables**: `{', '.join(r['retrieved_tables'])}`\n")
            
            # Status checkmarks
            ret_chk = "✅ PASS" if r["retrieval_match"] else "❌ FAIL"
            val_chk = "✅ PASS" if r["sql_valid"] else "❌ FAIL"
            exe_chk = "✅ PASS" if r["execution_success"] else "❌ FAIL"
            acc_chk = "✅ PASS" if r["accuracy_match"] else "❌ FAIL"
            
            f.write(f"- **Retrieval Match**: {ret_chk}\n")
            f.write(f"- **SQL Validity**: {val_chk}\n")
            f.write(f"- **Execution Success**: {exe_chk}\n")
            f.write(f"- **Execution Result Accuracy**: {acc_chk}\n")
            f.write(f"- **Time Taken**: {r['duration_sec']:.2f} seconds\n\n")
            
            if r["error"]:
                f.write(f"**Error Details**:\n```\n{r['error']}\n```\n\n")
                
            f.write("**Expected SQL**:\n")
            f.write(f"```sql\n{r['expected_sql']}\n```\n\n")
            
            f.write("**Generated SQL**:\n")
            if r["generated_sql"]:
                f.write(f"```sql\n{r['generated_sql']}\n```\n\n")
            else:
                f.write("*[No SQL generated]*\n\n")
                
            f.write("**Validated SQL** (if different/running):\n")
            if r["validated_sql"]:
                f.write(f"```sql\n{r['validated_sql']}\n```\n\n")
            else:
                f.write("*[No Validated SQL run]*\n\n")
                
            f.write("---\n\n")
            
    print(f"\nMarkdown report generated successfully at: {report_path}")

if __name__ == "__main__":
    run_evaluation()
