#!/usr/bin/env python3
"""
SOC 2 Trust Services Criteria Ingestion

Ingests SOC 2 Trust Services Criteria into the multi-framework database.
SOC 2 has 5 Trust Service Principles with associated criteria.
"""

import sqlite3
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# SOC 2 Trust Services Criteria
SOC2_CRITERIA = {
    'CC': {
        'principle': 'Common Criteria',
        'description': 'Common Criteria related to all Trust Services Categories',
        'criteria': [
            ('CC1', 'Control Environment', 'The entity demonstrates a commitment to integrity and ethical values.', 'high'),
            ('CC2', 'Communication and Information', 'The entity obtains or generates and uses relevant, quality information to support the functioning of internal control.', 'high'),
            ('CC3', 'Risk Assessment', 'The entity identifies risks to the achievement of its objectives and analyzes risks as a basis for determining how the risks should be managed.', 'critical'),
            ('CC4', 'Monitoring Activities', 'The entity selects, develops, and performs ongoing and/or separate evaluations to ascertain whether the components of internal control are present and functioning.', 'high'),
            ('CC5', 'Control Activities', 'The entity selects and develops control activities that contribute to the mitigation of risks.', 'critical'),
            ('CC6', 'Logical and Physical Access Controls', 'The entity implements logical access security software, infrastructure, and architectures over protected information assets.', 'critical'),
            ('CC7', 'System Operations', 'The entity manages the selection, development, and implementation of its system.', 'high'),
            ('CC8', 'Change Management', 'The entity implements change management processes and procedures.', 'high'),
            ('CC9', 'Risk Mitigation', 'The entity identifies, selects, and develops risk mitigation activities for risks arising from potential business disruptions.', 'critical'),
        ]
    },
    'A': {
        'principle': 'Additional Criteria for Availability',
        'description': 'The system is available for operation and use as committed or agreed.',
        'criteria': [
            ('A1', 'Availability', 'The entity maintains, monitors, and evaluates current processing capacity and use of system components.', 'critical'),
        ]
    },
    'P': {
        'principle': 'Additional Criteria for Processing Integrity',
        'description': 'System processing is complete, valid, accurate, timely, and authorized.',
        'criteria': [
            ('P1', 'Processing Integrity', 'The entity obtains or generates, uses, and communicates relevant, quality information regarding the objectives related to processing.', 'high'),
        ]
    },
    'C': {
        'principle': 'Additional Criteria for Confidentiality',
        'description': 'Information designated as confidential is protected as committed or agreed.',
        'criteria': [
            ('C1', 'Confidentiality', 'The entity identifies and maintains confidential information to meet the entity\'s objectives related to confidentiality.', 'critical'),
        ]
    },
    'PI': {
        'principle': 'Additional Criteria for Privacy',
        'description': 'Personal information is collected, used, retained, disclosed, and disposed of to meet the entity\'s objectives.',
        'criteria': [
            ('PI1', 'Privacy Notice', 'The entity provides notice to data subjects about its privacy practices.', 'high'),
            ('PI2', 'Choice and Consent', 'The entity communicates choices available regarding the collection, use, retention, disclosure, and disposal of personal information.', 'high'),
            ('PI3', 'Collection', 'The entity collects personal information consistent with its privacy notice.', 'high'),
            ('PI4', 'Use and Retention', 'The entity uses and retains personal information consistent with its privacy notice and objectives.', 'critical'),
            ('PI5', 'Disclosure and Notification', 'The entity discloses personal information to third parties consistent with its privacy notice.', 'critical'),
            ('PI6', 'Quality', 'The entity maintains accurate, complete, and relevant personal information.', 'medium'),
            ('PI7', 'Monitoring and Enforcement', 'The entity monitors compliance with its privacy policies and procedures.', 'high'),
        ]
    }
}


def ingest_soc2(db_path: str):
    """Ingest SOC 2 Trust Services Criteria into the database."""
    
    logger.info(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get SOC2 framework ID
        cursor.execute("SELECT framework_id FROM frameworks WHERE framework_code = 'SOC2'")
        result = cursor.fetchone()
        if not result:
            logger.error("SOC2 framework not found in database")
            return False
        
        framework_id = result[0]
        logger.info(f"Found SOC2 framework (ID: {framework_id})")
        
        # Insert criteria
        total_criteria = 0
        for category_code, category_data in SOC2_CRITERIA.items():
            principle = category_data['principle']
            logger.info(f"Processing {category_code}: {principle}")
            
            for criterion_id, criterion_name, criterion_desc, priority in category_data['criteria']:
                full_id = f"SOC2-{criterion_id}"
                
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
                    full_id,
                    criterion_name,
                    criterion_desc,
                    criterion_desc,
                    category_code,
                    principle,
                    priority,
                    1 if category_code == 'CC' else 0  # Common Criteria are mandatory
                ))
                
                total_criteria += 1
        
        conn.commit()
        
        logger.info(f"✓ Ingested {total_criteria} SOC 2 criteria")
        
        # Verify
        cursor.execute('''
            SELECT COUNT(*) FROM framework_controls 
            WHERE framework_id = ?
        ''', (framework_id,))
        count = cursor.fetchone()[0]
        logger.info(f"✓ Verified {count} SOC 2 criteria in database")
        
        # Show principle distribution
        cursor.execute('''
            SELECT control_domain, COUNT(*) as cnt
            FROM framework_controls
            WHERE framework_id = ?
            GROUP BY control_domain
            ORDER BY control_domain
        ''', (framework_id,))
        
        logger.info("\n✓ Criteria distribution by principle:")
        for principle, cnt in cursor.fetchall():
            logger.info(f"  {principle}: {cnt} criteria")
        
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
        
        logger.info("\n✓ Criteria distribution by priority:")
        for priority, cnt in cursor.fetchall():
            logger.info(f"  {priority}: {cnt} criteria")
        
        # Show mandatory vs optional
        cursor.execute('''
            SELECT 
                CASE WHEN is_mandatory = 1 THEN 'Mandatory' ELSE 'Optional' END as status,
                COUNT(*) as cnt
            FROM framework_controls
            WHERE framework_id = ?
            GROUP BY is_mandatory
        ''', (framework_id,))
        
        logger.info("\n✓ Mandatory vs Optional:")
        for status, cnt in cursor.fetchall():
            logger.info(f"  {status}: {cnt} criteria")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error ingesting SOC 2: {e}")
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
    logger.info("SOC 2 TRUST SERVICES CRITERIA INGESTION")
    logger.info("=" * 70)
    
    success = ingest_soc2(str(db_path))
    
    if success:
        logger.info("\n" + "=" * 70)
        logger.info("✅ SOC 2 ingestion complete!")
        logger.info("=" * 70)
        return 0
    else:
        logger.info("\n" + "=" * 70)
        logger.info("⚠ SOC 2 ingestion failed")
        logger.info("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
