
import sqlite3
import os

# Path to the database file
db_path = os.path.join('instance', 'pagms.db')
print(f"Connecting to database at: {os.path.abspath(db_path)}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    columns_to_add_grants = [
        ("funder_reference_number", "TEXT"),
        ("financial_reporting_frequency", "TEXT"),
        ("progress_reporting_frequency", "TEXT"),
        ("special_requirements", "TEXT"),
        ("ethical_approval_filename", "TEXT"),
        ("agreement_filename", "TEXT"),
        ("budget_breakdown_filename", "TEXT"),
        ("award_letter_filename", "TEXT"),
        ("currency", "TEXT"),
        ("exchange_rate", "REAL")
    ]

    print("Checking and patching grants table columns...")
    for col, dtype in columns_to_add_grants:
        try:
            cursor.execute(f"ALTER TABLE grants ADD COLUMN {col} {dtype}")
            print(f"[OK] Added column to grants: {col}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print(f"[INFO] Column {col} already exists in grants. Skipped.")
            else:
                print(f"[ERROR] Error adding {col} to grants: {e}")

    # Patch for budget_categories table
    columns_to_add_budget_categories = [
        ("spent", "REAL")
    ]

    print("\nChecking and patching budget_categories table columns...")
    for col, dtype in columns_to_add_budget_categories:
        try:
            cursor.execute(f"ALTER TABLE budget_categories ADD COLUMN {col} {dtype}")
            print(f"[OK] Added column to budget_categories: {col}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print(f"[INFO] Column {col} already exists in budget_categories. Skipped.")
            else:
                print(f"[ERROR] Error adding {col} to budget_categories: {e}")

    conn.commit()
    conn.close()
    print("\nDatabase patch completed successfully!")
    print("Please refresh the dashboard now.")

except Exception as e:
    print(f"\n[CRITICAL] Error patching database: {e}")
