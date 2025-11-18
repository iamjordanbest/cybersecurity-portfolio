#!/usr/bin/env python3
"""
CVE to NIST Controls Auto-Mapping Script

This script automatically maps CVEs to NIST 800-53 controls based on:
1. CWE (Common Weakness Enumeration) to control family mapping
2. Vulnerability type and impact analysis
3. CVSS metrics and severity levels
4. Attack vectors and exploitation characteristics
"""

import sqlite3
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set
import logging
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# CWE to NIST 800-53 Control Mapping
# Based on common vulnerability patterns and security control objectives
CWE_TO_CONTROL_MAPPING = {
    # Access Control Issues
    'CWE-284': ['AC-2', 'AC-3', 'AC-6'],  # Improper Access Control
    'CWE-285': ['AC-3', 'AC-6'],  # Improper Authorization
    'CWE-287': ['IA-2', 'IA-5', 'AC-7'],  # Improper Authentication
    'CWE-288': ['IA-2', 'IA-5'],  # Authentication Bypass
    'CWE-306': ['IA-2', 'IA-9'],  # Missing Authentication
    'CWE-307': ['AC-7', 'IA-5'],  # Improper Restriction of Excessive Authentication Attempts
    'CWE-862': ['AC-3', 'AC-6'],  # Missing Authorization
    'CWE-863': ['AC-3', 'AC-4'],  # Incorrect Authorization
    
    # Injection Vulnerabilities
    'CWE-78': ['SI-10', 'CM-7', 'AC-6'],  # OS Command Injection
    'CWE-79': ['SI-10', 'SI-15'],  # Cross-Site Scripting
    'CWE-89': ['SI-10', 'AC-6'],  # SQL Injection
    'CWE-94': ['SI-10', 'CM-7'],  # Code Injection
    'CWE-95': ['SI-10', 'CM-7'],  # Eval Injection
    
    # Memory/Buffer Issues
    'CWE-119': ['SI-16', 'SA-15'],  # Buffer Errors
    'CWE-120': ['SI-16', 'SA-15'],  # Buffer Overflow
    'CWE-125': ['SI-16', 'SA-15'],  # Out-of-bounds Read
    'CWE-787': ['SI-16', 'SA-15'],  # Out-of-bounds Write
    'CWE-416': ['SI-16', 'SA-15'],  # Use After Free
    
    # Configuration/Deployment
    'CWE-16': ['CM-2', 'CM-6', 'CM-7'],  # Configuration
    'CWE-732': ['AC-3', 'AC-6', 'CM-6'],  # Incorrect Permission Assignment
    'CWE-276': ['AC-3', 'AC-6'],  # Incorrect Default Permissions
    'CWE-798': ['IA-5', 'SA-4'],  # Hard-coded Credentials
    'CWE-522': ['IA-5', 'SC-28'],  # Insufficiently Protected Credentials
    
    # Path/Directory Traversal
    'CWE-22': ['AC-3', 'AC-4', 'SI-10'],  # Path Traversal
    'CWE-23': ['AC-3', 'SI-10'],  # Relative Path Traversal
    'CWE-35': ['AC-4', 'SI-10'],  # Path Traversal
    
    # Input Validation
    'CWE-20': ['SI-10', 'SI-15'],  # Improper Input Validation
    'CWE-74': ['SI-10'],  # Injection
    'CWE-129': ['SI-10', 'SI-16'],  # Improper Validation of Array Index
    
    # Cryptographic Issues
    'CWE-326': ['SC-12', 'SC-13'],  # Inadequate Encryption Strength
    'CWE-327': ['SC-12', 'SC-13'],  # Use of Broken Crypto
    'CWE-328': ['SC-13'],  # Use of Weak Hash
    'CWE-329': ['SC-13', 'SC-28'],  # Not Using Random IV
    'CWE-330': ['SC-13'],  # Use of Insufficiently Random Values
    
    # Information Disclosure
    'CWE-200': ['AC-3', 'SC-4'],  # Information Exposure
    'CWE-209': ['SI-11', 'SC-4'],  # Information in Error Messages
    'CWE-532': ['AU-9', 'SC-4'],  # Insertion of Sensitive Info in Log
    'CWE-552': ['AC-3', 'CM-6'],  # Files Accessible to External Parties
    
    # Privilege Escalation
    'CWE-269': ['AC-6', 'CM-5'],  # Improper Privilege Management
    'CWE-267': ['AC-6', 'CM-5'],  # Privilege Defined with Unsafe Actions
    'CWE-250': ['AC-6'],  # Execution with Unnecessary Privileges
    
    # Race Conditions
    'CWE-362': ['SC-3', 'SI-16'],  # Race Condition
    'CWE-367': ['SC-3'],  # Time-of-check Time-of-use
    
    # Deserialization
    'CWE-502': ['SI-10', 'CM-7'],  # Deserialization of Untrusted Data
    
    # File Upload
    'CWE-434': ['SI-10', 'SI-3', 'CM-7'],  # Unrestricted File Upload
    
    # SSRF and Network Issues
    'CWE-918': ['AC-4', 'SC-7'],  # Server-Side Request Forgery
    'CWE-940': ['AC-4', 'SC-7'],  # Improper Verification of Source
    
    # XML/XXE Issues
    'CWE-611': ['SI-10', 'CM-7'],  # XXE
}


