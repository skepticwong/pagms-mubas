"""
migrate_budget_snapshots.py
---------------------------
Creates the budget_snapshots table for immutable pre-amendment snapshots.
Also backfills a 'baseline' snapshot for every existing grant.

Run once: python migrate_budget_snapshots.py
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'pagms.db')


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print(f"Connected to database: {DB_PATH}\n")

    # 1. Create budget_snapshots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget_snapshots (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            grant_id       INTEGER NOT NULL REFERENCES grants(id),
            amendment_id   INTEGER REFERENCES budget_amendments(id),
            snapshot_type  VARCHAR(20) NOT NULL DEFAULT 'pre_amendment',
            snapshot_data  TEXT NOT NULL,
            captured_by    INTEGER REFERENCES users(id),
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✅ Table budget_snapshots ready")
    conn.commit()

    # 2. Backfill a 'baseline' snapshot for every existing grant
    cursor.execute("SELECT id FROM grants")
    grants = cursor.fetchall()

    print(f"\n  Backfilling baseline snapshots for {len(grants)} grants...")

    for (grant_id,) in grants:
        # Check if baseline already exists
        cursor.execute(
            "SELECT id FROM budget_snapshots WHERE grant_id=? AND snapshot_type='baseline'",
            (grant_id,)
        )
        if cursor.fetchone():
            print(f"  ⚠️  Baseline for grant {grant_id} already exists — skipping")
            continue

        # Get current categories as the baseline
        cursor.execute(
            "SELECT id, name, allocated, spent FROM budget_categories WHERE grant_id=?",
            (grant_id,)
        )
        categories = cursor.fetchall()
        snapshot_data = json.dumps([
            {'id': c[0], 'name': c[1], 'allocated': c[2], 'spent': c[3]}
            for c in categories
        ])

        cursor.execute(
            """INSERT INTO budget_snapshots (grant_id, amendment_id, snapshot_type, snapshot_data, captured_by, created_at)
               VALUES (?, NULL, 'baseline', ?, NULL, ?)""",
            (grant_id, snapshot_data, datetime.utcnow().isoformat())
        )
        print(f"  ✅ Baseline snapshot created for grant {grant_id} ({len(categories)} categories)")

    conn.commit()
    conn.close()
    print("\nMigration complete.")


if __name__ == '__main__':
    migrate()
