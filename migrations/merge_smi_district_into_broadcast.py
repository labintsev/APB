"""
Migration script: embed `smi` and `district` data into the `broadcast` table.

Usage: run from project root with the same environment used to run the app.

Make a backup of your database before running this script.

Example:
    cp broadcasts.db broadcasts.db.bkp
    python migrations/merge_smi_district_into_broadcast.py

The script will:
 - add columns to `broadcast` for smi_name, smi_rating, smi_male_proportion, 
   district_name, district_population
 - populate these columns from existing `smi` and `district` tables
 - (optionally) drop the `smi` and `district` tables

Note: adjust DB path in app config if needed.
"""

import sys
import os

# Add parent directory to path so we can import adcalc
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc import create_app
from adcalc.models import db
from sqlalchemy import text


def run(drop_source_tables=False):
    app = create_app()
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()
        
        try:
            # Add columns (SQLite supports ADD COLUMN)
            try:
                conn.execute(text("ALTER TABLE broadcast ADD COLUMN smi_name TEXT"))
                print("✓ Added smi_name column")
            except Exception as e:
                print(f"  smi_name column already exists or error: {e}")
            
            try:
                conn.execute(text("ALTER TABLE broadcast ADD COLUMN smi_rating REAL"))
                print("✓ Added smi_rating column")
            except Exception as e:
                print(f"  smi_rating column already exists or error: {e}")
            
            try:
                conn.execute(text("ALTER TABLE broadcast ADD COLUMN smi_male_proportion REAL"))
                print("✓ Added smi_male_proportion column")
            except Exception as e:
                print(f"  smi_male_proportion column already exists or error: {e}")
            
            try:
                conn.execute(text("ALTER TABLE broadcast ADD COLUMN district_name TEXT"))
                print("✓ Added district_name column")
            except Exception as e:
                print(f"  district_name column already exists or error: {e}")
            
            try:
                conn.execute(text("ALTER TABLE broadcast ADD COLUMN district_population INTEGER"))
                print("✓ Added district_population column")
            except Exception as e:
                print(f"  district_population column already exists or error: {e}")

            # Populate new columns from existing tables
            update_sql = """
            UPDATE broadcast SET
              smi_name = (SELECT name FROM smi WHERE smi.id = broadcast.smi_id),
              smi_rating = (SELECT rating FROM smi WHERE smi.id = broadcast.smi_id),
              smi_male_proportion = (SELECT male FROM smi WHERE smi.id = broadcast.smi_id),
              district_name = (SELECT name FROM district WHERE district.id = broadcast.district_id),
              district_population = (SELECT population FROM district WHERE district.id = broadcast.district_id)
            """
            result = conn.execute(text(update_sql))
            print(f"✓ Updated {result.rowcount} broadcast records with smi and district data")

            if drop_source_tables:
                try:
                    conn.execute(text('DROP TABLE IF EXISTS smi'))
                    conn.execute(text('DROP TABLE IF EXISTS district'))
                    print('✓ Dropped source tables `smi` and `district`')
                except Exception as e:
                    print('Warning: failed to drop source tables:', e)

            trans.commit()
            print("\n✓ Migration completed successfully!")
        except Exception as e:
            trans.rollback()
            print(f"\n✗ Migration failed: {e}")
            raise
        finally:
            conn.close()


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--drop', action='store_true', help='Drop source tables after migration')
    args = p.parse_args()
    run(drop_source_tables=args.drop)
