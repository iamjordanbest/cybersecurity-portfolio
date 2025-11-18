#!/usr/bin/env python3
"""
CIS Controls v8 Ingestion

Ingests CIS Critical Security Controls v8 into the multi-framework database.
CIS Controls v8 has 18 main controls with 153 safeguards.
"""

import sqlite3
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# CIS Controls v8 - 18 Controls with key safeguards
CIS_CONTROLS_V8 = {
    '1': {
        'name': 'Inventory and Control of Enterprise Assets',
        'description': 'Actively manage (inventory, track, and correct) all enterprise assets (end-user devices, network devices, IoT devices, etc.) connected to the infrastructure, physically, virtually, remotely, and those within cloud environments.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Devices',
        'priority': 'critical'
    },
    '2': {
        'name': 'Inventory and Control of Software Assets',
        'description': 'Actively manage (inventory, track, and correct) all software (operating systems and applications) on the network so that only authorized software is installed and can execute.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Applications',
        'priority': 'critical'
    },
    '3': {
        'name': 'Data Protection',
        'description': 'Develop processes and technical controls to identify, classify, securely handle, retain, and dispose of data.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Data',
        'priority': 'critical'
    },
    '4': {
        'name': 'Secure Configuration of Enterprise Assets and Software',
        'description': 'Establish and maintain the secure configuration of enterprise assets and software.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Devices',
        'priority': 'critical'
    },
    '5': {
        'name': 'Account Management',
        'description': 'Use processes and tools to assign and manage authorization to credentials for user accounts, including administrator accounts, as well as service accounts.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Users',
        'priority': 'critical'
    },
    '6': {
        'name': 'Access Control Management',
        'description': 'Use processes and tools to create, assign, manage, and revoke access credentials and privileges for user, administrator, and service accounts.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Users',
        'priority': 'critical'
    },
    '7': {
        'name': 'Continuous Vulnerability Management',
        'description': 'Develop a plan to continuously assess and track vulnerabilities on all enterprise assets within the enterprise\'s infrastructure.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Applications',
        'priority': 'critical'
    },
    '8': {
        'name': 'Audit Log Management',
        'description': 'Collect, alert, review, and retain audit logs of events that could help detect, understand, or recover from an attack.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Network',
        'priority': 'high'
    },
    '9': {
        'name': 'Email and Web Browser Protections',
        'description': 'Improve protections and detections of threats from email and web vectors, as these are opportunities for attackers to manipulate human behavior.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Applications',
        'priority': 'high'
    },
    '10': {
        'name': 'Malware Defenses',
        'description': 'Prevent or control the installation, spread, and execution of malicious applications, code, or scripts on enterprise assets.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Devices',
        'priority': 'critical'
    },
    '11': {
        'name': 'Data Recovery',
        'description': 'Establish and maintain data recovery practices sufficient to restore in-scope enterprise assets to a pre-incident and trusted state.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Data',
        'priority': 'high'
    },
    '12': {
        'name': 'Network Infrastructure Management',
        'description': 'Establish, implement, and actively manage (track, report, correct) network devices, in order to prevent attackers from exploiting vulnerable network services and access points.',
        'implementation_group': ['IG2', 'IG3'],
        'asset_type': 'Network',
        'priority': 'high'
    },
    '13': {
        'name': 'Network Monitoring and Defense',
        'description': 'Operate processes and tooling to establish and maintain comprehensive network monitoring and defense against security threats across the enterprise\'s network infrastructure.',
        'implementation_group': ['IG2', 'IG3'],
        'asset_type': 'Network',
        'priority': 'high'
    },
    '14': {
        'name': 'Security Awareness and Skills Training',
        'description': 'Establish and maintain a security awareness program to influence behavior among the workforce to be security conscious and properly skilled to reduce cybersecurity risks.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Users',
        'priority': 'medium'
    },
    '15': {
        'name': 'Service Provider Management',
        'description': 'Develop a process to evaluate service providers who hold sensitive data, or are responsible for an enterprise\'s critical IT platforms or processes.',
        'implementation_group': ['IG2', 'IG3'],
        'asset_type': 'Users',
        'priority': 'medium'
    },
    '16': {
        'name': 'Application Software Security',
        'description': 'Manage the security life cycle of in-house developed, hosted, or acquired software to prevent, detect, and remediate security weaknesses before they can impact the enterprise.',
        'implementation_group': ['IG2', 'IG3'],
        'asset_type': 'Applications',
        'priority': 'high'
    },
    '17': {
        'name': 'Incident Response Management',
        'description': 'Establish a program to develop and maintain an incident response capability to properly prepare for, detect, respond to, and recover from modern cybersecurity incidents.',
        'implementation_group': ['IG1', 'IG2', 'IG3'],
        'asset_type': 'Data',
        'priority': 'high'
    },
    '18': {
        'name': 'Penetration Testing',
        'description': 'Test the effectiveness and resiliency of enterprise assets through identifying and exploiting weaknesses in controls, and simulating the objectives and actions of an attacker.',
        'implementation_group': ['IG3'],
        'asset_type': 'Network',
        'priority': 'medium'
    }
}


