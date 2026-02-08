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
            # Create new broadcast table
            conn.execute(text("""
                CREATE TABLE broadcast_new (
                    id INTEGER PRIMARY KEY,
                    org_id INTEGER,
                    smi_name TEXT,
                    smi_rating REAL,
                    smi_male_proportion REAL,
                    district_name TEXT,
                    district_population INTEGER,
                    region_id INTEGER,
                    frequency TEXT,
                    power REAL
                )
            """))
            # copy data from old tables (join to smi and district to populate embedded columns)
            # Use LEFT JOIN so missing smi/district entries do not prevent copying
            conn.execute(text("""
                INSERT INTO broadcast_new (id, org_id, smi_name, smi_rating, smi_male_proportion,
                    district_name, district_population, region_id, frequency, power)
                SELECT b.id, b.org_id,
                       s.name AS smi_name,
                       s.rating AS smi_rating,
                       s.male AS smi_male_proportion,
                       d.name AS district_name,
                       d.population AS district_population,
                       b.region_id,
                       b.frequency,
                       b.power
                FROM broadcast b
                LEFT JOIN smi s ON b.smi_id = s.id
                LEFT JOIN district d ON b.district_id = d.id
            """))

            # Rename broadcast table
            conn.execute(text("DROP TABLE broadcast"))
            conn.execute(text("ALTER TABLE broadcast_new RENAME TO broadcast"))

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
