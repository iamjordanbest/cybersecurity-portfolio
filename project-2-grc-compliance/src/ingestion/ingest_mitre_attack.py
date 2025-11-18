#!/usr/bin/env python3
"""
MITRE ATT&CK Ingestion Script

This script ingests MITRE ATT&CK techniques from the enterprise-attack.json file
and maps them to NIST 800-53 controls in the database.
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# MITRE ATT&CK Tactic to NIST Control Family Mapping
TACTIC_TO_CONTROL_FAMILY = {
    'reconnaissance': ['RA', 'CA'],
    'resource-development': ['SA', 'RA'],
    'initial-access': ['AC', 'SC', 'SI'],
    'execution': ['SI', 'CM'],
    'persistence': ['AC', 'CM', 'SI'],
    'privilege-escalation': ['AC', 'IA', 'CM'],
    'defense-evasion': ['SI', 'AU', 'AC'],
    'credential-access': ['IA', 'AC'],
    'discovery': ['SC', 'AC'],
    'lateral-movement': ['AC', 'SC'],
    'collection': ['AC', 'AU', 'SC'],
    'command-and-control': ['SC', 'SI'],
    'exfiltration': ['SC', 'AC'],
    'impact': ['CP', 'SC', 'SI']
}


# Technique pattern to control mapping
TECHNIQUE_PATTERNS = {
    'brute force': ['AC-7', 'IA-5'],
    'phishing': ['AT-2', 'AT-3', 'SC-7'],
    'credential': ['IA-2', 'IA-5', 'IA-8'],
    'malware': ['SI-3', 'SI-4', 'SI-8'],
    'exploit': ['SI-2', 'RA-5', 'CM-6'],
    'remote': ['AC-17', 'SC-7', 'SC-8'],
    'privilege': ['AC-6', 'CM-5'],
    'encryption': ['SC-12', 'SC-13', 'SC-28'],
    'log': ['AU-2', 'AU-3', 'AU-6', 'AU-9'],
    'network': ['SC-7', 'AC-4'],
    'data exfiltration': ['SC-7', 'AC-4', 'SI-4'],
    'backdoor': ['CM-7', 'SI-4'],
    'web': ['SC-5', 'SC-7', 'SI-10'],
    'injection': ['SI-10', 'CM-7'],
    'denial of service': ['SC-5', 'SC-6'],
}


def get_db_connection(db_path: str = 'grc_analytics.db') -> sqlite3.Connection:
    """Create a database connection to SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)


