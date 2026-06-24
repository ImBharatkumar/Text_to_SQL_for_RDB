import sqlite3
import os
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def seed_database():
    """Seeds the database with sample schema and data for all domains."""
    conn = get_connection()
    cursor = conn.cursor()

    # -------------------------------------------------------------------------
    # DOMAIN: healthcare_claims
    # -------------------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (
        member_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        birth_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payers (
        payer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        claim_id TEXT PRIMARY KEY,
        member_id TEXT,
        payer_id TEXT,
        service_date TEXT,
        amount REAL,
        status TEXT,
        FOREIGN KEY(member_id) REFERENCES members(member_id),
        FOREIGN KEY(payer_id) REFERENCES payers(payer_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        payment_id TEXT PRIMARY KEY,
        claim_id TEXT,
        amount REAL,
        payment_date TEXT,
        method TEXT,
        FOREIGN KEY(claim_id) REFERENCES claims(claim_id)
    )
    """)

    # -------------------------------------------------------------------------
    # DOMAIN: retail_sales
    # -------------------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER,
        price REAL,
        order_date TEXT
    )
    """)

    # -------------------------------------------------------------------------
    # DOMAIN: finance_banking
    # -------------------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bank_customers (
        customer_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        date_of_birth TEXT,
        kyc_status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_id TEXT PRIMARY KEY,
        customer_id TEXT,
        account_type TEXT,
        balance REAL,
        currency TEXT,
        opened_date TEXT,
        status TEXT,
        FOREIGN KEY(customer_id) REFERENCES bank_customers(customer_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        account_id TEXT,
        transaction_type TEXT,
        amount REAL,
        transaction_date TEXT,
        description TEXT,
        reference_number TEXT,
        FOREIGN KEY(account_id) REFERENCES accounts(account_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        loan_id TEXT PRIMARY KEY,
        customer_id TEXT,
        loan_type TEXT,
        principal_amount REAL,
        interest_rate REAL,
        term_months INTEGER,
        monthly_payment REAL,
        disbursement_date TEXT,
        status TEXT,
        FOREIGN KEY(customer_id) REFERENCES bank_customers(customer_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS branches (
        branch_id TEXT PRIMARY KEY,
        branch_name TEXT NOT NULL,
        city TEXT,
        state TEXT,
        address TEXT,
        phone TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS credit_cards (
        card_id TEXT PRIMARY KEY,
        customer_id TEXT,
        card_type TEXT,
        credit_limit REAL,
        current_balance REAL,
        due_date TEXT,
        rewards_points INTEGER,
        FOREIGN KEY(customer_id) REFERENCES bank_customers(customer_id)
    )
    """)

    # -------------------------------------------------------------------------
    # DOMAIN: ecommerce
    # -------------------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ec_customers (
        customer_id TEXT PRIMARY KEY,
        email TEXT,
        username TEXT,
        registration_date TEXT,
        country TEXT,
        loyalty_tier TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        brand TEXT,
        unit_price REAL,
        cost_price REAL,
        sku TEXT,
        is_active INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT,
        order_date TEXT,
        total_amount REAL,
        discount_amount REAL,
        shipping_cost REAL,
        status TEXT,
        shipping_address TEXT,
        FOREIGN KEY(customer_id) REFERENCES ec_customers(customer_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        item_id TEXT PRIMARY KEY,
        order_id TEXT,
        product_id TEXT,
        quantity INTEGER,
        unit_price REAL,
        subtotal REAL,
        FOREIGN KEY(order_id) REFERENCES orders(order_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        review_id TEXT PRIMARY KEY,
        product_id TEXT,
        customer_id TEXT,
        rating INTEGER,
        review_text TEXT,
        review_date TEXT,
        helpful_votes INTEGER,
        FOREIGN KEY(product_id) REFERENCES products(product_id),
        FOREIGN KEY(customer_id) REFERENCES ec_customers(customer_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        inventory_id TEXT PRIMARY KEY,
        product_id TEXT,
        warehouse_id TEXT,
        quantity_on_hand INTEGER,
        reorder_level INTEGER,
        last_restocked TEXT,
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )
    """)

    # -------------------------------------------------------------------------
    # DOMAIN: hr_payroll
    # -------------------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        department_id TEXT PRIMARY KEY,
        department_name TEXT NOT NULL,
        location TEXT,
        head_count INTEGER,
        budget REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        hire_date TEXT,
        department_id TEXT,
        job_title TEXT,
        manager_id TEXT,
        employment_type TEXT,
        status TEXT,
        FOREIGN KEY(department_id) REFERENCES departments(department_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS salaries (
        salary_id TEXT PRIMARY KEY,
        employee_id TEXT,
        base_salary REAL,
        bonus REAL,
        effective_date TEXT,
        end_date TEXT,
        currency TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leave_requests (
        leave_id TEXT PRIMARY KEY,
        employee_id TEXT,
        leave_type TEXT,
        start_date TEXT,
        end_date TEXT,
        days_requested INTEGER,
        status TEXT,
        approved_by TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS performance_reviews (
        review_id TEXT PRIMARY KEY,
        employee_id TEXT,
        reviewer_id TEXT,
        review_period TEXT,
        overall_rating REAL,
        comments TEXT,
        review_date TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
    )
    """)

    # -------------------------------------------------------------------------
    # DOMAIN: logistics
    # -------------------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS carriers (
        carrier_id TEXT PRIMARY KEY,
        carrier_name TEXT NOT NULL,
        service_type TEXT,
        contact_email TEXT,
        rating REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warehouses (
        warehouse_id TEXT PRIMARY KEY,
        warehouse_name TEXT NOT NULL,
        city TEXT,
        state TEXT,
        capacity_units INTEGER,
        current_utilization REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS routes (
        route_id TEXT PRIMARY KEY,
        origin_city TEXT,
        destination_city TEXT,
        distance_km REAL,
        estimated_hours REAL,
        active INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shipments (
        shipment_id TEXT PRIMARY KEY,
        origin_warehouse_id TEXT,
        destination_address TEXT,
        carrier_id TEXT,
        route_id TEXT,
        weight_kg REAL,
        status TEXT,
        shipped_date TEXT,
        estimated_delivery TEXT,
        actual_delivery TEXT,
        FOREIGN KEY(origin_warehouse_id) REFERENCES warehouses(warehouse_id),
        FOREIGN KEY(carrier_id) REFERENCES carriers(carrier_id),
        FOREIGN KEY(route_id) REFERENCES routes(route_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracking_events (
        event_id TEXT PRIMARY KEY,
        shipment_id TEXT,
        event_type TEXT,
        event_timestamp TEXT,
        location TEXT,
        notes TEXT,
        FOREIGN KEY(shipment_id) REFERENCES shipments(shipment_id)
    )
    """)

    # -------------------------------------------------------------------------
    # DOMAIN: education
    # -------------------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        enrollment_date TEXT,
        program TEXT,
        gpa REAL,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instructors (
        instructor_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        department TEXT,
        rank TEXT,
        hire_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id TEXT PRIMARY KEY,
        course_code TEXT,
        course_name TEXT NOT NULL,
        credits INTEGER,
        department TEXT,
        instructor_id TEXT,
        semester TEXT,
        max_enrollment INTEGER,
        FOREIGN KEY(instructor_id) REFERENCES instructors(instructor_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id TEXT PRIMARY KEY,
        student_id TEXT,
        course_id TEXT,
        enrollment_date TEXT,
        status TEXT,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grades (
        grade_id TEXT PRIMARY KEY,
        enrollment_id TEXT,
        assessment_type TEXT,
        score REAL,
        max_score REAL,
        letter_grade TEXT,
        graded_date TEXT,
        FOREIGN KEY(enrollment_id) REFERENCES enrollments(enrollment_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id TEXT PRIMARY KEY,
        enrollment_id TEXT,
        class_date TEXT,
        status TEXT,
        FOREIGN KEY(enrollment_id) REFERENCES enrollments(enrollment_id)
    )
    """)

    # =========================================================================
    # SEED DATA
    # =========================================================================

    # --- healthcare_claims ---
    cursor.execute("SELECT COUNT(*) FROM members")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO members VALUES (?, ?, ?, ?)", [
            ("M001", "John", "Doe", "1985-05-12"),
            ("M002", "Jane", "Smith", "1990-08-24"),
            ("M003", "Alice", "Jones", "1978-11-03"),
            ("M004", "Bob", "Brown", "1965-02-15"),
            ("M005", "Carol", "White", "1992-03-07"),
            ("M006", "David", "Lee", "1988-09-19"),
        ])

    cursor.execute("SELECT COUNT(*) FROM payers")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO payers VALUES (?, ?, ?)", [
            ("P001", "Blue Cross", "Commercial"),
            ("P002", "UnitedHealth", "Commercial"),
            ("P003", "Medicare", "Government"),
            ("P004", "Medicaid", "Government"),
            ("P005", "Aetna", "Commercial"),
        ])

    cursor.execute("SELECT COUNT(*) FROM claims")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?)", [
            ("C001", "M001", "P001", "2026-01-10", 150.00, "Paid"),
            ("C002", "M001", "P002", "2026-02-15", 250.00, "Pending"),
            ("C003", "M002", "P001", "2026-03-01", 1200.00, "Denied"),
            ("C004", "M003", "P003", "2026-03-12", 500.00, "Paid"),
            ("C005", "M004", "P004", "2026-04-05", 320.00, "Paid"),
            ("C006", "M005", "P005", "2026-04-20", 780.00, "Pending"),
            ("C007", "M006", "P002", "2026-05-01", 95.00, "Denied"),
            ("C008", "M003", "P001", "2026-05-15", 2100.00, "Paid"),
        ])

    cursor.execute("SELECT COUNT(*) FROM payments")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO payments VALUES (?, ?, ?, ?, ?)", [
            ("PAY001", "C001", 150.00, "2026-01-20", "EFT"),
            ("PAY002", "C004", 500.00, "2026-03-25", "Check"),
            ("PAY003", "C005", 320.00, "2026-04-15", "EFT"),
            ("PAY004", "C008", 2100.00, "2026-05-28", "Wire"),
        ])

    # --- retail_sales ---
    cursor.execute("SELECT COUNT(*) FROM sales")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)", [
            ("O001", "CUST001", "Laptop", 1, 1200.00, "2026-04-01"),
            ("O002", "CUST002", "Mouse", 2, 25.00, "2026-04-02"),
            ("O003", "CUST001", "Monitor", 1, 300.00, "2026-04-03"),
            ("O004", "CUST003", "Keyboard", 1, 75.00, "2026-04-05"),
            ("O005", "CUST004", "Webcam", 1, 89.99, "2026-04-10"),
            ("O006", "CUST002", "USB Hub", 3, 19.99, "2026-04-12"),
        ])

    # --- finance_banking ---
    cursor.execute("SELECT COUNT(*) FROM bank_customers")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO bank_customers VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("BC001", "Emma", "Taylor", "emma.t@email.com", "555-0101", "1983-06-14", "Verified"),
            ("BC002", "Liam", "Johnson", "liam.j@email.com", "555-0102", "1975-11-22", "Verified"),
            ("BC003", "Olivia", "Martinez", "olivia.m@email.com", "555-0103", "1995-03-08", "Pending"),
            ("BC004", "Noah", "Garcia", "noah.g@email.com", "555-0104", "1968-07-30", "Verified"),
            ("BC005", "Ava", "Wilson", "ava.w@email.com", "555-0105", "2000-01-15", "Rejected"),
            ("BC006", "James", "Anderson", "james.a@email.com", "555-0106", "1990-09-25", "Verified"),
        ])

    cursor.execute("SELECT COUNT(*) FROM accounts")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("ACC001", "BC001", "Savings", 15200.50, "USD", "2020-01-10", "Active"),
            ("ACC002", "BC001", "Checking", 3400.00, "USD", "2020-01-10", "Active"),
            ("ACC003", "BC002", "Savings", 87000.00, "USD", "2015-06-01", "Active"),
            ("ACC004", "BC003", "Checking", 540.25, "USD", "2023-08-15", "Active"),
            ("ACC005", "BC004", "Money Market", 250000.00, "USD", "2010-03-22", "Active"),
            ("ACC006", "BC005", "Checking", 0.00, "USD", "2024-02-01", "Frozen"),
            ("ACC007", "BC006", "Savings", 9800.00, "USD", "2019-11-11", "Active"),
        ])

    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("TXN001", "ACC001", "Deposit", 5000.00, "2026-01-05", "Payroll deposit", "REF-100"),
            ("TXN002", "ACC001", "Withdrawal", 200.00, "2026-01-10", "ATM withdrawal", "REF-101"),
            ("TXN003", "ACC002", "Transfer", 1000.00, "2026-01-15", "Transfer to savings", "REF-102"),
            ("TXN004", "ACC003", "Deposit", 12000.00, "2026-02-01", "Investment return", "REF-103"),
            ("TXN005", "ACC004", "Fee", 15.00, "2026-02-10", "Monthly maintenance fee", "REF-104"),
            ("TXN006", "ACC005", "Withdrawal", 5000.00, "2026-03-01", "Wire transfer", "REF-105"),
            ("TXN007", "ACC007", "Deposit", 2500.00, "2026-03-15", "Payroll deposit", "REF-106"),
            ("TXN008", "ACC002", "Deposit", 300.00, "2026-04-01", "Refund credit", "REF-107"),
        ])

    cursor.execute("SELECT COUNT(*) FROM loans")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO loans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            ("LN001", "BC001", "Personal", 10000.00, 7.5, 36, 310.94, "2024-06-01", "Active"),
            ("LN002", "BC002", "Mortgage", 350000.00, 4.25, 360, 1722.25, "2018-09-01", "Active"),
            ("LN003", "BC004", "Auto", 22000.00, 5.9, 60, 424.07, "2023-01-15", "Active"),
            ("LN004", "BC006", "Student", 15000.00, 3.75, 120, 150.65, "2022-08-20", "Active"),
            ("LN005", "BC003", "Personal", 5000.00, 12.0, 24, 234.85, "2025-03-10", "Active"),
        ])

    cursor.execute("SELECT COUNT(*) FROM branches")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO branches VALUES (?, ?, ?, ?, ?, ?)", [
            ("BR001", "Downtown Branch", "New York", "NY", "100 Wall St", "212-555-0001"),
            ("BR002", "West Side Branch", "Los Angeles", "CA", "500 Sunset Blvd", "310-555-0002"),
            ("BR003", "Midtown Branch", "Chicago", "IL", "200 Michigan Ave", "312-555-0003"),
            ("BR004", "South Branch", "Houston", "TX", "800 Main St", "713-555-0004"),
        ])

    cursor.execute("SELECT COUNT(*) FROM credit_cards")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO credit_cards VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("CC001", "BC001", "Gold", 10000.00, 2340.50, "2026-07-15", 4500),
            ("CC002", "BC002", "Platinum", 25000.00, 8900.00, "2026-07-20", 18200),
            ("CC003", "BC003", "Standard", 2000.00, 1850.00, "2026-07-10", 320),
            ("CC004", "BC004", "Platinum", 50000.00, 12000.00, "2026-07-25", 95000),
            ("CC005", "BC006", "Standard", 1500.00, 0.00, "2026-07-05", 750),
        ])

    # --- ecommerce ---
    cursor.execute("SELECT COUNT(*) FROM ec_customers")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO ec_customers VALUES (?, ?, ?, ?, ?, ?)", [
            ("EC001", "alice@shop.com", "alice99", "2022-01-10", "US", "Gold"),
            ("EC002", "bob@shop.com", "bobby_b", "2021-05-22", "CA", "Silver"),
            ("EC003", "carol@shop.com", "carol_c", "2023-03-14", "UK", "Bronze"),
            ("EC004", "dave@shop.com", "dave_d", "2020-11-01", "US", "Platinum"),
            ("EC005", "eve@shop.com", "eve_e", "2024-02-28", "AU", "Bronze"),
            ("EC006", "frank@shop.com", "frank_f", "2019-07-19", "US", "Platinum"),
        ])

    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            ("PRD001", "Wireless Headphones", "Electronics", "SoundMax", 149.99, 65.00, "SM-WH100", 1),
            ("PRD002", "Running Shoes", "Footwear", "SpeedFoot", 89.99, 35.00, "SF-RS200", 1),
            ("PRD003", "Python Programming Book", "Books", "TechPress", 49.99, 12.00, "TP-PY300", 1),
            ("PRD004", "Yoga Mat", "Sports", "FlexFit", 39.99, 10.00, "FF-YM400", 1),
            ("PRD005", "Bluetooth Speaker", "Electronics", "SoundMax", 79.99, 28.00, "SM-BS500", 1),
            ("PRD006", "Coffee Maker", "Appliances", "BrewKing", 129.99, 55.00, "BK-CM600", 1),
            ("PRD007", "Winter Jacket", "Clothing", "WarmWear", 199.99, 80.00, "WW-WJ700", 1),
            ("PRD008", "Mechanical Keyboard", "Electronics", "TypePro", 109.99, 42.00, "TP-MK800", 0),
        ])

    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            ("ORD001", "EC001", "2026-01-15", 239.98, 10.00, 9.99, "Delivered", "123 Main St, Austin TX"),
            ("ORD002", "EC002", "2026-02-03", 89.99, 0.00, 5.99, "Shipped", "456 Oak Ave, Toronto CA"),
            ("ORD003", "EC004", "2026-02-20", 389.97, 30.00, 0.00, "Delivered", "789 Park Rd, Seattle WA"),
            ("ORD004", "EC003", "2026-03-10", 49.99, 5.00, 3.99, "Delivered", "321 Elm St, London UK"),
            ("ORD005", "EC001", "2026-03-25", 129.99, 0.00, 7.99, "Processing", "123 Main St, Austin TX"),
            ("ORD006", "EC006", "2026-04-05", 309.98, 20.00, 0.00, "Delivered", "654 Pine St, Miami FL"),
        ])

    cursor.execute("SELECT COUNT(*) FROM order_items")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)", [
            ("ITM001", "ORD001", "PRD001", 1, 149.99, 149.99),
            ("ITM002", "ORD001", "PRD004", 2, 39.99, 79.98),
            ("ITM003", "ORD002", "PRD002", 1, 89.99, 89.99),
            ("ITM004", "ORD003", "PRD001", 1, 149.99, 149.99),
            ("ITM005", "ORD003", "PRD006", 1, 129.99, 129.99),
            ("ITM006", "ORD003", "PRD004", 1, 39.99, 39.99),
            ("ITM007", "ORD004", "PRD003", 1, 49.99, 49.99),
            ("ITM008", "ORD005", "PRD006", 1, 129.99, 129.99),
            ("ITM009", "ORD006", "PRD005", 2, 79.99, 159.98),
            ("ITM010", "ORD006", "PRD007", 1, 199.99, 199.99),
        ])

    cursor.execute("SELECT COUNT(*) FROM reviews")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("REV001", "PRD001", "EC001", 5, "Amazing sound quality!", "2026-01-25", 12),
            ("REV002", "PRD002", "EC002", 4, "Very comfortable for long runs.", "2026-02-15", 8),
            ("REV003", "PRD003", "EC003", 5, "Best Python book for beginners.", "2026-03-20", 20),
            ("REV004", "PRD004", "EC001", 3, "Good mat but slips a bit.", "2026-02-05", 4),
            ("REV005", "PRD006", "EC004", 4, "Makes great coffee every morning.", "2026-03-01", 6),
            ("REV006", "PRD005", "EC006", 5, "Loud and clear sound!", "2026-04-15", 9),
        ])

    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?)", [
            ("INV001", "PRD001", "WH001", 145, 20, "2026-03-01"),
            ("INV002", "PRD002", "WH001", 230, 30, "2026-02-15"),
            ("INV003", "PRD003", "WH002", 560, 50, "2026-01-20"),
            ("INV004", "PRD004", "WH002", 88, 15, "2026-03-10"),
            ("INV005", "PRD005", "WH001", 195, 25, "2026-04-01"),
            ("INV006", "PRD006", "WH003", 42, 10, "2026-02-28"),
            ("INV007", "PRD007", "WH003", 67, 10, "2026-01-10"),
            ("INV008", "PRD008", "WH002", 0, 10, "2025-12-01"),
        ])

    # --- hr_payroll ---
    cursor.execute("SELECT COUNT(*) FROM departments")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?, ?)", [
            ("DEPT001", "Engineering", "San Francisco", 45, 4500000.00),
            ("DEPT002", "Finance", "New York", 18, 1800000.00),
            ("DEPT003", "Human Resources", "Chicago", 12, 950000.00),
            ("DEPT004", "Marketing", "Los Angeles", 22, 2200000.00),
            ("DEPT005", "Operations", "Dallas", 30, 3000000.00),
        ])

    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            ("EMP001", "Sarah", "Connor", "sarah.c@corp.com", "2018-03-01", "DEPT001", "Senior Engineer", None, "Full-Time", "Active"),
            ("EMP002", "Mike", "Ross", "mike.r@corp.com", "2020-07-15", "DEPT002", "Financial Analyst", None, "Full-Time", "Active"),
            ("EMP003", "Rachel", "Zane", "rachel.z@corp.com", "2019-11-01", "DEPT003", "HR Manager", None, "Full-Time", "Active"),
            ("EMP004", "Harvey", "Specter", "harvey.s@corp.com", "2015-01-10", "DEPT001", "Engineering Manager", None, "Full-Time", "Active"),
            ("EMP005", "Donna", "Paulsen", "donna.p@corp.com", "2016-05-20", "DEPT003", "HR Specialist", "EMP003", "Full-Time", "Active"),
            ("EMP006", "Luis", "Litt", "luis.l@corp.com", "2021-09-01", "DEPT002", "Senior Analyst", "EMP002", "Full-Time", "Active"),
            ("EMP007", "Jessica", "Pearson", "jessica.p@corp.com", "2010-04-15", "DEPT004", "VP Marketing", None, "Full-Time", "Active"),
            ("EMP008", "Alex", "Williams", "alex.w@corp.com", "2023-02-01", "DEPT001", "Junior Engineer", "EMP004", "Full-Time", "Active"),
        ])

    cursor.execute("SELECT COUNT(*) FROM salaries")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO salaries VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("SAL001", "EMP001", 120000.00, 15000.00, "2024-01-01", None, "USD"),
            ("SAL002", "EMP002", 95000.00, 10000.00, "2024-01-01", None, "USD"),
            ("SAL003", "EMP003", 110000.00, 12000.00, "2024-01-01", None, "USD"),
            ("SAL004", "EMP004", 160000.00, 25000.00, "2024-01-01", None, "USD"),
            ("SAL005", "EMP005", 85000.00, 8000.00, "2024-01-01", None, "USD"),
            ("SAL006", "EMP006", 105000.00, 11000.00, "2024-01-01", None, "USD"),
            ("SAL007", "EMP007", 180000.00, 30000.00, "2024-01-01", None, "USD"),
            ("SAL008", "EMP008", 72000.00, 5000.00, "2023-02-01", None, "USD"),
        ])

    cursor.execute("SELECT COUNT(*) FROM leave_requests")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO leave_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            ("LV001", "EMP001", "Annual", "2026-07-01", "2026-07-10", 10, "Approved", "EMP004"),
            ("LV002", "EMP002", "Sick", "2026-05-12", "2026-05-13", 2, "Approved", "EMP003"),
            ("LV003", "EMP008", "Annual", "2026-06-15", "2026-06-19", 5, "Pending", "EMP004"),
            ("LV004", "EMP005", "Maternity", "2026-08-01", "2026-10-31", 65, "Approved", "EMP003"),
            ("LV005", "EMP006", "Annual", "2026-07-20", "2026-07-25", 6, "Rejected", "EMP002"),
        ])

    cursor.execute("SELECT COUNT(*) FROM performance_reviews")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO performance_reviews VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("PR001", "EMP001", "EMP004", "Annual-2025", 4.5, "Exceptional performance. Ready for promotion.", "2026-01-15"),
            ("PR002", "EMP002", "EMP003", "Annual-2025", 3.8, "Good analytical skills. Needs improvement in communication.", "2026-01-20"),
            ("PR003", "EMP008", "EMP004", "Annual-2025", 3.2, "Solid first year. Growing quickly.", "2026-01-22"),
            ("PR004", "EMP005", "EMP003", "Annual-2025", 4.0, "Excellent team player.", "2026-01-18"),
            ("PR005", "EMP007", "EMP003", "Annual-2025", 4.8, "Outstanding leadership and strategic vision.", "2026-01-25"),
        ])

    # --- logistics ---
    cursor.execute("SELECT COUNT(*) FROM carriers")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO carriers VALUES (?, ?, ?, ?, ?)", [
            ("CAR001", "FastFreight Co.", "Express", "ops@fastfreight.com", 4.7),
            ("CAR002", "GlobalShip Inc.", "Standard", "ops@globalship.com", 4.2),
            ("CAR003", "QuickDeliver LLC", "Overnight", "ops@quickdeliver.com", 4.9),
            ("CAR004", "EcoLogistics", "Standard", "ops@ecologistics.com", 3.8),
        ])

    cursor.execute("SELECT COUNT(*) FROM warehouses")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO warehouses VALUES (?, ?, ?, ?, ?, ?)", [
            ("WH001", "East Coast Hub", "Newark", "NJ", 50000, 72.5),
            ("WH002", "West Coast Hub", "Los Angeles", "CA", 75000, 58.0),
            ("WH003", "Central Hub", "Memphis", "TN", 100000, 83.0),
            ("WH004", "Southern Hub", "Atlanta", "GA", 40000, 45.5),
        ])

    cursor.execute("SELECT COUNT(*) FROM routes")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO routes VALUES (?, ?, ?, ?, ?, ?)", [
            ("RT001", "Newark", "Chicago", 1270.0, 14.5, 1),
            ("RT002", "Los Angeles", "Seattle", 1750.0, 20.0, 1),
            ("RT003", "Memphis", "Dallas", 800.0, 9.0, 1),
            ("RT004", "Atlanta", "Miami", 660.0, 7.5, 1),
            ("RT005", "Newark", "Atlanta", 1390.0, 15.5, 1),
            ("RT006", "Los Angeles", "Las Vegas", 435.0, 5.0, 0),
        ])

    cursor.execute("SELECT COUNT(*) FROM shipments")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO shipments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            ("SHP001", "WH001", "100 State St, Chicago IL", "CAR001", "RT001", 12.5, "Delivered", "2026-04-01", "2026-04-04", "2026-04-04"),
            ("SHP002", "WH002", "500 Pike St, Seattle WA", "CAR002", "RT002", 5.2, "In Transit", "2026-05-10", "2026-05-15", None),
            ("SHP003", "WH003", "200 Commerce St, Dallas TX", "CAR001", "RT003", 30.0, "Delivered", "2026-04-20", "2026-04-22", "2026-04-22"),
            ("SHP004", "WH004", "888 Brickell Ave, Miami FL", "CAR003", "RT004", 2.8, "Delivered", "2026-05-01", "2026-05-02", "2026-05-02"),
            ("SHP005", "WH001", "300 Peachtree St, Atlanta GA", "CAR004", "RT005", 18.0, "Failed", "2026-05-05", "2026-05-09", None),
            ("SHP006", "WH002", "750 Las Vegas Blvd, Las Vegas NV", "CAR001", "RT006", 7.5, "Picked Up", "2026-06-01", "2026-06-02", None),
        ])

    cursor.execute("SELECT COUNT(*) FROM tracking_events")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO tracking_events VALUES (?, ?, ?, ?, ?, ?)", [
            ("EVT001", "SHP001", "Picked Up", "2026-04-01 09:00", "Newark, NJ", None),
            ("EVT002", "SHP001", "Arrived at Hub", "2026-04-02 14:00", "Philadelphia, PA", None),
            ("EVT003", "SHP001", "Out for Delivery", "2026-04-04 08:00", "Chicago, IL", None),
            ("EVT004", "SHP001", "Delivered", "2026-04-04 13:30", "Chicago, IL", "Left at front door"),
            ("EVT005", "SHP002", "Picked Up", "2026-05-10 10:00", "Los Angeles, CA", None),
            ("EVT006", "SHP002", "Arrived at Hub", "2026-05-12 18:00", "Sacramento, CA", None),
            ("EVT007", "SHP004", "Picked Up", "2026-05-01 08:30", "Atlanta, GA", None),
            ("EVT008", "SHP004", "Delivered", "2026-05-02 11:00", "Miami, FL", "Signed by recipient"),
            ("EVT009", "SHP005", "Picked Up", "2026-05-05 09:00", "Newark, NJ", None),
            ("EVT010", "SHP005", "Delivery Failed", "2026-05-09 14:00", "Atlanta, GA", "Recipient not available"),
        ])

    # --- education ---
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            ("STU001", "Laura", "Palmer", "laura.p@uni.edu", "2022-09-01", "Computer Science", 3.8, "Active"),
            ("STU002", "James", "Hurley", "james.h@uni.edu", "2021-09-01", "Business", 3.2, "Active"),
            ("STU003", "Donna", "Hayward", "donna.h@uni.edu", "2023-01-15", "Nursing", 3.9, "Active"),
            ("STU004", "Bobby", "Briggs", "bobby.b@uni.edu", "2020-09-01", "Business", 2.7, "Active"),
            ("STU005", "Audrey", "Horne", "audrey.h@uni.edu", "2022-09-01", "Psychology", 3.6, "Active"),
            ("STU006", "Cooper", "Dale", "cooper.d@uni.edu", "2019-09-01", "Computer Science", 3.5, "Graduated"),
        ])

    cursor.execute("SELECT COUNT(*) FROM instructors")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO instructors VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("INS001", "Gordon", "Cole", "g.cole@uni.edu", "Computer Science", "Professor", "2005-08-01"),
            ("INS002", "Albert", "Rosenfield", "a.rosenfield@uni.edu", "Nursing", "Associate Professor", "2010-01-15"),
            ("INS003", "Phillip", "Jeffries", "p.jeffries@uni.edu", "Business", "Assistant Professor", "2018-09-01"),
            ("INS004", "Windom", "Earle", "w.earle@uni.edu", "Psychology", "Professor", "2000-03-01"),
        ])

    cursor.execute("SELECT COUNT(*) FROM courses")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            ("CRS001", "CS101", "Intro to Programming", 3, "Computer Science", "INS001", "Fall-2025", 40),
            ("CRS002", "CS301", "Database Systems", 3, "Computer Science", "INS001", "Spring-2026", 35),
            ("CRS003", "NUR201", "Clinical Practice I", 4, "Nursing", "INS002", "Fall-2025", 25),
            ("CRS004", "BUS101", "Business Fundamentals", 3, "Business", "INS003", "Fall-2025", 50),
            ("CRS005", "BUS305", "Financial Management", 3, "Business", "INS003", "Spring-2026", 40),
            ("CRS006", "PSY101", "Introduction to Psychology", 3, "Psychology", "INS004", "Fall-2025", 60),
            ("CRS007", "PSY302", "Cognitive Psychology", 3, "Psychology", "INS004", "Spring-2026", 30),
        ])

    cursor.execute("SELECT COUNT(*) FROM enrollments")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO enrollments VALUES (?, ?, ?, ?, ?)", [
            ("ENR001", "STU001", "CRS001", "2025-08-25", "Completed"),
            ("ENR002", "STU001", "CRS002", "2026-01-10", "Enrolled"),
            ("ENR003", "STU002", "CRS004", "2025-08-25", "Completed"),
            ("ENR004", "STU002", "CRS005", "2026-01-10", "Enrolled"),
            ("ENR005", "STU003", "CRS003", "2025-08-25", "Completed"),
            ("ENR006", "STU004", "CRS004", "2025-08-25", "Withdrawn"),
            ("ENR007", "STU005", "CRS006", "2025-08-25", "Completed"),
            ("ENR008", "STU005", "CRS007", "2026-01-10", "Enrolled"),
            ("ENR009", "STU006", "CRS001", "2019-09-01", "Completed"),
            ("ENR010", "STU001", "CRS006", "2025-08-25", "Completed"),
        ])

    cursor.execute("SELECT COUNT(*) FROM grades")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO grades VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("GRD001", "ENR001", "Final", 92.0, 100.0, "A-", "2025-12-15"),
            ("GRD002", "ENR001", "Midterm", 88.0, 100.0, "B+", "2025-10-20"),
            ("GRD003", "ENR003", "Final", 78.0, 100.0, "C+", "2025-12-15"),
            ("GRD004", "ENR005", "Final", 95.0, 100.0, "A", "2025-12-18"),
            ("GRD005", "ENR007", "Final", 85.0, 100.0, "B", "2025-12-14"),
            ("GRD006", "ENR009", "Final", 91.0, 100.0, "A-", "2023-12-16"),
            ("GRD007", "ENR010", "Final", 80.0, 100.0, "B-", "2025-12-14"),
        ])

    cursor.execute("SELECT COUNT(*) FROM attendance")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO attendance VALUES (?, ?, ?, ?)", [
            ("ATT001", "ENR001", "2025-09-03", "Present"),
            ("ATT002", "ENR001", "2025-09-10", "Present"),
            ("ATT003", "ENR001", "2025-09-17", "Absent"),
            ("ATT004", "ENR003", "2025-09-03", "Present"),
            ("ATT005", "ENR003", "2025-09-10", "Late"),
            ("ATT006", "ENR005", "2025-09-04", "Present"),
            ("ATT007", "ENR005", "2025-09-11", "Present"),
            ("ATT008", "ENR007", "2025-09-05", "Present"),
            ("ATT009", "ENR007", "2025-09-12", "Excused"),
            ("ATT010", "ENR009", "2019-09-05", "Present"),
        ])

    conn.commit()
    conn.close()

def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Executes a SQL query and returns a list of dictionaries."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_raw_schema() -> Dict[str, List[Dict[str, str]]]:
    """Retrieves metadata of all tables, including columns, types, and primary/foreign keys."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row['name'] for row in cursor.fetchall()]
    
    schema = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        
        schema[table] = [
            {
                "name": col["name"],
                "type": col["type"],
                "notnull": bool(col["notnull"]),
                "pk": bool(col["pk"])
            }
            for col in columns
        ]
        
    conn.close()
    return schema

# Auto seed when imported or run
seed_database()