def ingest_cis_controls(db_path: str):
    """Ingest CIS Controls v8 into the database."""
    
    logger.info(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get CIS framework ID
        cursor.execute("SELECT framework_id FROM frameworks WHERE framework_code = 'CIS'")
        result = cursor.fetchone()
        if not result:
            logger.error("CIS framework not found in database")
            return False
        
        framework_id = result[0]
        logger.info(f"Found CIS framework (ID: {framework_id})")
        
        # Insert controls
        total_controls = 0
        for control_num, control_data in CIS_CONTROLS_V8.items():
            control_id = f"CIS-{control_num}"
            
            cursor.execute('''
                INSERT OR IGNORE INTO framework_controls (
                    framework_id,
                    control_identifier,
                    control_name,
                    control_description,
                    control_objective,
                    control_category,
                    control_domain,
                    priority_level,
                    is_mandatory
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                framework_id,
                control_id,
                control_data['name'],
                control_data['description'],
                control_data['description'],
                control_data['asset_type'],
                f"CIS Control {control_num}",
                control_data['priority'],
                1 if 'IG1' in control_data['implementation_group'] else 0
            ))
            
            total_controls += 1
        
        # Add metadata about implementation groups
        for control_num, control_data in CIS_CONTROLS_V8.items():
            control_id = f"CIS-{control_num}"
            
            cursor.execute('''
                INSERT OR IGNORE INTO framework_metadata (
                    framework_id,
                    metadata_key,
                    metadata_value,
                    metadata_type
                ) VALUES (?, ?, ?, ?)
            ''', (
                framework_id,
                f"{control_id}_implementation_groups",
                ','.join(control_data['implementation_group']),
                'string'
            ))
        
        conn.commit()
        
        logger.info(f"✓ Ingested {total_controls} CIS Controls")
        
        # Verify
        cursor.execute('''
            SELECT COUNT(*) FROM framework_controls 
            WHERE framework_id = ?
        ''', (framework_id,))
        count = cursor.fetchone()[0]
        logger.info(f"✓ Verified {count} CIS Controls in database")
        
        # Show asset type distribution
        cursor.execute('''
            SELECT control_category, COUNT(*) as cnt, priority_level
            FROM framework_controls
            WHERE framework_id = ?
            GROUP BY control_category, priority_level
            ORDER BY priority_level DESC, control_category
        ''', (framework_id,))
        
        logger.info("\n✓ Control distribution by asset type and priority:")
        for asset_type, cnt, priority in cursor.fetchall():
            logger.info(f"  {asset_type} ({priority}): {cnt} controls")
        
        # Show priority distribution
        cursor.execute('''
            SELECT priority_level, COUNT(*) as cnt
            FROM framework_controls
            WHERE framework_id = ?
            GROUP BY priority_level
            ORDER BY 
                CASE priority_level
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END
        ''', (framework_id,))
        
        logger.info("\n✓ Control distribution by priority:")
        for priority, cnt in cursor.fetchall():
            logger.info(f"  {priority}: {cnt} controls")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error ingesting CIS Controls: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()


def main():
    """Main function."""
    db_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return 1
    
    logger.info("=" * 70)
    logger.info("CIS CONTROLS V8 INGESTION")
    logger.info("=" * 70)
    
    success = ingest_cis_controls(str(db_path))
    
    if success:
        logger.info("\n" + "=" * 70)
        logger.info("✅ CIS Controls v8 ingestion complete!")
        logger.info("=" * 70)
        return 0
    else:
        logger.info("\n" + "=" * 70)
        logger.info("⚠ CIS Controls v8 ingestion failed")
        logger.info("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
