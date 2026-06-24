import os
import yaml
from typing import Dict, Any, List

DEFAULT_DOMAINS = {
    "healthcare_claims": {
        "domain": "healthcare_claims",
        "description": "Healthcare claims database containing member information, claims, payers, and payments.",
        "tables": {
            "members": {
                "description": "Information about members enrolled in the health plans.",
                "columns": {
                    "member_id": "Unique identifier for each member.",
                    "first_name": "First name of the member.",
                    "last_name": "Last name of the member.",
                    "birth_date": "Date of birth of the member."
                }
            },
            "payers": {
                "description": "Insurers or payers who pay for health claims.",
                "columns": {
                    "payer_id": "Unique identifier for the payer.",
                    "name": "Name of the payer organization.",
                    "type": "Type of payer (e.g. government, commercial)."
                }
            },
            "claims": {
                "description": "Healthcare claims submitted by providers for services.",
                "columns": {
                    "claim_id": "Unique identifier for the claim.",
                    "member_id": "Member who received the services, matches members.member_id.",
                    "payer_id": "Payer responsible for the claim, matches payers.payer_id.",
                    "service_date": "Date when services were rendered.",
                    "amount": "Total dollar amount of the claim.",
                    "status": "Current status of the claim (e.g., Paid, Pending, Denied)."
                }
            },
            "payments": {
                "description": "Payment transactions mapping to claims.",
                "columns": {
                    "payment_id": "Unique payment identifier.",
                    "claim_id": "Claim that this payment belongs to, matches claims.claim_id.",
                    "amount": "Amount paid.",
                    "payment_date": "Date when payment was executed.",
                    "method": "Payment method (e.g., Check, EFT)."
                }
            }
        }
    },
    "retail_sales": {
        "domain": "retail_sales",
        "description": "Retail sales database containing order and product information.",
        "tables": {
            "sales": {
                "description": "Sales and orders database table containing order, product details, quantity, and price.",
                "columns": {
                    "order_id": "Unique identifier for the order.",
                    "customer_id": "Identifier of the customer who made the purchase.",
                    "product_name": "Name of the product sold.",
                    "quantity": "Quantity of items purchased.",
                    "price": "Unit price of the product.",
                    "order_date": "Date when the order was placed."
                }
            }
        }
    },
    "ecommerce": {
        "domain": "ecommerce",
        "description": "E-commerce platform database covering products, orders, customers, reviews, and inventory management.",
        "tables": {
            "customers": {
                "description": "Online shoppers registered on the e-commerce platform.",
                "columns": {
                    "customer_id": "Unique identifier for the customer.",
                    "email": "Customer's email address (unique login).",
                    "username": "Customer's display name.",
                    "registration_date": "Date the customer registered.",
                    "country": "Country of the customer.",
                    "loyalty_tier": "Loyalty program tier (e.g., Bronze, Silver, Gold, Platinum)."
                }
            },
            "products": {
                "description": "Product catalog with pricing and categorization.",
                "columns": {
                    "product_id": "Unique product identifier.",
                    "name": "Product display name.",
                    "category": "Product category (e.g., Electronics, Clothing, Books).",
                    "brand": "Brand or manufacturer name.",
                    "unit_price": "Selling price per unit in USD.",
                    "cost_price": "Procurement cost per unit.",
                    "sku": "Stock keeping unit code.",
                    "is_active": "Whether the product is currently listed (1=yes, 0=no)."
                }
            },
            "orders": {
                "description": "Customer purchase orders placed on the platform.",
                "columns": {
                    "order_id": "Unique identifier for the order.",
                    "customer_id": "Customer who placed the order, matches customers.customer_id.",
                    "order_date": "Date and time the order was placed.",
                    "total_amount": "Total order value including taxes.",
                    "discount_amount": "Discount applied to the order.",
                    "shipping_cost": "Shipping fee charged.",
                    "status": "Order status (e.g., Pending, Shipped, Delivered, Cancelled, Returned).",
                    "shipping_address": "Full shipping address."
                }
            },
            "order_items": {
                "description": "Individual line items within an order, linking products to orders.",
                "columns": {
                    "item_id": "Unique identifier for the line item.",
                    "order_id": "Order this item belongs to, matches orders.order_id.",
                    "product_id": "Product purchased, matches products.product_id.",
                    "quantity": "Number of units ordered.",
                    "unit_price": "Price per unit at time of purchase.",
                    "subtotal": "Total price for this line item (quantity * unit_price)."
                }
            },
            "reviews": {
                "description": "Product reviews and ratings submitted by customers.",
                "columns": {
                    "review_id": "Unique identifier for the review.",
                    "product_id": "Product being reviewed, matches products.product_id.",
                    "customer_id": "Customer who wrote the review, matches customers.customer_id.",
                    "rating": "Star rating from 1 to 5.",
                    "review_text": "Written review content.",
                    "review_date": "Date the review was posted.",
                    "helpful_votes": "Number of users who found the review helpful."
                }
            },
            "inventory": {
                "description": "Current warehouse stock levels and replenishment info.",
                "columns": {
                    "inventory_id": "Unique inventory record identifier.",
                    "product_id": "Product in inventory, matches products.product_id.",
                    "warehouse_id": "Warehouse where stock is held.",
                    "quantity_on_hand": "Units currently available in stock.",
                    "reorder_level": "Minimum threshold to trigger reorder.",
                    "last_restocked": "Date inventory was last replenished."
                }
            }
        }
    },
    "finance_banking": {
        "domain": "finance_banking",
        "description": "Banking and financial transactions database covering accounts, customers, loans, transactions, and branches.",
        "tables": {
            "customers": {
                "description": "Bank customers with personal and contact information.",
                "columns": {
                    "customer_id": "Unique identifier for each bank customer.",
                    "first_name": "Customer's first name.",
                    "last_name": "Customer's last name.",
                    "email": "Customer's email address.",
                    "phone": "Customer's contact phone number.",
                    "date_of_birth": "Customer's date of birth.",
                    "kyc_status": "Know-Your-Customer verification status (e.g., Verified, Pending, Rejected)."
                }
            },
            "accounts": {
                "description": "Bank accounts held by customers including savings and checking.",
                "columns": {
                    "account_id": "Unique identifier for the bank account.",
                    "customer_id": "Customer who owns this account, matches customers.customer_id.",
                    "account_type": "Type of account (e.g., Savings, Checking, Money Market).",
                    "balance": "Current account balance in USD.",
                    "currency": "Currency code (e.g., USD, EUR).",
                    "opened_date": "Date the account was opened.",
                    "status": "Account status (e.g., Active, Frozen, Closed)."
                }
            },
            "transactions": {
                "description": "Financial transactions including deposits, withdrawals, and transfers.",
                "columns": {
                    "transaction_id": "Unique identifier for the transaction.",
                    "account_id": "Account involved in the transaction, matches accounts.account_id.",
                    "transaction_type": "Type of transaction (e.g., Deposit, Withdrawal, Transfer, Fee).",
                    "amount": "Transaction amount in USD.",
                    "transaction_date": "Date and time the transaction occurred.",
                    "description": "Free-text description of the transaction.",
                    "reference_number": "External reference or confirmation number."
                }
            },
            "loans": {
                "description": "Loan records issued to customers.",
                "columns": {
                    "loan_id": "Unique identifier for the loan.",
                    "customer_id": "Customer who took the loan, matches customers.customer_id.",
                    "loan_type": "Type of loan (e.g., Personal, Mortgage, Auto, Student).",
                    "principal_amount": "Original loan amount in USD.",
                    "interest_rate": "Annual interest rate as a percentage.",
                    "term_months": "Loan term duration in months.",
                    "monthly_payment": "Required monthly payment amount.",
                    "disbursement_date": "Date the loan was disbursed.",
                    "status": "Loan status (e.g., Active, Paid Off, Defaulted)."
                }
            },
            "branches": {
                "description": "Physical bank branch locations.",
                "columns": {
                    "branch_id": "Unique identifier for the branch.",
                    "branch_name": "Name of the branch location.",
                    "city": "City where the branch is located.",
                    "state": "State or province of the branch.",
                    "address": "Street address of the branch.",
                    "phone": "Branch contact phone number."
                }
            },
            "credit_cards": {
                "description": "Credit card accounts linked to bank customers.",
                "columns": {
                    "card_id": "Unique credit card identifier.",
                    "customer_id": "Card holder, matches customers.customer_id.",
                    "card_type": "Card tier (e.g., Standard, Gold, Platinum).",
                    "credit_limit": "Maximum credit limit in USD.",
                    "current_balance": "Current outstanding balance.",
                    "due_date": "Next payment due date.",
                    "rewards_points": "Accumulated rewards points."
                }
            }
        }
    },
    "logistics": {
        "domain": "logistics",
        "description": "Logistics and supply chain database covering shipments, carriers, warehouses, routes, and delivery tracking.",
        "tables": {
            "shipments": {
                "description": "Shipment records tracking packages from origin to destination.",
                "columns": {
                    "shipment_id": "Unique identifier for the shipment.",
                    "origin_warehouse_id": "Source warehouse, matches warehouses.warehouse_id.",
                    "destination_address": "Full delivery address.",
                    "carrier_id": "Carrier handling the shipment, matches carriers.carrier_id.",
                    "route_id": "Route used for this shipment, matches routes.route_id.",
                    "weight_kg": "Package weight in kilograms.",
                    "status": "Shipment status (e.g., Picked Up, In Transit, Out for Delivery, Delivered, Failed).",
                    "shipped_date": "Date the shipment was dispatched.",
                    "estimated_delivery": "Expected delivery date.",
                    "actual_delivery": "Actual date of delivery (null if not yet delivered)."
                }
            },
            "carriers": {
                "description": "Logistics and courier service providers.",
                "columns": {
                    "carrier_id": "Unique carrier identifier.",
                    "carrier_name": "Name of the carrier company.",
                    "service_type": "Service level (e.g., Standard, Express, Overnight).",
                    "contact_email": "Carrier contact email.",
                    "rating": "Carrier performance rating out of 5."
                }
            },
            "warehouses": {
                "description": "Storage and distribution center locations.",
                "columns": {
                    "warehouse_id": "Unique warehouse identifier.",
                    "warehouse_name": "Name of the warehouse facility.",
                    "city": "City where the warehouse is located.",
                    "state": "State/region of the warehouse.",
                    "capacity_units": "Maximum storage capacity in units.",
                    "current_utilization": "Current storage utilization percentage."
                }
            },
            "routes": {
                "description": "Predefined delivery routes between locations.",
                "columns": {
                    "route_id": "Unique route identifier.",
                    "origin_city": "Departure city of the route.",
                    "destination_city": "Arrival city of the route.",
                    "distance_km": "Total route distance in kilometers.",
                    "estimated_hours": "Estimated travel time in hours.",
                    "active": "Whether the route is currently active (1=yes, 0=no)."
                }
            },
            "tracking_events": {
                "description": "Individual tracking events and status updates for shipments.",
                "columns": {
                    "event_id": "Unique event identifier.",
                    "shipment_id": "Shipment this event belongs to, matches shipments.shipment_id.",
                    "event_type": "Type of event (e.g., Picked Up, Arrived at Hub, Out for Delivery).",
                    "event_timestamp": "Date and time of the event.",
                    "location": "Location where the event occurred.",
                    "notes": "Additional notes or exception details."
                }
            }
        }
    },
    "hr_payroll": {
        "domain": "hr_payroll",
        "description": "Human resources and payroll database covering employees, departments, salaries, leave, and performance.",
        "tables": {
            "employees": {
                "description": "Employee master records including personal and employment details.",
                "columns": {
                    "employee_id": "Unique identifier for the employee.",
                    "first_name": "Employee's first name.",
                    "last_name": "Employee's last name.",
                    "email": "Work email address.",
                    "hire_date": "Date the employee was hired.",
                    "department_id": "Department the employee belongs to, matches departments.department_id.",
                    "job_title": "Employee's current job title.",
                    "manager_id": "Direct manager's employee_id, self-referencing employees.employee_id.",
                    "employment_type": "Employment contract type (e.g., Full-Time, Part-Time, Contractor).",
                    "status": "Employment status (e.g., Active, Terminated, On Leave)."
                }
            },
            "departments": {
                "description": "Company departments and cost centers.",
                "columns": {
                    "department_id": "Unique identifier for the department.",
                    "department_name": "Name of the department (e.g., Engineering, Finance, HR).",
                    "location": "Office location of the department.",
                    "head_count": "Current number of employees in the department.",
                    "budget": "Annual department budget in USD."
                }
            },
            "salaries": {
                "description": "Salary history and compensation records per employee.",
                "columns": {
                    "salary_id": "Unique identifier for the salary record.",
                    "employee_id": "Employee receiving this salary, matches employees.employee_id.",
                    "base_salary": "Annual base salary in USD.",
                    "bonus": "Annual bonus amount.",
                    "effective_date": "Date this salary became effective.",
                    "end_date": "Date this salary record ended (null if current).",
                    "currency": "Salary currency code."
                }
            },
            "leave_requests": {
                "description": "Employee leave and time-off requests.",
                "columns": {
                    "leave_id": "Unique identifier for the leave request.",
                    "employee_id": "Employee requesting leave, matches employees.employee_id.",
                    "leave_type": "Type of leave (e.g., Annual, Sick, Maternity, Unpaid).",
                    "start_date": "Leave start date.",
                    "end_date": "Leave end date.",
                    "days_requested": "Total number of leave days requested.",
                    "status": "Approval status (e.g., Pending, Approved, Rejected).",
                    "approved_by": "Manager who approved/rejected, matches employees.employee_id."
                }
            },
            "performance_reviews": {
                "description": "Annual or periodic employee performance evaluations.",
                "columns": {
                    "review_id": "Unique identifier for the performance review.",
                    "employee_id": "Employee being reviewed, matches employees.employee_id.",
                    "reviewer_id": "Manager conducting the review, matches employees.employee_id.",
                    "review_period": "Review period label (e.g., Q1-2026, Annual-2025).",
                    "overall_rating": "Numeric rating score (e.g., 1.0 to 5.0).",
                    "comments": "Reviewer comments and feedback.",
                    "review_date": "Date the review was completed."
                }
            }
        }
    },
    "education": {
        "domain": "education",
        "description": "Educational institution database covering students, courses, enrollments, instructors, and grades.",
        "tables": {
            "students": {
                "description": "Student records including demographics and enrollment status.",
                "columns": {
                    "student_id": "Unique identifier for the student.",
                    "first_name": "Student's first name.",
                    "last_name": "Student's last name.",
                    "email": "Student's email address.",
                    "enrollment_date": "Date the student enrolled at the institution.",
                    "program": "Academic program or major (e.g., Computer Science, Business, Nursing).",
                    "gpa": "Current cumulative GPA on a 4.0 scale.",
                    "status": "Enrollment status (e.g., Active, Graduated, Dropped, On Hold)."
                }
            },
            "instructors": {
                "description": "Faculty and instructors teaching courses.",
                "columns": {
                    "instructor_id": "Unique identifier for the instructor.",
                    "first_name": "Instructor's first name.",
                    "last_name": "Instructor's last name.",
                    "email": "Instructor's institutional email.",
                    "department": "Academic department the instructor belongs to.",
                    "rank": "Academic rank (e.g., Lecturer, Assistant Professor, Associate Professor, Professor).",
                    "hire_date": "Date the instructor was hired."
                }
            },
            "courses": {
                "description": "Academic courses offered by the institution.",
                "columns": {
                    "course_id": "Unique identifier for the course.",
                    "course_code": "Short alphanumeric code for the course (e.g., CS101, BUS302).",
                    "course_name": "Full name of the course.",
                    "credits": "Number of academic credit hours.",
                    "department": "Department offering the course.",
                    "instructor_id": "Instructor teaching the course, matches instructors.instructor_id.",
                    "semester": "Semester when the course is offered (e.g., Fall-2025, Spring-2026).",
                    "max_enrollment": "Maximum number of students allowed."
                }
            },
            "enrollments": {
                "description": "Student course enrollment records.",
                "columns": {
                    "enrollment_id": "Unique identifier for the enrollment record.",
                    "student_id": "Enrolled student, matches students.student_id.",
                    "course_id": "Course enrolled in, matches courses.course_id.",
                    "enrollment_date": "Date the student enrolled in the course.",
                    "status": "Enrollment status (e.g., Enrolled, Withdrawn, Completed)."
                }
            },
            "grades": {
                "description": "Student grades and academic performance per course.",
                "columns": {
                    "grade_id": "Unique identifier for the grade record.",
                    "enrollment_id": "Enrollment this grade belongs to, matches enrollments.enrollment_id.",
                    "assessment_type": "Type of assessment (e.g., Midterm, Final, Assignment, Quiz).",
                    "score": "Raw score achieved.",
                    "max_score": "Maximum possible score.",
                    "letter_grade": "Final letter grade (e.g., A, B+, C, F).",
                    "graded_date": "Date the grade was recorded."
                }
            },
            "attendance": {
                "description": "Student class attendance records.",
                "columns": {
                    "attendance_id": "Unique attendance record identifier.",
                    "enrollment_id": "Enrollment record, matches enrollments.enrollment_id.",
                    "class_date": "Date of the class session.",
                    "status": "Attendance status (e.g., Present, Absent, Late, Excused)."
                }
            }
        }
    }
}

