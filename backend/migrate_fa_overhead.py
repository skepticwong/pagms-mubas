"""
migrate_fa_overhead.py
----------------------
Adds F&A (Facilities & Administrative) indirect cost tracking columns.

Changes:
  - grants.fa_rate          : Float, default 0.0  (funder-specific overhead rate)
  - budget_categories.is_indirect : Boolean, default 0 (locks against PI expense submission)

Run once: python migrate_fa_overhead.py
"""

import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'pagms.db')


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print(f"Connected to database: {DB_PATH}\n")

    # 1. Add fa_rate to grants table
    try:
        cursor.execute("ALTER TABLE grants ADD COLUMN fa_rate FLOAT DEFAULT 0.0")
        print("  ✅ grants.fa_rate column added")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ⚠️  grants.fa_rate already exists — skipping")
        else:
            raise

    # 2. Add is_indirect to budget_categories table
    try:
        cursor.execute("ALTER TABLE budget_categories ADD COLUMN is_indirect BOOLEAN DEFAULT 0")
        print("  ✅ budget_categories.is_indirect column added")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ⚠️  budget_categories.is_indirect already exists — skipping")
        else:
            raise

    conn.commit()

    # 3. For any grants that already have an fa_rate > 0 (none yet), auto-create
    #    an "Indirect Costs / F&A" budget category marked is_indirect=1.
    #    (This handles future manual fa_rate assignments before the UI is wired.)
    cursor.execute("SELECT id, fa_rate, total_budget FROM grants WHERE fa_rate > 0")
    grants_with_fa = cursor.fetchall()

    for grant_id, fa_rate, total_budget in grants_with_fa:
        overhead_amount = round(total_budget * fa_rate, 2)

        # Check if an indirect category already exists
        cursor.execute(
            "SELECT id FROM budget_categories WHERE grant_id=? AND is_indirect=1",
            (grant_id,)
        )
        existing = cursor.fetchone()

        if not existing:
            cursor.execute(
                """INSERT INTO budget_categories (grant_id, name, allocated, spent, is_indirect)
                   VALUES (?, ?, ?, 0, 1)""",
                (grant_id, "Indirect Costs / F&A", overhead_amount)
            )
            print(f"  ✅ Auto-created 'Indirect Costs / F&A' category for grant {grant_id} (amount: {overhead_amount:,.2f})")

    conn.commit()
    conn.close()

    print("\nMigration complete. Run migrate_budget_snapshots.py next.")


if __name__ == '__main__':
    migrate()
