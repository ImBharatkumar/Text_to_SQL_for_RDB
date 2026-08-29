import re
from typing import Tuple, List, Set

# Read-only operations keywords to verify and list of banned writing commands
BANNED_KEYWORDS = {
    "insert", "update", "delete", "drop", "alter", "create", "truncate", 
    "replace", "grant", "revoke", "vacuum", "pragma", "reindex"
}

DEFAULT_WHITELIST_TABLES = {
    # --- healthcare_claims ---
    "members", "payers", "claims", "payments",
    # --- retail_sales ---
    "sales",
    # --- finance_banking ---
    "bank_customers", "accounts", "transactions", "loans", "branches", "credit_cards",
    # --- ecommerce ---
    "ec_customers", "products", "orders", "order_items", "reviews", "inventory",
    # --- hr_payroll ---
    "departments", "employees", "salaries", "leave_requests", "performance_reviews",
    # --- logistics ---
    "carriers", "warehouses", "routes", "shipments", "tracking_events",
    # --- education ---
    "students", "instructors", "courses", "enrollments", "grades", "attendance","departments"
}

def validate_sql(sql: str, whitelist_tables: Set[str] = DEFAULT_WHITELIST_TABLES, max_limit: int = 100) -> Tuple[bool, str, str]:
    """
    Validates a SQL query:
    1. Blocks non-read-only commands.
    2. Enforces that only whitelisted tables are queried.
    3. Appends/enforces a LIMIT clause.
    
    Returns (is_valid, modified_sql, error_message).
    """
    # Clean SQL string
    sql_clean = sql.strip().strip(";").strip()
    
    # Check for empty query
    if not sql_clean:
        return False, "", "Empty SQL query."
        
    # Check for banned keywords
    # Use word boundary to avoid false positives (e.g., "created_at" containing "create")
    for keyword in BANNED_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, sql_clean, re.IGNORECASE):
            return False, "", f"Security Violation: Command '{keyword.upper()}' is not allowed."

    # Parse tables referenced in the query using a simple regex-based approach
    # Looking for keywords like FROM or JOIN followed by table names.
    # Note: For production, a robust SQL parser like sqlglot or sqlparse is preferred,
    # but for a lightweight MVP, regex works for standard queries.
    referenced_tables = set()
    
    # Find words following FROM or JOIN
    table_matches = re.findall(
        r"\b(?:from|join)\s+([a-zA-Z0-9_\`\"\[\]\.]+)", 
        sql_clean, 
        re.IGNORECASE
    )
    
    for match in table_matches:
        # Strip brackets, quotes, schemas
        table_name = match.strip("`\"[]").split(".")[-1].lower()
        referenced_tables.add(table_name)
        
    # If no tables were detected, we still want to make sure it's valid, but let's check what we did find
    for table in referenced_tables:
        if table not in whitelist_tables:
            return False, "", f"Access Violation: Table '{table}' is not in the whitelist."

    # Enforce LIMIT
    # Check if query already has a LIMIT clause
    limit_match = re.search(r"\blimit\s+(\d+)\b", sql_clean, re.IGNORECASE)
    if limit_match:
        current_limit = int(limit_match.group(1))
        if current_limit > max_limit:
            # Enforce maximum limit
            modified_sql = re.sub(r"\blimit\s+\d+\b", f"LIMIT {max_limit}", sql_clean, flags=re.IGNORECASE)
        else:
            modified_sql = sql_clean
    else:
        # Append LIMIT
        modified_sql = f"{sql_clean} LIMIT {max_limit}"
        
    # Add trailing semicolon back for standard SQL compliance
    modified_sql += ";"
    
    return True, modified_sql, ""
