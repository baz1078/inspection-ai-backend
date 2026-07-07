"""
One-time migration: add the `role` column to the existing User table.

db.create_all() only creates MISSING tables — it does not alter existing
ones, so this must be run once against any database that already has a
User table (i.e. production) before/after deploying the role-gated
realtor report feature. Safe to run multiple times (skips if the column
already exists). Local dev DBs created fresh already have this column
via models.py and don't need this script.

Usage:
    python migrate_add_role_column.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, text, inspect


def main():
    db_url = os.getenv('DATABASE_URL', 'sqlite:///inspection_reports.db')
    print(f"Connecting to: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    engine = create_engine(db_url)

    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('User')]
    if 'role' in columns:
        print("`role` column already exists on User — nothing to do.")
        return

    with engine.begin() as conn:
        if db_url.startswith('sqlite'):
            conn.execute(text(
                "ALTER TABLE \"User\" ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'buyer'"
            ))
        else:
            conn.execute(text(
                "ALTER TABLE \"User\" ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'buyer'"
            ))
    print("Added `role` column to User (default 'buyer' for all existing accounts).")


if __name__ == '__main__':
    main()
