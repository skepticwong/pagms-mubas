import sqlite3
import os
from app import app, db

print("Starting DB migration...")

# Step 1: Create missing tables (e.g., RuleProfileSnapshot) via SQLAlchemy
with app.app_context():
    try:
        db.create_all()
        print("db.create_all() executed successfully.")
    except Exception as e:
        print(f"Error in create_all: {e}")

# Step 2: Add missing columns manually to existing tables
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'pagms.db')
print(f"Connecting to database at {db_path}...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column(table, column, datatype):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {datatype}")
        print(f"Successfully added column '{column}' to '{table}'.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            print(f"Column '{column}' already exists in '{table}'.")
        else:
            print(f"Error adding '{column}' to '{table}': {e}")

# rule_profiles
add_column("rule_profiles", "created_at", "DATETIME")
add_column("rule_profiles", "funder_id", "VARCHAR(100)")

# rules
add_column("rules", "priority_level", "INTEGER")
add_column("rules", "guidance_text", "TEXT")

# grants
add_column("grants", "rule_profile_id", "INTEGER")
add_column("grants", "rule_snapshot_id", "INTEGER")

conn.commit()
conn.close()
print("Migration completed.")
