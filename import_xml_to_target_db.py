#!/usr/bin/env python3
"""
Parse broadcast license XML and populate target_schema.sql database.
Filters: status == 'действующая' AND licensed_activity == 'Радиовещание радиоканала'
"""

import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime


class XMLToTargetSchemaImporter:
    """Import XML data to normalized target schema database."""
    
    def __init__(self, db_path: str, schema_path: str):
        """Initialize importer."""
        self.db_path = db_path
        self.schema_path = schema_path
        self.conn = None
        self.cursor = None
        self.namespace = {'rkn': 'http://rsoc.ru/opendata/7705846236-LicBroadcast'}
        
        # Filters
        self.status_filter = 'действующая'
        self.activity_filter = 'Радиовещание радиоканала'
        
        # Cache for deduplication (region, district, smi)
        self.region_cache: Dict[str, int] = {}
        self.district_cache: Dict[Tuple[int, str], int] = {}
        self.smi_cache: Dict[str, int] = {}
        self.org_cache: Dict[int, int] = {}
    
    def create_database(self):
        """Create database schema."""
        print(f"Creating database at {self.db_path}...")
        
        # Remove existing database if it exists
        if Path(self.db_path).exists():
            Path(self.db_path).unlink()
        
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Read and execute schema
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()
            self.cursor.executescript(schema)
        
        self.conn.commit()
        print("Database schema created successfully.")
    
    def parse_xml(self, xml_path: str) -> Optional[ET.Element]:
        """Parse XML file and return root element."""
        print(f"Parsing XML file: {xml_path}")
        try:
            tree = ET.parse(xml_path)
            return tree.getroot()
        except Exception as e:
            print(f"Error parsing XML: {e}")
            return None
    
    def get_text(self, element: Optional[ET.Element], default: str = "") -> str:
        """Safely get text from XML element."""
        if element is not None and element.text:
            return element.text.strip()
        return default
    
    def safe_int(self, value_str: str) -> Optional[int]:
        """Convert string to integer or return None."""
        if not value_str:
            return None
        try:
            return int(value_str)
        except ValueError:
            return None
    
    def safe_float(self, value_str: str) -> Optional[float]:
        """Convert string to float or return None."""
        if not value_str:
            return None
        try:
            return float(value_str.replace(',', '.'))
        except ValueError:
            return None
    
    def get_or_create_region(self, region_name: str) -> int:
        """Get or create region, return its ID."""
        if region_name in self.region_cache:
            return self.region_cache[region_name]
        
        self.cursor.execute("INSERT INTO region (name) VALUES (?)", (region_name,))
        region_id = self.cursor.lastrowid
        self.region_cache[region_name] = region_id
        return region_id
    
    def get_or_create_district(self, region_id: int, district_name: str, population: Optional[float]) -> int:
        """Get or create district, return its ID."""
        key = (region_id, district_name)
        if key in self.district_cache:
            return self.district_cache[key]
        
        pop_int = int(population * 1000) if population else None
        self.cursor.execute(
            "INSERT INTO district (region_id, name, population) VALUES (?, ?, ?)",
            (region_id, district_name, pop_int)
        )
        district_id = self.cursor.lastrowid
        self.district_cache[key] = district_id
        return district_id
    
    def get_or_create_smi(self, smi_name: str) -> int:
        """Get or create SMI (media), return its ID."""
        if smi_name in self.smi_cache:
            return self.smi_cache[smi_name]
        
        self.cursor.execute("INSERT INTO smi (smi_id, name) VALUES (?, ?)", (0, smi_name))
        smi_id = self.cursor.lastrowid
        self.smi_cache[smi_name] = smi_id
        return smi_id
    
    def get_or_create_organisation(self, record_elem: ET.Element) -> Optional[int]:
        """Extract and create organisation, return its ID."""
        org_id_val = self.safe_int(self.get_text(record_elem.find('rkn:org_id', self.namespace)))
        if org_id_val is None:
            return None
        
        if org_id_val in self.org_cache:
            return self.org_cache[org_id_val]
        
        org_name = self.get_text(record_elem.find('rkn:org_name', self.namespace))
        org_name_short = self.get_text(record_elem.find('rkn:org_name_short', self.namespace))
        inn = self.get_text(record_elem.find('rkn:inn', self.namespace))
        ogrn = self.get_text(record_elem.find('rkn:ogrn', self.namespace))
        address = self.get_text(record_elem.find('rkn:address', self.namespace))
        phone = self.get_text(record_elem.find('rkn:phone', self.namespace))
        email = self.get_text(record_elem.find('rkn:email', self.namespace))
        
        # Check for duplicate by inn/ogrn
        try:
            self.cursor.execute(
                "INSERT INTO organisation (org_id, name, name_short, inn, ogrn, address, phone, email) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (org_id_val, org_name, org_name_short, inn, ogrn, address, phone, email)
            )
            db_org_id = self.cursor.lastrowid
            self.org_cache[org_id_val] = db_org_id
            return db_org_id
        except sqlite3.IntegrityError:
            # Already exists, fetch it
            self.cursor.execute("SELECT id FROM organisation WHERE inn = ?", (inn,))
            result = self.cursor.fetchone()
            if result:
                db_org_id = result[0]
                self.org_cache[org_id_val] = db_org_id
                return db_org_id
        
        return None
    
    def insert_broadcast_records(self, record_id: int, record_elem: ET.Element):
        """Insert broadcast records from grid."""
        grid_elem = record_elem.find('rkn:grid', self.namespace)
        if grid_elem is None:
            return
        
        smi_name = self.get_text(record_elem.find('rkn:smi_name', self.namespace))
        smi_id = self.get_or_create_smi(smi_name)
        
        for row in grid_elem.findall('rkn:row', self.namespace):
            try:
                region_name = self.get_text(row.find('rkn:region_name_full', self.namespace))
                district_name = self.get_text(row.find('rkn:region_text', self.namespace))
                population = self.safe_float(self.get_text(row.find('rkn:population', self.namespace)))
                
                mount_point = self.get_text(row.find('rkn:mount_point', self.namespace))
                channel_num = self.get_text(row.find('rkn:channel_num', self.namespace))
                freq = self.get_text(row.find('rkn:freq', self.namespace))
                power = self.get_text(row.find('rkn:power', self.namespace))
                brcst_time = self.get_text(row.find('rkn:brcst_time', self.namespace))
                
                # Get or create region and district
                region_id = self.get_or_create_region(region_name)
                district_id = self.get_or_create_district(region_id, district_name, population)
                
                # Insert broadcast record
                self.cursor.execute(
                    "INSERT INTO broadcast (org_id, district_id, smi_id, mount_point, channel_num, freq, power, brcst_time) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (record_id, district_id, smi_id, mount_point, channel_num, freq, power, brcst_time)
                )
            
            except Exception as e:
                print(f"Error inserting broadcast record: {e}")
    
    def import_xml(self, xml_path: str):
        """Main import function with filters."""
        root = self.parse_xml(xml_path)
        if root is None:
            return
        
        records_count = 0
        filtered_count = 0
        
        # Find all record elements
        for record_elem in root.findall('rkn:record', self.namespace):
            try:
                # Apply filters
                status = self.get_text(record_elem.find('rkn:status', self.namespace))
                licensed_activity = self.get_text(record_elem.find('rkn:licensed_activity', self.namespace))
                
                if status != self.status_filter or licensed_activity != self.activity_filter:
                    filtered_count += 1
                    continue
                
                # Get or create organisation
                org_id = self.get_or_create_organisation(record_elem)
                if org_id is None:
                    continue
                
                # Insert broadcast records
                self.insert_broadcast_records(org_id, record_elem)
                
                records_count += 1
                if records_count % 10 == 0:
                    print(f"Processed {records_count} matching records...")
            
            except Exception as e:
                print(f"Error processing record: {e}")
        
        self.conn.commit()
        print(f"\nImport complete!")
        print(f"  Inserted: {records_count} records")
        print(f"  Filtered out: {filtered_count} records")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")


def main():
    """Main entry point."""
    import sys
    
    # Default paths
    db_name = 'broadcast_target.db'
    schema_path = 'data/target_schema.sql'
    xml_path = 'data/data-20251201T0000-structure-20220404T0000.xml'
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        xml_path = sys.argv[1]
    if len(sys.argv) > 2:
        db_name = sys.argv[2]
    if len(sys.argv) > 3:
        schema_path = sys.argv[3]
    
    print("=" * 70)
    print("XML to Target Schema Database Importer")
    print("=" * 70)
    print(f"XML file: {xml_path}")
    print(f"Database: {db_name}")
    print(f"Schema: {schema_path}")
    print(f"\nFilters applied:")
    print(f"  - status = 'действующая'")
    print(f"  - licensed_activity = 'Радиовещание радиоканала'")
    print("=" * 70)
    
    # Create and run importer
    importer = XMLToTargetSchemaImporter(db_name, schema_path)
    
    try:
        importer.create_database()
        importer.import_xml(xml_path)
    
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        importer.close()


if __name__ == '__main__':
    main()
