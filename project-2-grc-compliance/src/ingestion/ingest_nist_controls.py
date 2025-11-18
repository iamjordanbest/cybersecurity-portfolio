#!/usr/bin/env python3
"""
NIST 800-53 Controls Ingestion Script

This script ingests NIST 800-53 control data from OSCAL JSON format
and stores it in the SQLite database for the GRC Analytics Platform.
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


def get_db_connection(db_path: str = 'grc_analytics.db') -> sqlite3.Connection:
    """Create a database connection to SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)


def load_oscal_catalog(json_file_path: str) -> Dict[str, Any]:
    """Load NIST 800-53 control catalog from OSCAL JSON file."""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded OSCAL catalog from {json_file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        sys.exit(1)


def extract_control_text(parts: List[Dict[str, Any]]) -> str:
    """
    Extract and concatenate control text from parts.
    
    Args:
        parts: List of control parts
        
    Returns:
        Concatenated control text
    """
    text_parts = []
    
    for part in parts:
        if 'prose' in part:
            text_parts.append(part['prose'])
        
        # Recursively process nested parts
        if 'parts' in part:
            nested_text = extract_control_text(part['parts'])
            if nested_text:
                text_parts.append(nested_text)
    
    return ' '.join(text_parts)


def parse_control(control: Dict[str, Any], family: str) -> Dict[str, Any]:
    """
    Parse a single control from OSCAL format.
    
    Args:
        control: Control dictionary from OSCAL
        family: Control family name
        
    Returns:
        Dictionary with parsed control data
    """
    control_id = control.get('id', '').upper()
    title = control.get('title', '')
    
    # Extract control text
    control_text = ''
    if 'parts' in control:
        control_text = extract_control_text(control['parts'])
    
    # Get control label
    label = control_id
    if 'props' in control:
        for prop in control['props']:
            if prop.get('name') == 'label':
                label = prop.get('value', control_id)
                break
    
    # Determine if it's an enhancement (has parent)
    is_enhancement = '-' in control_id and '(' in control_id
    parent_control_id = None
    if is_enhancement:
        parent_control_id = control_id.split('(')[0].strip()
    
    return {
        'control_id': control_id,
        'family': family,
        'title': title,
        'description': control_text[:1000] if control_text else title,  # Limit to 1000 chars
        'full_text': control_text,
        'label': label,
        'is_enhancement': is_enhancement,
        'parent_control_id': parent_control_id
    }


def ingest_controls_to_db(catalog_data: Dict[str, Any], conn: sqlite3.Connection) -> int:
    """
    Ingest NIST controls into the database.
    
    Args:
        catalog_data: OSCAL catalog data
        conn: Database connection
        
    Returns:
        Number of controls ingested
    """
    cursor = conn.cursor()
    ingested_count = 0
    
    catalog = catalog_data.get('catalog', {})
    groups = catalog.get('groups', [])
    
    logger.info(f"Processing {len(groups)} control families...")
    
    for group in groups:
        family_id = group.get('id', '').upper()
        family_title = group.get('title', '')
        
        logger.info(f"Processing family: {family_title} ({family_id})")
        
        controls = group.get('controls', [])
        
        for control in controls:
            control_data = parse_control(control, family_title)
            
            # Check if control already exists
            cursor.execute('SELECT control_id FROM nist_controls WHERE control_id = ?', 
                         (control_data['control_id'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute('''
                    UPDATE nist_controls
                    SET control_family = ?,
                        control_name = ?,
                        control_description = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE control_id = ?
                ''', (
                    control_data['family'],
                    control_data['title'],
                    control_data['description'],
                    control_data['control_id']
                ))
            else:
                # Insert new record
                try:
                    cursor.execute('''
                        INSERT INTO nist_controls (
                            control_id, control_family, control_name, control_description,
                            baseline_low, baseline_moderate, baseline_high,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ''', (
                        control_data['control_id'],
                        control_data['family'],
                        control_data['title'],
                        control_data['description'],
                        0,  # baseline_low
                        1,  # baseline_moderate (default)
                        0   # baseline_high
                    ))
                    ingested_count += 1
                except sqlite3.IntegrityError:
                    logger.warning(f"Duplicate control ID: {control_data['control_id']}")
                    continue
            
            # Process control enhancements
            if 'controls' in control:
                for enhancement in control['controls']:
                    enh_data = parse_control(enhancement, family_title)
                    
                    cursor.execute('SELECT control_id FROM nist_controls WHERE control_id = ?',
                                 (enh_data['control_id'],))
                    existing_enh = cursor.fetchone()
                    
                    if not existing_enh:
                        try:
                            cursor.execute('''
                                INSERT INTO nist_controls (
                                    control_id, control_family, control_name, control_description,
                                    baseline_low, baseline_moderate, baseline_high,
                                    created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            ''', (
                                enh_data['control_id'],
                                enh_data['family'],
                                enh_data['title'],
                                enh_data['description'],
                                0,  # baseline_low
                                1,  # baseline_moderate (default for enhancements)
                                0   # baseline_high
                            ))
                            ingested_count += 1
                        except sqlite3.IntegrityError:
                            continue
    
    conn.commit()
    logger.info(f"Successfully ingested {ingested_count} controls")
    
    return ingested_count


def main():
    """Main execution function."""
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    oscal_file = project_root / 'data' / 'raw' / 'nist_oscal' / 'oscal-content' / 'nist.gov' / 'SP800-53' / 'rev5' / 'json' / 'NIST_SP-800-53_rev5_catalog.json'
    db_file = project_root / 'data' / 'processed' / 'grc_analytics.db'
    
    logger.info("=" * 60)
    logger.info("NIST 800-53 Controls Ingestion Script")
    logger.info("=" * 60)
    
    # Check if OSCAL file exists
    if not oscal_file.exists():
        logger.error(f"OSCAL file not found: {oscal_file}")
        logger.info("Please ensure the NIST OSCAL data is available.")
        sys.exit(1)
    
    # Load OSCAL catalog
    catalog_data = load_oscal_catalog(str(oscal_file))
    
    # Get database connection
    conn = get_db_connection(str(db_file))
    
    try:
        # Ingest controls
        total_processed = ingest_controls_to_db(catalog_data, conn)
        
        logger.info("=" * 60)
        logger.info(f"Total controls processed: {total_processed}")
        logger.info("Ingestion completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
