#!/usr/bin/env python3
"""
ISO 27001:2013 Controls Ingestion

Ingests ISO/IEC 27001:2013 Annex A controls into the multi-framework database.
ISO 27001 has 14 domains (A.5 - A.18) with 114 controls.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ISO 27001:2013 Annex A Controls
ISO_27001_CONTROLS = {
    'A.5': {
        'domain': 'Information Security Policies',
        'controls': [
            ('A.5.1.1', 'Policies for information security', 'To provide management direction and support for information security in accordance with business requirements and relevant laws and regulations.'),
            ('A.5.1.2', 'Review of the policies for information security', 'To ensure the policies for information security remain suitable, adequate and effective.')
        ]
    },
    'A.6': {
        'domain': 'Organization of Information Security',
        'controls': [
            ('A.6.1.1', 'Information security roles and responsibilities', 'To ensure that information security responsibilities are defined and allocated.'),
            ('A.6.1.2', 'Segregation of duties', 'To reduce opportunities for unauthorized or unintentional modification or misuse of organizational assets.'),
            ('A.6.1.3', 'Contact with authorities', 'To maintain appropriate contacts with relevant authorities.'),
            ('A.6.1.4', 'Contact with special interest groups', 'To maintain appropriate contacts with special interest groups or other specialist security forums.'),
            ('A.6.1.5', 'Information security in project management', 'To address information security in project management.'),
            ('A.6.2.1', 'Mobile device policy', 'To ensure the security of teleworking and use of mobile devices.'),
            ('A.6.2.2', 'Teleworking', 'To protect information accessed, processed or stored at teleworking sites.')
        ]
    },
    'A.7': {
        'domain': 'Human Resource Security',
        'controls': [
            ('A.7.1.1', 'Screening', 'To ensure that employees and contractors understand their responsibilities and are suitable for the roles for which they are considered.'),
            ('A.7.1.2', 'Terms and conditions of employment', 'To ensure that employees and contractors are aware of and fulfill their information security responsibilities.'),
            ('A.7.2.1', 'Management responsibilities', 'To ensure that employees and contractors are aware of and fulfill their information security responsibilities.'),
            ('A.7.2.2', 'Information security awareness, education and training', 'To ensure that employees and contractors receive appropriate awareness education and training.'),
            ('A.7.2.3', 'Disciplinary process', 'To ensure there is a formal and communicated disciplinary process in place.'),
            ('A.7.3.1', 'Termination or change of employment responsibilities', 'To protect the organization\'s interests as part of the process of changing or terminating employment.')
        ]
    },
    'A.8': {
        'domain': 'Asset Management',
        'controls': [
            ('A.8.1.1', 'Inventory of assets', 'To identify organizational assets and define appropriate protection responsibilities.'),
            ('A.8.1.2', 'Ownership of assets', 'To identify, document and implement rules for the acceptable use of information and assets.'),
            ('A.8.1.3', 'Acceptable use of assets', 'To prevent unauthorized disclosure, modification, removal or destruction of information.'),
            ('A.8.1.4', 'Return of assets', 'To ensure that employees and external party users return all organizational assets in their possession.'),
            ('A.8.2.1', 'Classification of information', 'To ensure information receives an appropriate level of protection.'),
            ('A.8.2.2', 'Labeling of information', 'To ensure an appropriate set of procedures for information labeling.'),
            ('A.8.2.3', 'Handling of assets', 'To develop and implement procedures for handling assets in accordance with the classification scheme.'),
            ('A.8.3.1', 'Management of removable media', 'To prevent unauthorized disclosure, modification, removal or destruction of information stored on media.'),
            ('A.8.3.2', 'Disposal of media', 'To prevent unauthorized disclosure or re-use of information.'),
            ('A.8.3.3', 'Physical media transfer', 'To protect media containing information against unauthorized access, misuse or corruption during transportation.')
        ]
    },
    'A.9': {
        'domain': 'Access Control',
        'controls': [
            ('A.9.1.1', 'Access control policy', 'To limit access to information and information processing facilities.'),
            ('A.9.1.2', 'Access to networks and network services', 'To provide access to networks and network services only for authorized users.'),
            ('A.9.2.1', 'User registration and de-registration', 'To ensure authorized user access and to prevent unauthorized access.'),
            ('A.9.2.2', 'User access provisioning', 'To assign user access rights to networks and network services.'),
            ('A.9.2.3', 'Management of privileged access rights', 'To restrict and control the allocation and use of privileged access rights.'),
            ('A.9.2.4', 'Management of secret authentication information of users', 'To ensure allocation of secret authentication information is controlled through a formal management process.'),
            ('A.9.2.5', 'Review of user access rights', 'To maintain authorized access and prevent unauthorized access.'),
            ('A.9.2.6', 'Removal or adjustment of access rights', 'To remove or adjust access rights of all employees and external party users upon termination.'),
            ('A.9.3.1', 'Use of secret authentication information', 'To protect secret authentication information from unauthorized use.'),
            ('A.9.4.1', 'Information access restriction', 'To restrict access to information based on business needs.'),
            ('A.9.4.2', 'Secure log-on procedures', 'To control access to operating systems by a secure log-on procedure.'),
            ('A.9.4.3', 'Password management system', 'To ensure password quality and proper management.'),
            ('A.9.4.4', 'Use of privileged utility programs', 'To restrict and tightly control the use of utility programs.'),
            ('A.9.4.5', 'Access control to program source code', 'To prevent unauthorized access to program source code.')
        ]
    },
    'A.10': {
        'domain': 'Cryptography',
        'controls': [
            ('A.10.1.1', 'Policy on the use of cryptographic controls', 'To ensure proper and effective use of cryptography to protect information confidentiality, authenticity and/or integrity.'),
            ('A.10.1.2', 'Key management', 'To ensure proper and effective use of cryptography through key lifecycle management.')
        ]
    },
    'A.11': {
        'domain': 'Physical and Environmental Security',
        'controls': [
            ('A.11.1.1', 'Physical security perimeter', 'To prevent unauthorized physical access, damage and interference to information and information processing facilities.'),
            ('A.11.1.2', 'Physical entry controls', 'To ensure only authorized personnel are allowed access to secure areas.'),
            ('A.11.1.3', 'Securing offices, rooms and facilities', 'To design and apply physical security for offices, rooms and facilities.'),
            ('A.11.1.4', 'Protecting against external and environmental threats', 'To design physical protection against natural disasters, malicious attack or accidents.'),
            ('A.11.1.5', 'Working in secure areas', 'To establish procedures for working in secure areas.'),
            ('A.11.1.6', 'Delivery and loading areas', 'To control access points to prevent unauthorized access to information and information processing facilities.'),
            ('A.11.2.1', 'Equipment siting and protection', 'To reduce risk from environmental threats, hazards and opportunities for unauthorized access.'),
            ('A.11.2.2', 'Supporting utilities', 'To protect equipment from power failures and other disruptions.'),
            ('A.11.2.3', 'Cabling security', 'To protect cables carrying data or supporting information services from interception, interference or damage.'),
            ('A.11.2.4', 'Equipment maintenance', 'To ensure availability and integrity of equipment.'),
            ('A.11.2.5', 'Removal of assets', 'To prevent theft, misuse or unauthorized removal of assets.'),
            ('A.11.2.6', 'Security of equipment and assets off-premises', 'To ensure security of assets used off-premises.'),
            ('A.11.2.7', 'Secure disposal or re-use of equipment', 'To prevent information leakage from equipment to be disposed of or re-used.'),
            ('A.11.2.8', 'Unattended user equipment', 'To ensure appropriate protection for unattended equipment.'),
            ('A.11.2.9', 'Clear desk and clear screen policy', 'To reduce risk of unauthorized access, loss of, and damage to information during and outside normal working hours.')
        ]
    },
    'A.12': {
        'domain': 'Operations Security',
        'controls': [
            ('A.12.1.1', 'Documented operating procedures', 'To ensure correct and secure operations of information processing facilities.'),
            ('A.12.1.2', 'Change management', 'To ensure secure changes to information processing facilities and systems.'),
            ('A.12.1.3', 'Capacity management', 'To ensure system performance meets requirements.'),
            ('A.12.1.4', 'Separation of development, testing and operational environments', 'To reduce risks from unauthorized access or changes to the operational environment.'),
            ('A.12.2.1', 'Controls against malware', 'To ensure information and information processing facilities are protected against malware.'),
            ('A.12.3.1', 'Information backup', 'To protect against loss of data.'),
            ('A.12.4.1', 'Event logging', 'To record events and generate evidence.'),
            ('A.12.4.2', 'Protection of log information', 'To protect log information against tampering and unauthorized access.'),
            ('A.12.4.3', 'Administrator and operator logs', 'To record system administrator and operator activities.'),
            ('A.12.4.4', 'Clock synchronization', 'To ensure accuracy of audit trails.'),
            ('A.12.5.1', 'Installation of software on operational systems', 'To control installation of software on operational systems.'),
            ('A.12.6.1', 'Management of technical vulnerabilities', 'To prevent exploitation of technical vulnerabilities.'),
            ('A.12.6.2', 'Restrictions on software installation', 'To control user-installed software.'),
            ('A.12.7.1', 'Information systems audit controls', 'To minimize impact of audit activities on operational systems.')
        ]
    },
    'A.13': {
        'domain': 'Communications Security',
        'controls': [
            ('A.13.1.1', 'Network controls', 'To ensure protection of information in networks.'),
            ('A.13.1.2', 'Security of network services', 'To maintain security of network services.'),
            ('A.13.1.3', 'Segregation in networks', 'To segregate information services, users and information systems.'),
            ('A.13.2.1', 'Information transfer policies and procedures', 'To protect information transferred within and outside the organization.'),
            ('A.13.2.2', 'Agreements on information transfer', 'To maintain security of information transferred to external parties.'),
            ('A.13.2.3', 'Electronic messaging', 'To protect information involved in electronic messaging.'),
            ('A.13.2.4', 'Confidentiality or non-disclosure agreements', 'To protect confidential information.')
        ]
    },
    'A.14': {
        'domain': 'System Acquisition, Development and Maintenance',
        'controls': [
            ('A.14.1.1', 'Information security requirements analysis and specification', 'To ensure information security is included in new information systems or enhancements.'),
            ('A.14.1.2', 'Securing application services on public networks', 'To protect information involved in application services over public networks.'),
            ('A.14.1.3', 'Protecting application services transactions', 'To prevent incomplete transmission, mis-routing, unauthorized message alteration, disclosure, duplication or replay.'),
            ('A.14.2.1', 'Secure development policy', 'To establish rules for development of software and systems.'),
            ('A.14.2.2', 'System change control procedures', 'To ensure security is maintained during the system development lifecycle.'),
            ('A.14.2.3', 'Technical review of applications after operating platform changes', 'To ensure no adverse impact on organizational operations or security.'),
            ('A.14.2.4', 'Restrictions on changes to software packages', 'To prevent modification of software packages.'),
            ('A.14.2.5', 'Secure system engineering principles', 'To establish and apply secure system engineering principles.'),
            ('A.14.2.6', 'Secure development environment', 'To establish a secure development environment.'),
            ('A.14.2.7', 'Outsourced development', 'To ensure security of outsourced system development.'),
            ('A.14.2.8', 'System security testing', 'To ensure security functionality works correctly.'),
            ('A.14.2.9', 'System acceptance testing', 'To ensure new information systems meet acceptance criteria.'),
            ('A.14.3.1', 'Protection of test data', 'To ensure test data is protected.')
        ]
    },
    'A.15': {
        'domain': 'Supplier Relationships',
        'controls': [
            ('A.15.1.1', 'Information security policy for supplier relationships', 'To ensure protection of organizational assets accessible by suppliers.'),
            ('A.15.1.2', 'Addressing security within supplier agreements', 'To establish and agree security requirements with suppliers.'),
            ('A.15.1.3', 'Information and communication technology supply chain', 'To ensure security of ICT supply chain.'),
            ('A.15.2.1', 'Monitoring and review of supplier services', 'To maintain agreed level of information security in supplier service delivery.'),
            ('A.15.2.2', 'Managing changes to supplier services', 'To manage changes in supplier service provision.')
        ]
    },
    'A.16': {
        'domain': 'Information Security Incident Management',
        'controls': [
            ('A.16.1.1', 'Responsibilities and procedures', 'To ensure consistent and effective approach to information security incident management.'),
            ('A.16.1.2', 'Reporting information security events', 'To ensure information security events are reported timely.'),
            ('A.16.1.3', 'Reporting information security weaknesses', 'To ensure employees and contractors report observed or suspected security weaknesses.'),
            ('A.16.1.4', 'Assessment of and decision on information security events', 'To assess information security events and decide if they are security incidents.'),
            ('A.16.1.5', 'Response to information security incidents', 'To respond to information security incidents in accordance with documented procedures.'),
            ('A.16.1.6', 'Learning from information security incidents', 'To ensure knowledge from security incidents is used to strengthen security.'),
            ('A.16.1.7', 'Collection of evidence', 'To define procedures for identification, collection, acquisition and preservation of evidence.')
        ]
    },
    'A.17': {
        'domain': 'Information Security Aspects of Business Continuity Management',
        'controls': [
            ('A.17.1.1', 'Planning information security continuity', 'To plan information security continuity requirements.'),
            ('A.17.1.2', 'Implementing information security continuity', 'To establish, document and implement processes and technical measures for business continuity.'),
            ('A.17.1.3', 'Verify, review and evaluate information security continuity', 'To verify established controls remain effective.'),
            ('A.17.2.1', 'Availability of information processing facilities', 'To ensure availability of information processing facilities.')
        ]
    },
    'A.18': {
        'domain': 'Compliance',
        'controls': [
            ('A.18.1.1', 'Identification of applicable legislation and contractual requirements', 'To avoid breaches of legal, statutory, regulatory or contractual obligations.'),
            ('A.18.1.2', 'Intellectual property rights', 'To ensure compliance with legal and contractual requirements related to intellectual property.'),
            ('A.18.1.3', 'Protection of records', 'To protect records from loss, destruction, falsification and unauthorized access.'),
            ('A.18.1.4', 'Privacy and protection of personally identifiable information', 'To ensure privacy and protection of PII as required by law.'),
            ('A.18.1.5', 'Regulation of cryptographic controls', 'To ensure compliance with relevant agreements, legislation and regulations.'),
            ('A.18.2.1', 'Independent review of information security', 'To ensure effectiveness of implementation and operation of ISMS.'),
            ('A.18.2.2', 'Compliance with security policies and standards', 'To ensure compliance with organizational security policies and standards.'),
            ('A.18.2.3', 'Technical compliance review', 'To ensure systems comply with organizational security policies and standards.')
        ]
    }
}


def ingest_iso27001_controls(db_path: str):
    """Ingest ISO 27001 controls into the database."""
    
    logger.info(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get ISO 27001 framework ID
        cursor.execute("SELECT framework_id FROM frameworks WHERE framework_code = 'ISO-27001'")
        result = cursor.fetchone()
        if not result:
            logger.error("ISO-27001 framework not found in database")
            return False
        
        framework_id = result[0]
        logger.info(f"Found ISO-27001 framework (ID: {framework_id})")
        
        # Insert controls
        total_controls = 0
        for domain_code, domain_data in ISO_27001_CONTROLS.items():
            domain_name = domain_data['domain']
            logger.info(f"Processing domain {domain_code}: {domain_name}")
            
            for control_id, control_name, control_objective in domain_data['controls']:
                # Determine priority based on domain
                if domain_code in ['A.9', 'A.10', 'A.12', 'A.13']:  # Access, Crypto, Ops, Comms
                    priority = 'critical'
                elif domain_code in ['A.6', 'A.8', 'A.14', 'A.16']:  # Org, Assets, Dev, Incidents
                    priority = 'high'
                elif domain_code in ['A.7', 'A.11', 'A.15', 'A.17']:  # HR, Physical, Suppliers, BC
                    priority = 'medium'
                else:  # A.5, A.18 - Policies, Compliance
                    priority = 'low'
                
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
                    control_name,
                    control_objective,  # Use objective as description
                    control_objective,
                    domain_code,
                    domain_name,
                    priority,
                    1  # All ISO 27001 Annex A controls are mandatory
                ))
                
                total_controls += 1
        
        conn.commit()
        
        logger.info(f"✓ Ingested {total_controls} ISO 27001 controls")
        
        # Verify
        cursor.execute('''
            SELECT COUNT(*) FROM framework_controls 
            WHERE framework_id = ?
        ''', (framework_id,))
        count = cursor.fetchone()[0]
        logger.info(f"✓ Verified {count} ISO 27001 controls in database")
        
        # Show domain distribution
        cursor.execute('''
            SELECT control_category, COUNT(*) as cnt
            FROM framework_controls
            WHERE framework_id = ?
            GROUP BY control_category
            ORDER BY control_category
        ''', (framework_id,))
        
        logger.info("\n✓ Control distribution by domain:")
        for domain, cnt in cursor.fetchall():
            logger.info(f"  {domain}: {cnt} controls")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error ingesting ISO 27001 controls: {e}")
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
    logger.info("ISO 27001:2013 CONTROLS INGESTION")
    logger.info("=" * 70)
    
    success = ingest_iso27001_controls(str(db_path))
    
    if success:
        logger.info("\n" + "=" * 70)
        logger.info("✅ ISO 27001 ingestion complete!")
        logger.info("=" * 70)
        return 0
    else:
        logger.info("\n" + "=" * 70)
        logger.info("⚠ ISO 27001 ingestion failed")
        logger.info("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
