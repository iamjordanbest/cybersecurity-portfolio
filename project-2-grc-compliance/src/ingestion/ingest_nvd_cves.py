#!/usr/bin/env python3
"""
NVD CVE Ingestion Script

This script ingests CVE data from the NVD (National Vulnerability Database) JSON file
and stores it in the SQLite database for the GRC Analytics Platform.
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection(db_path: str = 'grc_analytics.db') -> sqlite3.Connection:
    """
    Create a database connection to SQLite database.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        Connection object
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)


def load_nvd_data(json_file_path: str) -> Dict[str, Any]:
    """
    Load NVD CVE data from JSON file.
    
    Args:
        json_file_path: Path to the NVD JSON file
        
    Returns:
        Dictionary containing NVD data
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded NVD data from {json_file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        sys.exit(1)


def parse_cvss_metrics(cve_item: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Extract CVSS metrics from CVE item.
    
    Args:
        cve_item: CVE vulnerability item
        
    Returns:
        Dictionary with CVSS scores
    """
    metrics = {
        'cvss_v3_score': None,
        'cvss_v3_severity': None,
        'cvss_v2_score': None,
        'cvss_v2_severity': None
    }
    
    # Try to get CVSS v3 metrics
    if 'metrics' in cve_item:
        if 'cvssMetricV31' in cve_item['metrics'] and cve_item['metrics']['cvssMetricV31']:
            cvss_v3 = cve_item['metrics']['cvssMetricV31'][0]['cvssData']
            metrics['cvss_v3_score'] = cvss_v3.get('baseScore')
            metrics['cvss_v3_severity'] = cvss_v3.get('baseSeverity')
        elif 'cvssMetricV30' in cve_item['metrics'] and cve_item['metrics']['cvssMetricV30']:
            cvss_v3 = cve_item['metrics']['cvssMetricV30'][0]['cvssData']
            metrics['cvss_v3_score'] = cvss_v3.get('baseScore')
            metrics['cvss_v3_severity'] = cvss_v3.get('baseSeverity')
        
        # Try to get CVSS v2 metrics
        if 'cvssMetricV2' in cve_item['metrics'] and cve_item['metrics']['cvssMetricV2']:
            cvss_v2 = cve_item['metrics']['cvssMetricV2'][0]['cvssData']
            metrics['cvss_v2_score'] = cvss_v2.get('baseScore')
            metrics['cvss_v2_severity'] = cvss_v2.get('baseSeverity', 'UNKNOWN')
    
    return metrics


def parse_cwe_ids(cve_item: Dict[str, Any]) -> List[str]:
    """
    Extract CWE IDs from CVE item.
    
    Args:
        cve_item: CVE vulnerability item
        
    Returns:
        List of CWE IDs
    """
    cwe_ids = []
    
    if 'weaknesses' in cve_item:
        for weakness in cve_item['weaknesses']:
            if 'description' in weakness:
                for desc in weakness['description']:
                    if desc.get('lang') == 'en' and desc.get('value', '').startswith('CWE-'):
                        cwe_ids.append(desc['value'])
    
    return cwe_ids


