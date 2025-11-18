#!/usr/bin/env python3
"""
PCI-DSS v4.0 Requirements Ingestion

Ingests PCI-DSS v4.0 requirements into the multi-framework database.
PCI-DSS v4.0 has 12 principal requirements with multiple sub-requirements.
"""

import sqlite3
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# PCI-DSS v4.0 - 12 Principal Requirements
PCI_DSS_V4_REQUIREMENTS = {
    '1': {
        'name': 'Install and Maintain Network Security Controls',
        'description': 'Network security controls (NSCs) such as firewalls and other network security technologies, are network policy enforcement points that typically control network traffic between two or more logical or physical network segments (or subnets) based on pre-defined policies or rules.',
        'goal': 'Network Security',
        'priority': 'critical'
    },
    '2': {
        'name': 'Apply Secure Configurations to All System Components',
        'description': 'Malicious individuals, both external and internal to an entity, often use default passwords and other vendor default settings to compromise systems. These passwords and settings are well known and are easily determined via public information.',
        'goal': 'Secure Configuration',
        'priority': 'critical'
    },
    '3': {
        'name': 'Protect Stored Account Data',
        'description': 'Protection methods such as encryption, truncation, masking, and hashing are critical components of account data protection. If an intruder circumvents other security controls and gains access to encrypted account data, the data is unreadable without the proper cryptographic keys.',
        'goal': 'Data Protection',
        'priority': 'critical'
    },
    '4': {
        'name': 'Protect Cardholder Data with Strong Cryptography During Transmission',
        'description': 'Sensitive information must be encrypted during transmission over networks that are easily accessed by malicious individuals, including the Internet and wireless technologies.',
        'goal': 'Data Protection',
        'priority': 'critical'
    },
    '5': {
        'name': 'Protect All Systems and Networks from Malicious Software',
        'description': 'Malicious software (malware) is software or firmware designed to infiltrate or damage a computer system without the owner\'s knowledge or consent, with the intent of compromising the confidentiality, integrity, or availability of data, applications, or operating systems.',
        'goal': 'Malware Protection',
        'priority': 'critical'
    },
    '6': {
        'name': 'Develop and Maintain Secure Systems and Software',
        'description': 'Unscrupulous individuals use security vulnerabilities to gain privileged access to systems. Many of these vulnerabilities are fixed by vendor-provided security patches, which must be installed by the entities that manage the systems.',
        'goal': 'Secure Development',
        'priority': 'high'
    },
    '7': {
        'name': 'Restrict Access to System Components and Cardholder Data by Business Need to Know',
        'description': 'To ensure critical data can only be accessed by authorized personnel, systems and processes must be in place to limit access based on need to know and according to job responsibilities.',
        'goal': 'Access Control',
        'priority': 'critical'
    },
    '8': {
        'name': 'Identify Users and Authenticate Access to System Components',
        'description': 'Two fundamental principles for identifying users and managing their access to system components are to 1) assign a unique identification (ID) to each user, and 2) authenticate each user before allowing access to system components or cardholder data.',
        'goal': 'Identity Management',
        'priority': 'critical'
    },
    '9': {
        'name': 'Restrict Physical Access to Cardholder Data',
        'description': 'Any physical access to cardholder data or systems that store, process, or transmit cardholder data provides the opportunity for individuals to access and/or remove systems or hardcopies, and should be appropriately restricted.',
        'goal': 'Physical Security',
        'priority': 'high'
    },
    '10': {
        'name': 'Log and Monitor All Access to System Components and Cardholder Data',
        'description': 'Logging mechanisms and the ability to track user activities are critical for effective forensics and vulnerability management. The presence of logs on all system components and in the cardholder data environment (CDE) allows thorough tracking, alerting, and analysis.',
        'goal': 'Logging & Monitoring',
        'priority': 'critical'
    },
    '11': {
        'name': 'Test Security of Systems and Networks Regularly',
        'description': 'Vulnerabilities are being discovered continually by malicious individuals and researchers, and being introduced by new software. System components, processes, and bespoke and custom software should be tested frequently to ensure security controls continue to reflect a changing environment.',
        'goal': 'Security Testing',
        'priority': 'high'
    },
    '12': {
        'name': 'Support Information Security with Organizational Policies and Programs',
        'description': 'The organization\'s overall information security policy sets the tone for the whole entity and informs personnel what is expected of them. All personnel should be aware of the sensitivity of cardholder data and their responsibilities for protecting it.',
        'goal': 'Security Governance',
        'priority': 'high'
    }
}


def ingest_pci_dss(db_path: str):
    """Ingest PCI-DSS v4.0 requirements into the database."""
    
    logger.info(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get PCI-DSS framework ID
        cursor.execute("SELECT framework_id FROM frameworks WHERE framework_code = 'PCI-DSS'")
        result = cursor.fetchone()
        if not result:
            logger.error("PCI-DSS framework not found in database")
            return False
        
        framework_id = result[0]
        logger.info(f"Found PCI-DSS framework (ID: {framework_id})")
        
        # Insert requirements
        total_requirements = 0
        for req_num, req_data in PCI_DSS_V4_REQUIREMENTS.items():
            req_id = f"PCI-DSS-{req_num}"
            
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
                req_id,
                req_data['name'],
                req_data['description'],
                req_data['description'],
                req_data['goal'],
                f"Requirement {req_num}",
                req_data['priority'],
                1  # All PCI-DSS requirements are mandatory
            ))
            
            total_requirements += 1
        
        conn.commit()
        
        logger.info(f"✓ Ingested {total_requirements} PCI-DSS requirements")
        
        # Verify
        cursor.execute('''
            SELECT COUNT(*) FROM framework_controls 
            WHERE framework_id = ?
        ''', (framework_id,))
        count = cursor.fetchone()[0]
        logger.info(f"✓ Verified {count} PCI-DSS requirements in database")
        
        # Show goal distribution
        cursor.execute('''
            SELECT control_category, COUNT(*) as cnt, priority_level
            FROM framework_controls
            WHERE framework_id = ?
            GROUP BY control_category, priority_level
            ORDER BY priority_level DESC, control_category
        ''', (framework_id,))
        
        logger.info("\n✓ Requirement distribution by goal and priority:")
        for goal, cnt, priority in cursor.fetchall():
            logger.info(f"  {goal} ({priority}): {cnt} requirements")
        
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
        
        logger.info("\n✓ Requirement distribution by priority:")
        for priority, cnt in cursor.fetchall():
            logger.info(f"  {priority}: {cnt} requirements")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error ingesting PCI-DSS: {e}")
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
    logger.info("PCI-DSS V4.0 REQUIREMENTS INGESTION")
    logger.info("=" * 70)
    
    success = ingest_pci_dss(str(db_path))
    
    if success:
        logger.info("\n" + "=" * 70)
        logger.info("✅ PCI-DSS v4.0 ingestion complete!")
        logger.info("=" * 70)
        return 0
    else:
        logger.info("\n" + "=" * 70)
        logger.info("⚠ PCI-DSS v4.0 ingestion failed")
        logger.info("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
