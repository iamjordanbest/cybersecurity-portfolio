#!/usr/bin/env python3
"""
CISA KEV Data Ingestion Script
Loads CISA Known Exploited Vulnerabilities into PostgreSQL database
"""

import json
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import os
import sys

def load_kev_data(json_file_path):
    """Load KEV JSON data from file"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_db_connection():
    """Create database connection"""
    # For now, return None - will be configured with actual DB credentials
    # Replace with your database credentials
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'grc_analytics'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database connection error: {e}")
        print("Note: Database credentials should be configured in environment variables")
        return None

def ingest_kev_to_db(kev_data, conn):
    """Insert KEV data into database"""
    cursor = conn.cursor()
    
    vulnerabilities = kev_data['vulnerabilities']
    
    # Prepare data for bulk insert
    records = []
    for vuln in vulnerabilities:
        record = (
            vuln['cveID'],
            vuln['vendorProject'],
            vuln['product'],
            vuln['vulnerabilityName'],
            vuln['shortDescription'],
            vuln['requiredAction'],
            vuln.get('knownRansomwareCampaignUse', 'Unknown') == 'Known',
            vuln['dateAdded'],
            vuln['dueDate'],
            vuln.get('notes', '')
        )
        records.append(record)
    
    # Bulk insert with ON CONFLICT handling
    insert_query = """
        INSERT INTO cisa_kev (
            cve_id, vendor_project, product, vulnerability_name,
            short_description, required_action, known_ransomware_use,
            date_added, due_date, notes
        ) VALUES %s
        ON CONFLICT (cve_id) 
        DO UPDATE SET
            vendor_project = EXCLUDED.vendor_project,
            product = EXCLUDED.product,
            vulnerability_name = EXCLUDED.vulnerability_name,
            short_description = EXCLUDED.short_description,
            required_action = EXCLUDED.required_action,
            known_ransomware_use = EXCLUDED.known_ransomware_use,
            date_added = EXCLUDED.date_added,
            due_date = EXCLUDED.due_date,
            notes = EXCLUDED.notes,
            updated_at = CURRENT_TIMESTAMP
    """
    
    execute_values(cursor, insert_query, records)
    conn.commit()
    
    print(f"✓ Inserted/Updated {len(records)} KEV records")
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM cisa_kev")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cisa_kev WHERE known_ransomware_use = TRUE")
    ransomware_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cisa_kev WHERE due_date < CURRENT_DATE")
    overdue_count = cursor.fetchone()[0]
    
    cursor.close()
    
    return {
        'total': total_count,
        'ransomware': ransomware_count,
        'overdue': overdue_count
    }

def ingest_kev_to_sqlite(kev_data, db_path='grc_analytics.db'):
    """Fallback: Insert KEV data into SQLite database"""
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cisa_kev (
            cve_id TEXT PRIMARY KEY,
            vendor_project TEXT,
            product TEXT,
            vulnerability_name TEXT,
            short_description TEXT,
            required_action TEXT,
            known_ransomware_use INTEGER,
            date_added TEXT,
            due_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    vulnerabilities = kev_data['vulnerabilities']
    
    for vuln in vulnerabilities:
        cursor.execute("""
            INSERT OR REPLACE INTO cisa_kev (
                cve_id, vendor_project, product, vulnerability_name,
                short_description, required_action, known_ransomware_use,
                date_added, due_date, notes, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            vuln['cveID'],
            vuln['vendorProject'],
            vuln['product'],
            vuln['vulnerabilityName'],
            vuln['shortDescription'],
            vuln['requiredAction'],
            1 if vuln.get('knownRansomwareCampaignUse', 'Unknown') == 'Known' else 0,
            vuln['dateAdded'],
            vuln['dueDate'],
            vuln.get('notes', '')
        ))
    
    conn.commit()
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM cisa_kev")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cisa_kev WHERE known_ransomware_use = 1")
    ransomware_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cisa_kev WHERE date(due_date) < date('now')")
    overdue_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total_count,
        'ransomware': ransomware_count,
        'overdue': overdue_count
    }

def main():
    print("=" * 80)
    print("CISA KEV Data Ingestion")
    print("=" * 80)
    
    # Load KEV data
    kev_file = os.path.join(os.path.dirname(__file__), 
                           '../../data/raw/cisa_kev/known_exploited_vulnerabilities.json')
    
    if not os.path.exists(kev_file):
        print(f"❌ Error: KEV data file not found at {kev_file}")
        sys.exit(1)
    
    print(f"\nLoading KEV data from: {kev_file}")
    kev_data = load_kev_data(kev_file)
    
    print(f"✓ Loaded {kev_data['count']} vulnerabilities")
    print(f"  Catalog Version: {kev_data['catalogVersion']}")
    print(f"  Last Updated: {kev_data['dateReleased']}")
    
    # Try PostgreSQL first, fallback to SQLite
    conn = get_db_connection()
    
    if conn:
        print("\n✓ Connected to PostgreSQL database")
        stats = ingest_kev_to_db(kev_data, conn)
        conn.close()
        db_type = "PostgreSQL"
    else:
        print("\n⚠️  PostgreSQL not available, using SQLite fallback")
        db_path = os.path.join(os.path.dirname(__file__), '../../data/processed/grc_analytics.db')
        stats = ingest_kev_to_sqlite(kev_data, db_path)
        db_type = f"SQLite ({db_path})"
    
    print(f"\n{'=' * 80}")
    print("Ingestion Complete!")
    print(f"{'=' * 80}")
    print(f"Database: {db_type}")
    print(f"Total KEV Records: {stats['total']}")
    print(f"Ransomware-related: {stats['ransomware']}")
    print(f"Overdue Remediations: {stats['overdue']}")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    main()