def parse_cpe_data(cve_item: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract CPE (Common Platform Enumeration) data from CVE item.
    
    Args:
        cve_item: CVE vulnerability item
        
    Returns:
        List of dictionaries with vendor, product, version info
    """
    cpe_list = []
    
    if 'configurations' in cve_item:
        for config in cve_item['configurations']:
            if 'nodes' in config:
                for node in config['nodes']:
                    if 'cpeMatch' in node:
                        for cpe_match in node['cpeMatch']:
                            if cpe_match.get('vulnerable', False):
                                cpe_uri = cpe_match.get('criteria', '')
                                if cpe_uri.startswith('cpe:2.3:'):
                                    parts = cpe_uri.split(':')
                                    if len(parts) >= 6:
                                        cpe_list.append({
                                            'vendor': parts[3],
                                            'product': parts[4],
                                            'version': parts[5] if parts[5] != '*' else 'ANY'
                                        })
    
    return cpe_list


def ingest_cves_to_db(nvd_data: Dict[str, Any], conn: sqlite3.Connection) -> int:
    """
    Ingest CVE data into the database.
    
    Args:
        nvd_data: NVD data dictionary
        conn: Database connection
        
    Returns:
        Number of CVEs ingested
    """
    cursor = conn.cursor()
    ingested_count = 0
    updated_count = 0
    
    vulnerabilities = nvd_data.get('vulnerabilities', [])
    total_cves = len(vulnerabilities)
    
    logger.info(f"Processing {total_cves} CVEs...")
    
    for idx, vuln_item in enumerate(vulnerabilities, 1):
        if idx % 100 == 0:
            logger.info(f"Processed {idx}/{total_cves} CVEs...")
        
        cve = vuln_item.get('cve', {})
        cve_id = cve.get('id')
        
        if not cve_id:
            continue
        
        # Extract basic CVE information
        descriptions = cve.get('descriptions', [])
        description = next((d['value'] for d in descriptions if d.get('lang') == 'en'), '')
        
        published_date = cve.get('published')
        last_modified_date = cve.get('lastModified')
        
        # Get CVSS metrics
        metrics = parse_cvss_metrics(cve)
        
        # Get CWE IDs
        cwe_ids = parse_cwe_ids(cve)
        cwe_id = cwe_ids[0] if cwe_ids else None
        
        # Get references
        references = cve.get('references', [])
        reference_urls = [ref.get('url') for ref in references if ref.get('url')]
        
        # Get CPE data for vendor/product
        cpe_data = parse_cpe_data(cve)
        vendor = cpe_data[0]['vendor'] if cpe_data else 'Unknown'
        product = cpe_data[0]['product'] if cpe_data else 'Unknown'
        
        # Check if CVE already exists
        cursor.execute('SELECT cve_id FROM vulnerabilities WHERE cve_id = ?', (cve_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute('''
                UPDATE vulnerabilities
                SET description = ?,
                    published_date = ?,
                    last_modified_date = ?,
                    cvss_score = ?,
                    severity = ?,
                    cwe_id = ?,
                    vendor = ?,
                    product = ?,
                    reference_url = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cve_id = ?
            ''', (
                description,
                published_date,
                last_modified_date,
                metrics['cvss_v3_score'] or metrics['cvss_v2_score'],
                metrics['cvss_v3_severity'] or metrics['cvss_v2_severity'],
                cwe_id,
                vendor,
                product,
                reference_urls[0] if reference_urls else None,
                cve_id
            ))
            updated_count += 1
        else:
            # Insert new record
            try:
                cursor.execute('''
                    INSERT INTO vulnerabilities (
                        cve_id, description, published_date, last_modified_date,
                        cvss_score, severity, cwe_id, vendor, product,
                        reference_url, is_exploited, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    cve_id,
                    description,
                    published_date,
                    last_modified_date,
                    metrics['cvss_v3_score'] or metrics['cvss_v2_score'],
                    metrics['cvss_v3_severity'] or metrics['cvss_v2_severity'],
                    cwe_id,
                    vendor,
                    product,
                    reference_urls[0] if reference_urls else None,
                    False  # Will be updated by CISA KEV ingestion
                ))
                ingested_count += 1
            except sqlite3.IntegrityError:
                logger.warning(f"Duplicate CVE ID: {cve_id}")
                continue
    
    conn.commit()
    logger.info(f"Successfully ingested {ingested_count} new CVEs and updated {updated_count} existing CVEs")
    
    return ingested_count + updated_count


def update_exploited_status(conn: sqlite3.Connection, kev_file_path: Optional[str] = None) -> int:
    """
    Update the is_exploited flag for CVEs that are in the CISA KEV catalog.
    
    Args:
        conn: Database connection
        kev_file_path: Path to CISA KEV JSON file
        
    Returns:
        Number of CVEs updated
    """
    if not kev_file_path:
        kev_file_path = 'data/raw/cisa_kev/known_exploited_vulnerabilities.json'
    
    kev_path = Path(kev_file_path)
    if not kev_path.exists():
        logger.warning(f"KEV file not found: {kev_file_path}. Skipping exploited status update.")
        return 0
    
    try:
        with open(kev_path, 'r', encoding='utf-8') as f:
            kev_data = json.load(f)
        
        cursor = conn.cursor()
        updated_count = 0
        
        for vuln in kev_data.get('vulnerabilities', []):
            cve_id = vuln.get('cveID')
            if cve_id:
                cursor.execute('''
                    UPDATE vulnerabilities
                    SET is_exploited = TRUE,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE cve_id = ? AND is_exploited = FALSE
                ''', (cve_id,))
                if cursor.rowcount > 0:
                    updated_count += 1
        
        conn.commit()
        logger.info(f"Updated exploited status for {updated_count} CVEs from CISA KEV")
        return updated_count
        
    except Exception as e:
        logger.error(f"Error updating exploited status: {e}")
        return 0


def main():
    """Main execution function."""
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    nvd_file = project_root / 'data' / 'raw' / 'nist_nvd' / 'nvd_recent_cves.json'
    kev_file = project_root / 'data' / 'raw' / 'cisa_kev' / 'known_exploited_vulnerabilities.json'
    db_file = project_root / 'data' / 'processed' / 'grc_analytics.db'
    
    logger.info("=" * 60)
    logger.info("NVD CVE Ingestion Script")
    logger.info("=" * 60)
    
    # Check if NVD file exists
    if not nvd_file.exists():
        logger.error(f"NVD file not found: {nvd_file}")
        logger.info("Please ensure the NVD data file is downloaded.")
        sys.exit(1)
    
    # Load NVD data
    nvd_data = load_nvd_data(str(nvd_file))
    
    # Get database connection
    conn = get_db_connection(str(db_file))
    
    try:
        # Ingest CVEs
        total_processed = ingest_cves_to_db(nvd_data, conn)
        
        # Update exploited status from CISA KEV
        if kev_file.exists():
            update_exploited_status(conn, str(kev_file))
        
        logger.info("=" * 60)
        logger.info(f"Total CVEs processed: {total_processed}")
        logger.info("Ingestion completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