# Severity-based control recommendations
SEVERITY_CONTROL_MAPPING = {
    'CRITICAL': ['IR-4', 'IR-5', 'RA-5', 'SI-2'],
    'HIGH': ['IR-4', 'RA-5', 'SI-2'],
    'MEDIUM': ['RA-5', 'SI-2'],
    'LOW': ['RA-5']
}


# Exploited vulnerability additional controls
EXPLOITED_CONTROLS = ['IR-4', 'IR-6', 'SI-4', 'SI-5']


def get_db_connection(db_path: str = 'grc_analytics.db') -> sqlite3.Connection:
    """Create a database connection to SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)


def extract_cwe_from_text(text: str) -> List[str]:
    """
    Extract CWE IDs from text using regex.
    
    Args:
        text: Text that might contain CWE references
        
    Returns:
        List of CWE IDs found
    """
    pattern = r'CWE-\d+'
    return re.findall(pattern, text.upper())


def get_controls_for_cwe(cwe_id: str) -> List[str]:
    """
    Get NIST controls mapped to a specific CWE.
    
    Args:
        cwe_id: CWE identifier (e.g., 'CWE-79')
        
    Returns:
        List of control IDs
    """
    return CWE_TO_CONTROL_MAPPING.get(cwe_id, [])


def get_controls_for_severity(severity: str) -> List[str]:
    """
    Get NIST controls based on vulnerability severity.
    
    Args:
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
        
    Returns:
        List of control IDs
    """
    if not severity:
        return []
    return SEVERITY_CONTROL_MAPPING.get(severity.upper(), [])


def map_cve_to_controls(cve_data: Dict) -> Tuple[Set[str], Dict[str, str]]:
    """
    Map a CVE to relevant NIST controls.
    
    Args:
        cve_data: Dictionary containing CVE information
        
    Returns:
        Tuple of (set of control IDs, mapping justification dict)
    """
    control_ids = set()
    justifications = {}
    
    cve_id = cve_data['cve_id']
    cwe_id = cve_data.get('cwe_id')
    severity = cve_data.get('severity')
    is_exploited = cve_data.get('is_exploited', False)
    description = cve_data.get('description', '')
    
    # Map based on CWE
    if cwe_id:
        cwe_controls = get_controls_for_cwe(cwe_id)
        for control in cwe_controls:
            control_ids.add(control)
            justifications[control] = f"Mapped via {cwe_id}"
    
    # Extract additional CWEs from description
    description_cwes = extract_cwe_from_text(description)
    for desc_cwe in description_cwes:
        desc_controls = get_controls_for_cwe(desc_cwe)
        for control in desc_controls:
            control_ids.add(control)
            if control not in justifications:
                justifications[control] = f"Mapped via {desc_cwe} from description"
    
    # Map based on severity
    if severity:
        severity_controls = get_controls_for_severity(severity)
        for control in severity_controls:
            control_ids.add(control)
            if control not in justifications:
                justifications[control] = f"Mapped via {severity} severity"
    
    # Additional controls for exploited vulnerabilities
    if is_exploited:
        for control in EXPLOITED_CONTROLS:
            control_ids.add(control)
            if control not in justifications:
                justifications[control] = "Mapped due to active exploitation"
    
    # Keyword-based mapping for specific vulnerability types
    desc_lower = description.lower()
    
    if any(word in desc_lower for word in ['authentication', 'login', 'credential']):
        for control in ['IA-2', 'IA-5']:
            control_ids.add(control)
            if control not in justifications:
                justifications[control] = "Mapped via authentication keywords"
    
    if any(word in desc_lower for word in ['encryption', 'decrypt', 'cryptographic']):
        for control in ['SC-12', 'SC-13']:
            control_ids.add(control)
            if control not in justifications:
                justifications[control] = "Mapped via cryptography keywords"
    
    if any(word in desc_lower for word in ['audit', 'log', 'logging']):
        for control in ['AU-2', 'AU-3', 'AU-6']:
            control_ids.add(control)
            if control not in justifications:
                justifications[control] = "Mapped via audit/logging keywords"
    
    if any(word in desc_lower for word in ['backup', 'recovery']):
        for control in ['CP-9', 'CP-10']:
            control_ids.add(control)
            if control not in justifications:
                justifications[control] = "Mapped via backup keywords"
    
    if any(word in desc_lower for word in ['patch', 'update', 'vulnerability']):
        for control in ['SI-2', 'RA-5']:
            control_ids.add(control)
            if control not in justifications:
                justifications[control] = "Mapped via patching keywords"
    
    return control_ids, justifications


def automap_cves(conn: sqlite3.Connection, limit: int = None) -> Tuple[int, int]:
    """
    Automatically map CVEs to NIST controls.
    
    Args:
        conn: Database connection
        limit: Maximum number of CVEs to process (None for all)
        
    Returns:
        Tuple of (CVEs processed, mappings created)
    """
    cursor = conn.cursor()
    
    # Get all CVEs from CISA KEV (primary source for exploited vulnerabilities)
    query = '''
        SELECT 
            cve_id,
            vulnerability_name as description,
            'CRITICAL' as severity,
            1 as is_exploited,
            NULL as cwe_id
        FROM cisa_kev
    '''
    if limit:
        query += f' LIMIT {limit}'
    
    cursor.execute(query)
    cves = cursor.fetchall()
    
    logger.info(f"Processing {len(cves)} CVEs for auto-mapping...")
    
    cves_processed = 0
    mappings_created = 0
    
    for idx, cve in enumerate(cves, 1):
        if idx % 100 == 0:
            logger.info(f"Processed {idx}/{len(cves)} CVEs...")
        
        cve_data = dict(cve)
        cve_id = cve_data['cve_id']
        
        # Get mapped controls
        control_ids, justifications = map_cve_to_controls(cve_data)
        
        if not control_ids:
            # Default mapping if no specific controls found
            control_ids = {'RA-5', 'SI-2'}
            justifications = {
                'RA-5': 'Default vulnerability scanning control',
                'SI-2': 'Default flaw remediation control'
            }
        
        # Insert mappings
        for control_id in control_ids:
            # Check if control exists in database
            cursor.execute('SELECT control_id FROM nist_controls WHERE control_id = ?', (control_id,))
            if not cursor.fetchone():
                logger.debug(f"Control {control_id} not found in database, skipping")
                continue
            
            # Check if mapping already exists
            cursor.execute('''
                SELECT id FROM cve_control_mapping 
                WHERE cve_id = ? AND control_id = ?
            ''', (cve_id, control_id))
            
            if cursor.fetchone():
                continue  # Mapping already exists
            
            # Insert new mapping
            try:
                cursor.execute('''
                    INSERT INTO cve_control_mapping (
                        cve_id, control_id, mapping_type, confidence_score,
                        mapping_source, notes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    cve_id,
                    control_id,
                    'primary',
                    0.8,  # Default confidence score for automated mapping
                    'automated',
                    justifications.get(control_id, 'Automated mapping')
                ))
                mappings_created += 1
            except sqlite3.IntegrityError:
                logger.debug(f"Mapping already exists: {cve_id} -> {control_id}")
                continue
        
        cves_processed += 1
    
    conn.commit()
    logger.info(f"Successfully processed {cves_processed} CVEs and created {mappings_created} mappings")
    
    return cves_processed, mappings_created


def generate_mapping_report(conn: sqlite3.Connection, output_file: str = None):
    """
    Generate a report of CVE to control mappings.
    
    Args:
        conn: Database connection
        output_file: Optional output file path for JSON report
    """
    cursor = conn.cursor()
    
    # Get mapping statistics
    cursor.execute('''
        SELECT 
            COUNT(DISTINCT cve_id) as total_cves_mapped,
            COUNT(DISTINCT control_id) as total_controls_mapped,
            COUNT(*) as total_mappings
        FROM cve_control_mapping
    ''')
    stats = cursor.fetchone()
    
    # Get top mapped controls
    cursor.execute('''
        SELECT 
            vcm.control_id,
            nc.control_name,
            COUNT(*) as mapping_count
        FROM cve_control_mapping vcm
        JOIN nist_controls nc ON vcm.control_id = nc.control_id
        GROUP BY vcm.control_id
        ORDER BY mapping_count DESC
        LIMIT 10
    ''')
    top_controls = cursor.fetchall()
    
    # Get controls with most critical CVEs (using CISA KEV as proxy for critical)
    cursor.execute('''
        SELECT 
            vcm.control_id,
            nc.control_name,
            COUNT(*) as critical_count,
            0 as high_count
        FROM cve_control_mapping vcm
        JOIN nist_controls nc ON vcm.control_id = nc.control_id
        JOIN cisa_kev v ON vcm.cve_id = v.cve_id
        GROUP BY vcm.control_id
        ORDER BY critical_count DESC
        LIMIT 10
    ''')
    high_risk_controls = cursor.fetchall()
    
    report = {
        'statistics': {
            'total_cves_mapped': stats['total_cves_mapped'],
            'total_controls_mapped': stats['total_controls_mapped'],
            'total_mappings': stats['total_mappings']
        },
        'top_mapped_controls': [
            {
                'control_id': row['control_id'],
                'title': row['control_name'],
                'mapping_count': row['mapping_count']
            }
            for row in top_controls
        ],
        'high_risk_controls': [
            {
                'control_id': row['control_id'],
                'title': row['control_name'],
                'critical_cves': row['critical_count'],
                'high_cves': row['high_count']
            }
            for row in high_risk_controls
        ]
    }
    
    # Display report
    logger.info("\n" + "=" * 60)
    logger.info("CVE TO CONTROL MAPPING REPORT")
    logger.info("=" * 60)
    logger.info(f"Total CVEs Mapped: {report['statistics']['total_cves_mapped']}")
    logger.info(f"Total Controls Mapped: {report['statistics']['total_controls_mapped']}")
    logger.info(f"Total Mappings Created: {report['statistics']['total_mappings']}")
    
    logger.info("\n" + "-" * 60)
    logger.info("TOP 10 MOST MAPPED CONTROLS:")
    logger.info("-" * 60)
    for control in report['top_mapped_controls']:
        logger.info(f"{control['control_id']}: {control['title']} ({control['mapping_count']} CVEs)")
    
    logger.info("\n" + "-" * 60)
    logger.info("TOP 10 HIGH-RISK CONTROLS:")
    logger.info("-" * 60)
    for control in report['high_risk_controls']:
        logger.info(f"{control['control_id']}: {control['title']} "
                   f"(Critical: {control['critical_cves']}, High: {control['high_cves']})")
    
    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"\nReport saved to: {output_file}")


def main():
    """Main execution function."""
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    db_file = project_root / 'data' / 'processed' / 'grc_analytics.db'
    report_file = project_root / 'outputs' / 'reports' / 'cve_control_mapping_report.json'
    
    logger.info("=" * 60)
    logger.info("CVE to NIST Controls Auto-Mapping Script")
    logger.info("=" * 60)
    
    # Get database connection
    conn = get_db_connection(str(db_file))
    
    try:
        # Perform auto-mapping
        cves_processed, mappings_created = automap_cves(conn)
        
        logger.info("\n" + "=" * 60)
        logger.info(f"CVEs Processed: {cves_processed}")
        logger.info(f"Mappings Created: {mappings_created}")
        logger.info("=" * 60)
        
        # Generate report
        report_file.parent.mkdir(parents=True, exist_ok=True)
        generate_mapping_report(conn, str(report_file))
        
        logger.info("\nAuto-mapping completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during auto-mapping: {e}", exc_info=True)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
