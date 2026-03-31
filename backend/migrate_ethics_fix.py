# backend/migrate_ethics_fix.py
"""
Migration: Ethics Certificate Renewal Fix
Adds missing columns required for the full PI ethics certificate renewal lifecycle.

Columns added:
  grants:
    - ethics_certificate_filename (TEXT) — uploaded PDF from PI at renewal time

  ethics_suspension_periods:
    - reinstated_by   (INTEGER FK → users.id) — RSU officer who approved
    - reinstatement_notes (TEXT) — RSU verification notes at approval time

Run once:
  python migrate_ethics_fix.py
"""
import sqlite3
import os
import sys

# Locate the database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'pagms.db')

# Fallback: try root-level pagms.db
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(BASE_DIR, 'pagms.db')

if not os.path.exists(DB_PATH):
    print(f"ERROR: Database not found. Tried:\n  {os.path.join(BASE_DIR, 'instance', 'pagms.db')}\n  {os.path.join(BASE_DIR, 'pagms.db')}")
    sys.exit(1)

print(f"Using database: {DB_PATH}")

MIGRATIONS = [
    # ── grants table ─────────────────────────────────────────────────────────
    {
        "table": "grants",
        "column": "ethics_certificate_filename",
        "ddl": "ALTER TABLE grants ADD COLUMN ethics_certificate_filename TEXT",
        "description": "Stores the filename of the renewed ethics certificate uploaded by PI"
    },
    # ── ethics_suspension_periods table ──────────────────────────────────────
    {
        "table": "ethics_suspension_periods",
        "column": "reinstated_by",
        "ddl": "ALTER TABLE ethics_suspension_periods ADD COLUMN reinstated_by INTEGER REFERENCES users(id)",
        "description": "RSU user ID who approved the reinstatement"
    },
    {
        "table": "ethics_suspension_periods",
        "column": "reinstatement_notes",
        "ddl": "ALTER TABLE ethics_suspension_periods ADD COLUMN reinstatement_notes TEXT",
        "description": "Notes recorded by RSU when verifying the renewed certificate"
    },
]

def get_existing_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}

def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    results = []

    for migration in MIGRATIONS:
        table = migration["table"]
        column = migration["column"]
        ddl = migration["ddl"]
        desc = migration["description"]

        existing = get_existing_columns(cursor, table)
        if column in existing:
            print(f"  [SKIP]  {table}.{column} — already exists")
            results.append(("SKIP", table, column))
        else:
            try:
                cursor.execute(ddl)
                conn.commit()
                print(f"  [OK]    {table}.{column} — added ({desc})")
                results.append(("OK", table, column))
            except Exception as e:
                print(f"  [ERROR] {table}.{column} — {e}")
                conn.rollback()
                results.append(("ERROR", table, column))

    conn.close()

    print("\n── Migration Summary ─────────────────────────────")
    ok = sum(1 for r in results if r[0] == "OK")
    skip = sum(1 for r in results if r[0] == "SKIP")
    err = sum(1 for r in results if r[0] == "ERROR")
    print(f"  Added: {ok}  |  Skipped: {skip}  |  Errors: {err}")

    if err > 0:
        print("\nMigration completed with errors. Check the output above.")
        sys.exit(1)
    else:
        print("\nMigration completed successfully.")

if __name__ == "__main__":
    print("Running Ethics Renewal Migration...\n")
    run_migration()