def load_attack_data(json_file_path: str) -> Dict[str, Any]:
    """Load MITRE ATT&CK data from JSON file."""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded MITRE ATT&CK data from {json_file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        sys.exit(1)


def get_external_id(external_refs: List[Dict]) -> Optional[str]:
    """Extract MITRE ATT&CK ID from external references."""
    for ref in external_refs:
        if ref.get('source_name') == 'mitre-attack':
            return ref.get('external_id')
    return None


def get_tactics_from_kill_chain(kill_chain_phases: List[Dict]) -> List[str]:
    """Extract tactic names from kill chain phases."""
    tactics = []
    for phase in kill_chain_phases:
        if phase.get('kill_chain_name') == 'mitre-attack':
            tactics.append(phase.get('phase_name'))
    return tactics


def map_technique_to_controls(technique_name: str, description: str, tactics: List[str]) -> List[str]:
    """
    Map MITRE ATT&CK technique to NIST controls.
    
    Args:
        technique_name: Name of the technique
        description: Technique description
        tactics: List of associated tactics
        
    Returns:
        List of control IDs
    """
    controls = set()
    
    # Map based on tactics
    for tactic in tactics:
        if tactic in TACTIC_TO_CONTROL_FAMILY:
            families = TACTIC_TO_CONTROL_FAMILY[tactic]
            # Add primary control from each family
            for family in families:
                controls.add(f"{family}-1")  # Add the policy/procedures control
    
    # Map based on technique patterns
    text = f"{technique_name} {description}".lower()
    for pattern, pattern_controls in TECHNIQUE_PATTERNS.items():
        if pattern in text:
            controls.update(pattern_controls)
    
    return list(controls)


def ingest_attack_techniques(attack_data: Dict[str, Any], conn: sqlite3.Connection) -> int:
    """
    Ingest MITRE ATT&CK techniques into the database.
    
    Args:
        attack_data: MITRE ATT&CK data dictionary
        conn: Database connection
        
    Returns:
        Number of techniques ingested
    """
    cursor = conn.cursor()
    ingested_count = 0
    
    objects = attack_data.get('objects', [])
    techniques = [obj for obj in objects if obj.get('type') == 'attack-pattern']
    
    logger.info(f"Processing {len(techniques)} MITRE ATT&CK techniques...")
    
    for idx, technique in enumerate(techniques, 1):
        if idx % 50 == 0:
            logger.info(f"Processed {idx}/{len(techniques)} techniques...")
        
        # Skip deprecated techniques
        if technique.get('x_mitre_deprecated', False) or technique.get('revoked', False):
            continue
        
        # Extract technique information
        external_refs = technique.get('external_references', [])
        technique_id = get_external_id(external_refs)
        
        if not technique_id:
            continue
        
        name = technique.get('name', '')
        description = technique.get('description', '')
        
        # Get tactics
        kill_chain_phases = technique.get('kill_chain_phases', [])
        tactics = get_tactics_from_kill_chain(kill_chain_phases)
        tactic_str = ', '.join(tactics)
        
        # Check if technique already exists
        cursor.execute('SELECT technique_id FROM mitre_attack_techniques WHERE technique_id = ?', 
                      (technique_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute('''
                UPDATE mitre_attack_techniques
                SET technique_name = ?,
                    description = ?,
                    tactic = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE technique_id = ?
            ''', (name, description, tactic_str, technique_id))
        else:
            # Insert new record
            try:
                cursor.execute('''
                    INSERT INTO mitre_attack_techniques (
                        technique_id, technique_name, description, tactic,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (technique_id, name, description, tactic_str))
                ingested_count += 1
            except sqlite3.IntegrityError:
                logger.warning(f"Duplicate technique ID: {technique_id}")
                continue
    
    conn.commit()
    logger.info(f"Successfully ingested {ingested_count} MITRE ATT&CK techniques")
    
    return ingested_count


def map_attack_to_controls(conn: sqlite3.Connection) -> int:
    """
    Create mappings between MITRE ATT&CK techniques and NIST controls.
    
    Args:
        conn: Database connection
        
    Returns:
        Number of mappings created
    """
    cursor = conn.cursor()
    
    # Get all techniques
    cursor.execute('SELECT * FROM mitre_attack_techniques')
    techniques = cursor.fetchall()
    
    logger.info(f"Creating mappings for {len(techniques)} techniques...")
    
    mappings_created = 0
    
    for technique in techniques:
        technique_id = technique['technique_id']
        name = technique['technique_name']
        description = technique['description']
        tactics = technique['tactic'].split(', ') if technique['tactic'] else []
        
        # Get mapped controls
        control_ids = map_technique_to_controls(name, description, tactics)
        
        if not control_ids:
            continue
        
        # Insert mappings
        for control_id in control_ids:
            # Check if control exists
            cursor.execute('SELECT control_id FROM nist_controls WHERE control_id = ?', (control_id,))
            if not cursor.fetchone():
                continue
            
            # Check if mapping already exists
            cursor.execute('''
                SELECT id FROM attack_control_mapping 
                WHERE technique_id = ? AND control_id = ?
            ''', (technique_id, control_id))
            
            if cursor.fetchone():
                continue
            
            # Insert new mapping
            try:
                cursor.execute('''
                    INSERT INTO attack_control_mapping (
                        technique_id, control_id, effectiveness,
                        created_at
                    ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (technique_id, control_id, 'medium'))  # Medium effectiveness for automated mapping
                mappings_created += 1
            except sqlite3.IntegrityError:
                continue
    
    conn.commit()
    logger.info(f"Successfully created {mappings_created} technique-to-control mappings")
    
    return mappings_created


def generate_attack_report(conn: sqlite3.Connection):
    """
    Generate a report of MITRE ATT&CK ingestion.
    
    Args:
        conn: Database connection
    """
    cursor = conn.cursor()
    
    # Get statistics
    cursor.execute('SELECT COUNT(*) as total FROM mitre_attack_techniques')
    total_techniques = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(DISTINCT tactic) as total FROM mitre_attack_techniques WHERE tactic IS NOT NULL')
    
    cursor.execute('SELECT COUNT(*) as total FROM attack_control_mapping')
    total_mappings = cursor.fetchone()['total']
    
    # Get top tactics
    cursor.execute('''
        SELECT tactic, COUNT(*) as count
        FROM mitre_attack_techniques
        WHERE tactic IS NOT NULL AND tactic != ''
        GROUP BY tactic
        ORDER BY count DESC
        LIMIT 10
    ''')
    top_tactics = cursor.fetchall()
    
    # Get most mapped controls
    cursor.execute('''
        SELECT 
            acm.control_id,
            nc.control_name,
            COUNT(*) as technique_count
        FROM attack_control_mapping acm
        JOIN nist_controls nc ON acm.control_id = nc.control_id
        GROUP BY acm.control_id
        ORDER BY technique_count DESC
        LIMIT 10
    ''')
    top_controls = cursor.fetchall()
    
    logger.info("\n" + "=" * 60)
    logger.info("MITRE ATT&CK INGESTION REPORT")
    logger.info("=" * 60)
    logger.info(f"Total Techniques Ingested: {total_techniques}")
    logger.info(f"Total Mappings Created: {total_mappings}")
    
    logger.info("\n" + "-" * 60)
    logger.info("TOP 10 TACTICS:")
    logger.info("-" * 60)
    for row in top_tactics:
        logger.info(f"{row['tactic']}: {row['count']} techniques")
    
    logger.info("\n" + "-" * 60)
    logger.info("TOP 10 MOST MAPPED CONTROLS:")
    logger.info("-" * 60)
    for row in top_controls:
        logger.info(f"{row['control_id']}: {row['control_name']} ({row['technique_count']} techniques)")


def main():
    """Main execution function."""
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    attack_file = project_root / 'data' / 'raw' / 'mitre_attack' / 'cti' / 'enterprise-attack' / 'enterprise-attack.json'
    db_file = project_root / 'data' / 'processed' / 'grc_analytics.db'
    
    logger.info("=" * 60)
    logger.info("MITRE ATT&CK Ingestion Script")
    logger.info("=" * 60)
    
    # Check if ATT&CK file exists
    if not attack_file.exists():
        logger.error(f"MITRE ATT&CK file not found: {attack_file}")
        logger.info("Please ensure the MITRE ATT&CK data is available.")
        sys.exit(1)
    
    # Load ATT&CK data
    attack_data = load_attack_data(str(attack_file))
    
    # Get database connection
    conn = get_db_connection(str(db_file))
    
    try:
        # Ingest techniques
        techniques_ingested = ingest_attack_techniques(attack_data, conn)
        
        # Create mappings
        mappings_created = map_attack_to_controls(conn)
        
        # Generate report
        generate_attack_report(conn)
        
        logger.info("\n" + "=" * 60)
        logger.info("Ingestion completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
