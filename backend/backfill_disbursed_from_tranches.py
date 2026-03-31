"""
One-off: grant.disbursed_funds was not updated when tranches were released via
/api/tranches/<id>/release (only Finance /release-disbursement updated it).

This script adds the sum of amounts for tranches already in status 'released'
to each grant's disbursed_funds when that sum is not yet reflected.

Run from backend folder: python backfill_disbursed_from_tranches.py

Skip grants that already have disbursed_funds > 0 to avoid double-counting
if Finance had already released funds manually.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import func

from app import app
from models import db, Grant, Tranche


def main():
    with app.app_context():
        updated = 0
        grants = Grant.query.all()
        for g in grants:
            current = float(g.disbursed_funds or 0)
            if current > 0:
                continue
            q = (
                db.session.query(func.coalesce(func.sum(Tranche.amount), 0.0))
                .filter(
                    Tranche.grant_id == g.id,
                    func.lower(Tranche.status) == "released",
                )
            )
            tr_sum = float(q.scalar() or 0.0)
            if tr_sum <= 0:
                continue
            g.disbursed_funds = tr_sum
            updated += 1
            print(f"Grant {g.id} ({g.grant_code}): disbursed_funds set to {tr_sum}")
        if updated:
            db.session.commit()
            print(f"Done. Updated {updated} grant(s).")
        else:
            print("Nothing to backfill (no grants with 0 disbursed and released tranches).")


if __name__ == "__main__":
    main()
