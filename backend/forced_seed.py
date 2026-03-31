
import os
import sqlite3
import json

# Setup paths relative to backend dir
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BACKEND_DIR, 'instance')
DB_PATH = os.path.join(INSTANCE_DIR, 'pagms.db')

print(f"FORCED SEED: Using DB at {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("ERROR: DB not found at instance/pagms.db")
    os._exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Get an RSU user
cursor.execute("SELECT id FROM users WHERE role='RSU' LIMIT 1")
res = cursor.fetchone()
if not res:
    print("ERROR: No RSU user found.")
    conn.close()
    os._exit(1)
rsu_id = res[0]

# 2. Rules to seed
rules = [
    ("Equipment Threshold $5,000", "THRESHOLD", {"field": "amount", "operator": "greater_than", "value": 5000, "applies_to": "equipment"}, "BLOCK", 1, "Equipment over $5k blocked."),
    ("International Travel Approval", "CATEGORY_ALLOWABILITY", {"field": "amount", "operator": "greater_than", "value": 1000, "applies_to": "travel"}, "PRIOR_APPROVAL", 2, "Travel > $1k needs approval."),
    ("Consultancy Rate Cap", "THRESHOLD", {"field": "amount", "operator": "greater_than", "value": 500, "applies_to": "consultancy"}, "WARN", 3, "Consultancy cap warn.")
]

rule_ids = []
for name, r_type, logic, outcome, priority, guidance in rules:
    cursor.execute("SELECT id FROM rules WHERE name=?", (name,))
    exists = cursor.fetchone()
    if not exists:
        cursor.execute("""
            INSERT INTO rules (name, rule_type, logic_config, outcome, priority_level, guidance_text, created_by_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (name, r_type, json.dumps(logic), outcome, priority, guidance, rsu_id))
        rule_ids.append(cursor.lastrowid)
        print(f"Seeded Rule: {name}")
    else:
        rule_ids.append(exists[0])

# 3. Profiles to seed (matching FUNDERS in PI screen)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS funder_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) UNIQUE NOT NULL,
        funder_id VARCHAR(50) UNIQUE,
        version_number INTEGER DEFAULT 1,
        is_active BOOLEAN DEFAULT 1,
        created_by_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(created_by_id) REFERENCES users(id)
    )
""")

# Ensure version_number exists if table was created previously without it
try:
    cursor.execute("ALTER TABLE funder_profiles ADD COLUMN version_number INTEGER DEFAULT 1")
except: pass

funders = [
    ("World Bank Standard Profile", "wb"),
    ("NRF Compliance Profile", "nrf"),
    ("USAID Safeguard Profile", "usaid"),
    ("DFID Governance Profile", "dfid"),
    ("Gates Foundation Rules", "gates"),
    ("General Compliance Profile", "other")
]

for p_name, f_id in funders:
    cursor.execute("SELECT id FROM funder_profiles WHERE funder_id=?", (f_id,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO funder_profiles (name, funder_id, version_number, is_active, created_by_id)
            VALUES (?, ?, 1, 1, ?)
        """, (p_name, f_id, rsu_id))
        p_id = cursor.lastrowid
        
        # Link rules (M2M table might be funder_profile_rules)
        # Determine table name from models
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='funder_profile_rules'")
        table_name = 'funder_profile_rules' if cursor.fetchone() else 'rule_profile_rules'
        
        for r_id in rule_ids:
            try:
                cursor.execute(f"INSERT INTO {table_name} (funder_profile_id, rule_id) VALUES (?, ?)", (p_id, r_id))
            except Exception as e:
                print(f"Error linking rule {r_id} to profile {p_id}: {e}")
            
        print(f"Seeded Profile: {p_name} for {f_id}")

conn.commit()
conn.close()
print("FORCED SEED SUCCESSFUL.")
os._exit(0)
