import os
import sqlite3
import pandas as pd
import numpy as np

def generate_superstore_data(db_path="retail_data.db", csv_path="superstore.csv", n=5000):
    """Generates realistic Superstore retail dataset."""
    np.random.seed(42)
    categories = {
        "Technology": ["Phones", "Laptops", "Accessories", "Copiers"],
        "Furniture": ["Chairs", "Tables", "Bookcases", "Furnishings"],
        "Office Supplies": ["Binders", "Paper", "Storage", "Art", "Appliances"]
    }
    regions = ["East", "West", "Central", "South"]
    segments = ["Consumer", "Corporate", "Home Office"]
    ship_modes = ["Standard Class", "Second Class", "First Class", "Same Day"]
    
    rows = []
    cat_keys = list(categories.keys())
    for i in range(1, n + 1):
        cat = np.random.choice(cat_keys, p=[0.3, 0.3, 0.4])
        sub_cat = np.random.choice(categories[cat])
        sales = round(float(np.random.exponential(scale=180.0) + 10.0), 2)
        quantity = int(np.random.randint(1, 10))
        discount = float(np.random.choice([0.0, 0.1, 0.15, 0.2, 0.3, 0.5], p=[0.5, 0.15, 0.1, 0.1, 0.1, 0.05]))
        cost = sales * (1.0 - discount) * np.random.uniform(0.6, 0.95)
        profit = round(sales * (1.0 - discount) - cost, 2)
        
        rows.append({
            "OrderID": f"CA-2024-{100000 + i}",
            "OrderDate": pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(np.random.randint(0, 365))),
            "ShipMode": np.random.choice(ship_modes, p=[0.6, 0.2, 0.15, 0.05]),
            "Segment": np.random.choice(segments, p=[0.5, 0.3, 0.2]),
            "Region": np.random.choice(regions),
            "Category": cat,
            "SubCategory": sub_cat,
            "Sales": sales,
            "Quantity": quantity,
            "Discount": discount,
            "Profit": profit
        })
        
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    conn = sqlite3.connect(db_path)
    df.to_sql("orders", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Created {csv_path} and {db_path} with {n} rows.")

def generate_hr_data(db_path="hr_data.db", csv_path="hr.csv", n=3000):
    """Generates realistic HR employee attrition dataset."""
    np.random.seed(42)
    departments = ["Sales", "Research & Development", "Human Resources", "Engineering", "Marketing"]
    roles = ["Software Engineer", "Sales Executive", "Research Scientist", "HR Specialist", "Manager", "Analyst"]
    education_fields = ["Life Sciences", "Medical", "Marketing", "Technical Degree", "Other"]
    
    rows = []
    for i in range(1, n + 1):
        age = int(np.random.randint(22, 60))
        dept = np.random.choice(departments)
        role = np.random.choice(roles)
        monthly_income = int(np.random.normal(loc=6500, scale=2500))
        monthly_income = max(2500, monthly_income)
        years_at_company = int(min(age - 20, np.random.exponential(scale=5.0)))
        total_working_years = int(years_at_company + np.random.randint(0, 5))
        job_satisfaction = int(np.random.choice([1, 2, 3, 4], p=[0.15, 0.25, 0.35, 0.25]))
        overtime = np.random.choice(["Yes", "No"], p=[0.3, 0.7])
        
        # Attrition probability influenced by satisfaction, overtime, income
        attrition_prob = 0.15
        if overtime == "Yes":
            attrition_prob += 0.18
        if job_satisfaction <= 2:
            attrition_prob += 0.15
        if monthly_income < 4000:
            attrition_prob += 0.10
        attrition_prob = min(0.85, attrition_prob)
        attrition = "Yes" if np.random.rand() < attrition_prob else "No"
        
        rows.append({
            "EmployeeID": i,
            "Age": age,
            "Attrition": attrition,
            "Department": dept,
            "JobRole": role,
            "EducationField": np.random.choice(education_fields),
            "MonthlyIncome": monthly_income,
            "YearsAtCompany": years_at_company,
            "TotalWorkingYears": total_working_years,
            "JobSatisfaction": job_satisfaction,
            "OverTime": overtime
        })
        
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    conn = sqlite3.connect(db_path)
    df.to_sql("employees", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Created {csv_path} and {db_path} with {n} rows.")

def generate_loan_data(db_path="loan_data.db", csv_path="loan.csv", n=4000):
    """Generates realistic FinTech loan risk & default dataset."""
    np.random.seed(42)
    purposes = ["debt_consolidation", "credit_card", "home_improvement", "small_business", "major_purchase"]
    grades = ["A", "B", "C", "D", "E"]
    home_ownership = ["RENT", "MORTGAGE", "OWN"]
    
    rows = []
    for i in range(1, n + 1):
        loan_amnt = int(np.random.choice([5000, 10000, 15000, 20000, 25000, 35000]))
        term = np.random.choice(["36 months", "60 months"], p=[0.7, 0.3])
        grade = np.random.choice(grades, p=[0.25, 0.35, 0.22, 0.12, 0.06])
        interest_rate = {"A": 7.5, "B": 11.2, "C": 14.8, "D": 19.5, "E": 24.0}[grade] + round(float(np.random.normal(0, 0.8)), 2)
        annual_inc = int(np.random.lognormal(mean=11.0, sigma=0.5))
        annual_inc = max(20000, min(300000, annual_inc))
        dti = round(float(np.random.uniform(5.0, 35.0)), 2)
        credit_score = int(np.random.normal(loc=710, scale=50))
        credit_score = max(580, min(850, credit_score))
        
        # Default probability
        default_prob = 0.08
        if grade in ["D", "E"]:
            default_prob += 0.18
        if dti > 25:
            default_prob += 0.10
        if credit_score < 660:
            default_prob += 0.14
        loan_status = "Default" if np.random.rand() < default_prob else "Fully Paid"
        
        rows.append({
            "LoanID": 100000 + i,
            "LoanAmount": loan_amnt,
            "Term": term,
            "InterestRate": interest_rate,
            "Grade": grade,
            "AnnualIncome": annual_inc,
            "HomeOwnership": np.random.choice(home_ownership, p=[0.45, 0.45, 0.10]),
            "Purpose": np.random.choice(purposes),
            "DTI": dti,
            "CreditScore": credit_score,
            "LoanStatus": loan_status
        })
        
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    conn = sqlite3.connect(db_path)
    df.to_sql("loans", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Created {csv_path} and {db_path} with {n} rows.")

def generate_ecommerce_data(db_path="ecommerce_data.db", csv_path="ecommerce.csv", n=4000):
    """Generates realistic E-commerce session and order behavior dataset."""
    np.random.seed(42)
    device_types = ["Mobile", "Desktop", "Tablet"]
    traffic_sources = ["Google Search", "Direct", "Social Media", "Email Newsletter", "Paid Ads"]
    countries = ["United States", "United Kingdom", "Germany", "Canada", "France", "India", "Australia"]
    
    rows = []
    for i in range(1, n + 1):
        device = np.random.choice(device_types, p=[0.60, 0.32, 0.08])
        source = np.random.choice(traffic_sources, p=[0.35, 0.25, 0.20, 0.12, 0.08])
        page_views = int(np.random.poisson(lam=4.5) + 1)
        session_duration_min = round(float(page_views * np.random.uniform(0.5, 2.5)), 2)
        cart_value = round(float(np.random.exponential(scale=65.0) + 12.0), 2)
        
        # Converted probability
        conv_prob = 0.05 + (0.04 if page_views > 5 else 0.0) + (0.06 if device == "Desktop" else 0.0)
        converted = 1 if np.random.rand() < conv_prob else 0
        order_value = cart_value if converted == 1 else 0.0
        
        rows.append({
            "SessionID": 200000 + i,
            "Device": device,
            "TrafficSource": source,
            "Country": np.random.choice(countries),
            "PageViews": page_views,
            "DurationMinutes": session_duration_min,
            "CartValue": cart_value,
            "Converted": converted,
            "OrderValue": order_value
        })
        
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    conn = sqlite3.connect(db_path)
    df.to_sql("orders", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Created {csv_path} and {db_path} with {n} rows.")

def init_all_datasets():
    print("Initializing benchmark datasets for multi-domain verifiable analysis...")
    generate_superstore_data()
    generate_hr_data()
    generate_loan_data()
    generate_ecommerce_data()
    print("All datasets generated successfully!")

if __name__ == "__main__":
    init_all_datasets()
