#!/usr/bin/env python3
"""
Script to parse XML broadcast license data and import into SQLite database.
"""

import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class XMLToDatabaseImporter:
    """Import broadcast license data from XML to SQLite."""
    
    def __init__(self, db_path: str, schema_path: str):
        """Initialize importer with database and schema paths."""
        self.db_path = db_path
        self.schema_path = schema_path
        self.conn = None
        self.cursor = None
        self.namespace = {'rkn': 'http://rsoc.ru/opendata/7705846236-LicBroadcast'}
    
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
    
    def safe_date(self, date_str: str) -> Optional[str]:
        """Convert date string to proper format or return None."""
        if not date_str or date_str.lower() == 'none':
            return None
        try:
            # Try to parse and validate date
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            return None
    
    def safe_int(self, value_str: str) -> Optional[int]:
        """Convert string to integer or return None."""
        if not value_str:
            return None
        try:
            return int(value_str)
        except ValueError:
            return None
    
    def insert_record(self, record_elem: ET.Element) -> Optional[int]:
        """Insert main record and return record ID."""
        try:
            # Extract basic fields
            org_id = self.safe_int(self.get_text(record_elem.find('rkn:org_id', self.namespace)))
            org_name = self.get_text(record_elem.find('rkn:org_name', self.namespace))
            org_name_short = self.get_text(record_elem.find('rkn:org_name_short', self.namespace))
            org_name_brand = self.get_text(record_elem.find('rkn:org_name_brand', self.namespace))
            pattern_name = self.get_text(record_elem.find('rkn:pattern_name', self.namespace))
            address = self.get_text(record_elem.find('rkn:address', self.namespace))
            phone = self.get_text(record_elem.find('rkn:phone', self.namespace))
            email = self.get_text(record_elem.find('rkn:email', self.namespace))
            place = self.get_text(record_elem.find('rkn:place', self.namespace))
            inn = self.get_text(record_elem.find('rkn:inn', self.namespace))
            ogrn = self.get_text(record_elem.find('rkn:ogrn', self.namespace))
            licensed_activity = self.get_text(record_elem.find('rkn:licensed_activity', self.namespace))
            license_num = self.get_text(record_elem.find('rkn:license_num', self.namespace))
            license_num_old = self.get_text(record_elem.find('rkn:license_num_old', self.namespace))
            license_date = self.safe_date(self.get_text(record_elem.find('rkn:license_date', self.namespace)))
            service_start_date = self.safe_date(self.get_text(record_elem.find('rkn:service_start_date', self.namespace)))
            end_date = self.safe_date(self.get_text(record_elem.find('rkn:end_date', self.namespace)))
            smi_name = self.get_text(record_elem.find('rkn:smi_name', self.namespace))
            status = self.get_text(record_elem.find('rkn:status', self.namespace))
            num_order = self.get_text(record_elem.find('rkn:num_order', self.namespace))
            date_order = self.safe_date(self.get_text(record_elem.find('rkn:date_order', self.namespace)))
            sreda = self.get_text(record_elem.find('rkn:sreda', self.namespace))
            changed_user_descr = self.get_text(record_elem.find('rkn:changed_user_descr', self.namespace))
            
            # Insert record
            self.cursor.execute('''
                INSERT INTO records (
                    org_id, org_name, org_name_short, org_name_brand, pattern_name,
                    address, phone, email, place, inn, ogrn, licensed_activity,
                    license_num, license_num_old, license_date, service_start_date,
                    end_date, smi_name, status, num_order, date_order, sreda,
                    changed_user_descr
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                org_id, org_name, org_name_short, org_name_brand, pattern_name,
                address, phone, email, place, inn, ogrn, licensed_activity,
                license_num, license_num_old, license_date, service_start_date,
                end_date, smi_name, status, num_order, date_order, sreda,
                changed_user_descr
            ))
            
            return self.cursor.lastrowid
        
        except Exception as e:
            print(f"Error inserting record: {e}")
            return None
    
    def insert_license_actions(self, record_id: int, record_elem: ET.Element):
        """Insert license action records (granting, renewal, etc.)."""
        actions = ['granting', 'renewal', 'prolongation', 'suspension', 'annulled']
        
        for action_name in actions:
            action_elem = record_elem.find(f'rkn:{action_name}', self.namespace)
            if action_elem is not None:
                try:
                    date = self.safe_date(self.get_text(action_elem.find('rkn:date', self.namespace)))
                    reason = self.get_text(action_elem.find('rkn:reason', self.namespace))
                    description = self.get_text(action_elem.find('rkn:description', self.namespace))
                    
                    self.cursor.execute('''
                        INSERT INTO license_actions (record_id, action_type, date, reason, description)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (record_id, action_name, date, reason, description))
                
                except Exception as e:
                    print(f"Error inserting {action_name} action for record {record_id}: {e}")
    
    def insert_broadcast_grid(self, record_id: int, record_elem: ET.Element):
        """Insert broadcast grid (сетка вещания) records."""
        grid_elem = record_elem.find('rkn:grid', self.namespace)
        if grid_elem is None:
            return
        
        for row in grid_elem.findall('rkn:row', self.namespace):
            try:
                region_name_full = self.get_text(row.find('rkn:region_name_full', self.namespace))
                region_text = self.get_text(row.find('rkn:region_text', self.namespace))
                mount_point = self.get_text(row.find('rkn:mount_point', self.namespace))
                channel_num = self.get_text(row.find('rkn:channel_num', self.namespace))
                freq = self.get_text(row.find('rkn:freq', self.namespace))
                power = self.get_text(row.find('rkn:power', self.namespace))
                population = self.get_text(row.find('rkn:population', self.namespace))
                brcst_time = self.get_text(row.find('rkn:brcst_time', self.namespace))
                sat_brcst_params = self.get_text(row.find('rkn:sat_brcst_params', self.namespace))
                brcst_descr = self.get_text(row.find('rkn:brcst_descr', self.namespace))
                pack_pos_num = self.get_text(row.find('rkn:pack_pos_num', self.namespace))
                pack_num = self.get_text(row.find('rkn:pack_num', self.namespace))
                isz = self.get_text(row.find('rkn:isz', self.namespace))
                transponder = self.safe_int(self.get_text(row.find('rkn:transponder', self.namespace)))
                
                self.cursor.execute('''
                    INSERT INTO broadcast_grid (
                        record_id, region_name_full, region_text, mount_point, channel_num,
                        freq, power, population, brcst_time, sat_brcst_params, brcst_descr,
                        pack_pos_num, pack_num, isz, transponder
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record_id, region_name_full, region_text, mount_point, channel_num,
                    freq, power, population, brcst_time, sat_brcst_params, brcst_descr,
                    pack_pos_num, pack_num, isz, transponder
                ))
            
            except Exception as e:
                print(f"Error inserting broadcast grid row for record {record_id}: {e}")
    
    def insert_programm_concept(self, record_id: int, record_elem: ET.Element):
        """Insert program concept (программная концепция) records."""
        concept_elem = record_elem.find('rkn:programm_concept', self.namespace)
        if concept_elem is None:
            return
        
        for row in concept_elem.findall('rkn:row', self.namespace):
            try:
                smi_name = self.get_text(row.find('rkn:smi_name', self.namespace))
                brcst_direction = self.get_text(row.find('rkn:brcst_direction', self.namespace))
                percentage = self.safe_int(self.get_text(row.find('rkn:percentage', self.namespace)))
                spec = self.get_text(row.find('rkn:spec', self.namespace))
                
                self.cursor.execute('''
                    INSERT INTO programm_concept (record_id, smi_name, brcst_direction, percentage, spec)
                    VALUES (?, ?, ?, ?, ?)
                ''', (record_id, smi_name, brcst_direction, percentage, spec))
            
            except Exception as e:
                print(f"Error inserting program concept row for record {record_id}: {e}")
    
    def import_xml(self, xml_path: str):
        """Main import function."""
        root = self.parse_xml(xml_path)
        if root is None:
            return
        
        records_count = 0
        
        # Find all record elements
        for record_elem in root.findall('rkn:record', self.namespace):
            try:
                # Insert main record
                record_id = self.insert_record(record_elem)
                if record_id is None:
                    continue
                
                # Insert related data
                self.insert_license_actions(record_id, record_elem)
                self.insert_broadcast_grid(record_id, record_elem)
                self.insert_programm_concept(record_id, record_elem)
                
                records_count += 1
                if records_count % 10 == 0:
                    print(f"Processed {records_count} records...")
            
            except Exception as e:
                print(f"Error processing record: {e}")
        
        self.conn.commit()
        print(f"\nImport complete! Inserted {records_count} records.")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")


def main():
    """Main entry point."""
    import sys
    
    # Default paths
    db_path = 'broadcast_licenses.db'
    schema_path = 'sqlite_schema.sql'
    xml_path = r'data\data-20251201T0000-structure-20220404T0000.xml'
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        xml_path = sys.argv[1]
    if len(sys.argv) > 2:
        db_path = sys.argv[2]
    if len(sys.argv) > 3:
        schema_path = sys.argv[3]
    
    print("=" * 60)
    print("XML to SQLite Database Importer")
    print("=" * 60)
    print(f"XML file: {xml_path}")
    print(f"Database: {db_path}")
    print(f"Schema: {schema_path}")
    print("=" * 60)
    
    # Create and run importer
    importer = XMLToDatabaseImporter(db_path, schema_path)
    
    try:
        importer.create_database()
        importer.import_xml(xml_path)
    
    except Exception as e:
        print(f"Fatal error: {e}")
    
    finally:
        importer.close()


if __name__ == '__main__':
    main()
