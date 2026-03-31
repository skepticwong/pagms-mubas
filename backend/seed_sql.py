# backend/seed_sql.py
import sqlite3
import json
from datetime import datetime

DB_PATH = 'instance/pagms.db'

def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Connected to {DB_PATH}. Starting SQL seeding...")

    try:
        # 1. Ensure RSU Admin exists
        cursor.execute("SELECT id FROM users WHERE role='RSU' LIMIT 1")
        admin_row = cursor.fetchone()
        if not admin_row:
            print("No RSU Admin found. Creating one...")
            # Using a dummy hash for rsu@mubas.mw (password: compliance20)
            # In a real app we'd use Werkzeug, but for this SQL script we just need the row.
            dummy_hash = "pbkdf2:sha256:600000$..." 
            cursor.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                           ("RSU Compliance Admin", "rsu@mubas.mw", dummy_hash, "RSU"))
            admin_id = cursor.lastrowid
        else:
            admin_id = admin_row[0]

        # 2. Seed Rules
        rules = [
            ("Single Expense Limit (MWK 5M)", "EXPENSE_LIMIT", {"max_amount": 5000000}, "PRIOR_APPROVAL", "Any single expense exceeding MWK 5,000,000 requires prior RSU approval."),
            ("Alcohol & Tobacco Prohibition", "DESCRIPTION_MATCH", {"keywords": ["alcohol", "tobacco", "cigarette", "liquor", "beer", "wine"]}, "BLOCK", "Expenses for alcohol or tobacco are strictly prohibited."),
            ("Uncategorized Spending Block", "CATEGORY_MATCH", {"forbidden_categories": ["Miscellaneous", "Other"]}, "BLOCK", "All expenses must be mapped to a valid budget category."),
            ("International Travel Audit", "CATEGORY_MATCH", {"special_categories": ["International Travel"]}, "WARN", "International travel triggers an automatic compliance flag.")
        ]

        rule_ids = []
        for name, r_type, logic, outcome, guidance in rules:
            cursor.execute("SELECT id FROM rules WHERE name=?", (name,))
            row = cursor.fetchone()
            if not row:
                cursor.execute("INSERT INTO rules (name, rule_type, logic_config, outcome, priority_level, guidance_text, is_active, created_by_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               (name, r_type, json.dumps(logic), outcome, 3, guidance, 1, admin_id))
                rule_ids.append(cursor.lastrowid)
            else:
                rule_ids.append(row[0])

        # 3. Seed Funder Profiles
        funders = [
            ("World Bank (WB)", "wb"),
            ("National Research Fund (NRF)", "nrf"),
            ("USAID", "usaid"),
            ("EU Horizon", "eu"),
            ("Gates Foundation", "gates")
        ]

        for name, f_id in funders:
            cursor.execute("SELECT id FROM funder_profiles WHERE funder_id=?", (f_id,))
            row = cursor.fetchone()
            if not row:
                cursor.execute("INSERT INTO funder_profiles (name, funder_id, is_active, created_by_id) VALUES (?, ?, ?, ?)",
                               (name, f_id, 1, admin_id))
                profile_id = cursor.lastrowid
            else:
                profile_id = row[0]
            
            # Link rules to profiles
            for r_id in rule_ids:
                cursor.execute("INSERT OR IGNORE INTO funder_profile_rules (profile_id, rule_id) VALUES (?, ?)", (profile_id, r_id))

        conn.commit()
        print("SQL Seeding Complete!")

    except Exception as e:
        print(f"Error during SQL seeding: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed()