def load_domain(filepath: str) -> Dict[str, Any]:
    """Loads a domain YAML file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def save_domain(filepath: str, domain_data: Dict[str, Any]) -> None:
    """Saves a domain dict to a YAML file."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, 'w') as f:
        yaml.safe_dump(domain_data, f, sort_keys=False)

def init_default_domains(directory: str) -> None:
    """Initializes the default domain YAML files if they do not exist."""
    for name, data in DEFAULT_DOMAINS.items():
        path = os.path.join(directory, f"{name}.yaml")
        if not os.path.exists(path):
            save_domain(path, data)

def serialize_domain_tables(domain_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Serializes each table in a domain to a search-friendly document string.
    Returns list of dicts with:
      - 'domain': domain name
      - 'table': table name
      - 'text': string containing table & column semantic details for embedding/retrieval
    """
    documents = []
    domain_name = domain_data.get("domain", "")
    domain_desc = domain_data.get("description", "")
    tables = domain_data.get("tables", {})
    
    for table_name, table_info in tables.items():
        desc = table_info.get("description", "")
        cols = table_info.get("columns", {})
        cols_str = ", ".join([f"{c} ({desc})" for c, desc in cols.items()])
        
        doc_text = (
            f"Domain: {domain_name}. "
            f"Domain Description: {domain_desc}. "
            f"Table Name: {table_name}. "
            f"Table Description: {desc}. "
            f"Columns: {cols_str}."
        )
        
        documents.append({
            "domain": domain_name,
            "table": table_name,
            "text": doc_text
        })
        
    return documents
