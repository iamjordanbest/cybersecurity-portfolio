#!/usr/bin/env python3
"""
Create Cross-Framework Control Mappings

Populates the control_mappings table with industry-standard mappings
between different compliance frameworks.

Based on:
- NIST IR 8011: NIST to ISO 27001 mappings
- CIS Controls to NIST CSF mappings
- Industry best practices
"""

import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analytics.framework_mapper import FrameworkMapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# NIST 800-53 to ISO 27001 Mappings (Sample - Key Controls)
NIST_TO_ISO_MAPPINGS = [
    # Access Control Family
    ('AC-1', 'A.9.1.1', 'RELATED', 0.85, 'Access control policy'),
    ('AC-2', 'A.9.2.1', 'EXACT', 0.95, 'User registration and de-registration'),
    ('AC-2', 'A.9.2.2', 'RELATED', 0.90, 'User access provisioning'),
    ('AC-3', 'A.9.4.1', 'RELATED', 0.85, 'Information access restriction'),
    ('AC-6', 'A.9.2.3', 'RELATED', 0.90, 'Management of privileged access rights'),
    ('AC-7', 'A.9.4.2', 'RELATED', 0.85, 'Secure log-on procedures'),
    ('AC-17', 'A.6.2.1', 'RELATED', 0.80, 'Mobile device and teleworking policy'),
    ('AC-18', 'A.6.2.1', 'RELATED', 0.80, 'Wireless access control'),
    ('AC-19', 'A.6.2.1', 'RELATED', 0.85, 'Access control for mobile devices'),
    ('AC-20', 'A.6.2.2', 'RELATED', 0.80, 'Use of external information systems'),
    
    # Awareness and Training
    ('AT-1', 'A.7.2.2', 'RELATED', 0.85, 'Information security awareness, education and training'),
    ('AT-2', 'A.7.2.2', 'EXACT', 0.95, 'Security awareness training'),
    ('AT-3', 'A.7.2.2', 'RELATED', 0.90, 'Role-based security training'),
    
    # Audit and Accountability
    ('AU-1', 'A.12.4.1', 'RELATED', 0.85, 'Event logging policy'),
    ('AU-2', 'A.12.4.1', 'EXACT', 0.95, 'Auditable events'),
    ('AU-3', 'A.12.4.1', 'RELATED', 0.90, 'Content of audit records'),
    ('AU-6', 'A.12.4.1', 'RELATED', 0.85, 'Audit review, analysis, and reporting'),
    ('AU-9', 'A.12.4.2', 'EXACT', 0.95, 'Protection of audit information'),
    ('AU-11', 'A.12.4.3', 'RELATED', 0.90, 'Audit record retention'),
    ('AU-12', 'A.12.4.4', 'RELATED', 0.85, 'Audit generation'),
    
    # Security Assessment and Authorization
    ('CA-1', 'A.18.2.1', 'RELATED', 0.80, 'Security assessment policy'),
    ('CA-2', 'A.18.2.1', 'RELATED', 0.85, 'Security assessments'),
    ('CA-7', 'A.18.2.2', 'RELATED', 0.85, 'Continuous monitoring'),
    
    # Configuration Management
    ('CM-1', 'A.12.1.2', 'RELATED', 0.85, 'Configuration management policy'),
    ('CM-2', 'A.12.1.2', 'EXACT', 0.95, 'Baseline configuration'),
    ('CM-3', 'A.12.1.2', 'EXACT', 0.95, 'Configuration change control'),
    ('CM-6', 'A.12.6.1', 'RELATED', 0.90, 'Configuration settings'),
    ('CM-7', 'A.12.6.2', 'RELATED', 0.85, 'Least functionality'),
    ('CM-8', 'A.8.1.1', 'EXACT', 0.95, 'Information system component inventory'),
    
    # Contingency Planning
    ('CP-1', 'A.17.1.1', 'RELATED', 0.85, 'Contingency planning policy'),
    ('CP-2', 'A.17.1.1', 'EXACT', 0.95, 'Contingency plan'),
    ('CP-3', 'A.17.1.3', 'RELATED', 0.90, 'Contingency training'),
    ('CP-4', 'A.17.1.3', 'RELATED', 0.90, 'Contingency plan testing'),
    ('CP-9', 'A.12.3.1', 'EXACT', 0.95, 'Information system backup'),
    ('CP-10', 'A.17.1.2', 'RELATED', 0.90, 'Information system recovery and reconstitution'),
    
    # Identification and Authentication
    ('IA-1', 'A.9.2.1', 'RELATED', 0.85, 'Identification and authentication policy'),
    ('IA-2', 'A.9.2.1', 'EXACT', 0.95, 'User identification and authentication'),
    ('IA-4', 'A.9.2.1', 'RELATED', 0.90, 'Identifier management'),
    ('IA-5', 'A.9.2.4', 'EXACT', 0.95, 'Authenticator management'),
    ('IA-8', 'A.9.2.1', 'RELATED', 0.85, 'Identification and authentication for non-organizational users'),
    
    # Incident Response
    ('IR-1', 'A.16.1.1', 'RELATED', 0.85, 'Incident response policy'),
    ('IR-2', 'A.16.1.1', 'EXACT', 0.95, 'Incident response training'),
    ('IR-4', 'A.16.1.5', 'EXACT', 0.95, 'Incident handling'),
    ('IR-5', 'A.16.1.4', 'RELATED', 0.90, 'Incident monitoring'),
    ('IR-6', 'A.16.1.2', 'EXACT', 0.95, 'Incident reporting'),
    ('IR-7', 'A.16.1.5', 'RELATED', 0.90, 'Incident response assistance'),
    ('IR-8', 'A.16.1.6', 'RELATED', 0.85, 'Incident response plan'),
    
    # Maintenance
    ('MA-2', 'A.11.2.4', 'RELATED', 0.85, 'Controlled maintenance'),
    ('MA-4', 'A.11.2.4', 'RELATED', 0.80, 'Nonlocal maintenance'),
    ('MA-5', 'A.11.2.7', 'RELATED', 0.85, 'Maintenance personnel'),
    
    # Media Protection
    ('MP-1', 'A.8.3.1', 'RELATED', 0.85, 'Media protection policy'),
    ('MP-2', 'A.8.3.1', 'EXACT', 0.95, 'Media access'),
    ('MP-6', 'A.8.3.2', 'EXACT', 0.95, 'Media sanitization'),
    ('MP-7', 'A.8.3.3', 'RELATED', 0.90, 'Media use'),
    
    # Physical and Environmental Protection
    ('PE-1', 'A.11.1.1', 'RELATED', 0.85, 'Physical and environmental protection policy'),
    ('PE-2', 'A.11.1.1', 'EXACT', 0.95, 'Physical access authorizations'),
    ('PE-3', 'A.11.1.2', 'EXACT', 0.95, 'Physical access control'),
    ('PE-6', 'A.11.1.3', 'RELATED', 0.90, 'Monitoring physical access'),
    ('PE-8', 'A.11.1.4', 'RELATED', 0.85, 'Visitor access records'),
    
    # Planning
    ('PL-1', 'A.5.1.1', 'RELATED', 0.80, 'Security planning policy'),
    ('PL-2', 'A.5.1.1', 'RELATED', 0.85, 'System security plan'),
    
    # Risk Assessment
    ('RA-1', 'A.12.6.1', 'RELATED', 0.85, 'Risk assessment policy'),
    ('RA-2', 'A.12.6.1', 'RELATED', 0.85, 'Security categorization'),
    ('RA-3', 'A.12.6.1', 'EXACT', 0.95, 'Risk assessment'),
    ('RA-5', 'A.12.6.1', 'EXACT', 0.95, 'Vulnerability scanning'),
    
    # System and Services Acquisition
    ('SA-1', 'A.14.1.1', 'RELATED', 0.80, 'System and services acquisition policy'),
    ('SA-2', 'A.14.1.1', 'RELATED', 0.85, 'Allocation of resources'),
    ('SA-3', 'A.14.1.1', 'RELATED', 0.85, 'System development life cycle'),
    ('SA-4', 'A.14.1.2', 'RELATED', 0.85, 'Acquisition process'),
    ('SA-8', 'A.14.2.5', 'RELATED', 0.85, 'Security engineering principles'),
    ('SA-9', 'A.15.1.1', 'RELATED', 0.85, 'External information system services'),
    ('SA-11', 'A.14.2.8', 'RELATED', 0.85, 'Developer security testing'),
    
    # System and Communications Protection
    ('SC-1', 'A.13.1.1', 'RELATED', 0.80, 'System and communications protection policy'),
    ('SC-5', 'A.13.1.1', 'RELATED', 0.80, 'Denial of service protection'),
    ('SC-7', 'A.13.1.3', 'RELATED', 0.90, 'Boundary protection'),
    ('SC-8', 'A.13.2.3', 'EXACT', 0.95, 'Transmission confidentiality and integrity'),
    ('SC-12', 'A.10.1.1', 'RELATED', 0.85, 'Cryptographic key establishment and management'),
    ('SC-13', 'A.10.1.1', 'EXACT', 0.95, 'Cryptographic protection'),
    ('SC-17', 'A.13.2.1', 'RELATED', 0.85, 'Public key infrastructure certificates'),
    ('SC-28', 'A.10.1.1', 'RELATED', 0.90, 'Protection of information at rest'),
    
    # System and Information Integrity
    ('SI-1', 'A.12.2.1', 'RELATED', 0.80, 'System and information integrity policy'),
    ('SI-2', 'A.12.6.1', 'EXACT', 0.95, 'Flaw remediation'),
    ('SI-3', 'A.12.2.1', 'EXACT', 0.95, 'Malicious code protection'),
    ('SI-4', 'A.12.4.1', 'RELATED', 0.85, 'Information system monitoring'),
    ('SI-5', 'A.12.6.1', 'RELATED', 0.90, 'Security alerts, advisories, and directives'),
    ('SI-7', 'A.12.2.1', 'RELATED', 0.85, 'Software, firmware, and information integrity'),
]


# CIS Controls to NIST 800-53 Mappings (Key mappings)
CIS_TO_NIST_MAPPINGS = [
    ('CIS-1', 'CM-8', 'EXACT', 0.95, 'Asset inventory'),
    ('CIS-1', 'IA-4', 'RELATED', 0.80, 'Asset identification'),
    ('CIS-2', 'CM-8', 'RELATED', 0.90, 'Software asset inventory'),
    ('CIS-2', 'CM-7', 'RELATED', 0.85, 'Least functionality - unauthorized software'),
    ('CIS-3', 'MP-2', 'RELATED', 0.85, 'Data protection'),
    ('CIS-3', 'SC-28', 'RELATED', 0.90, 'Data protection at rest'),
    ('CIS-4', 'CM-2', 'EXACT', 0.95, 'Secure configuration'),
    ('CIS-4', 'CM-6', 'EXACT', 0.95, 'Configuration settings'),
    ('CIS-5', 'IA-2', 'RELATED', 0.90, 'Account management'),
    ('CIS-5', 'AC-2', 'EXACT', 0.95, 'Account management'),
    ('CIS-6', 'AC-3', 'RELATED', 0.90, 'Access control management'),
    ('CIS-6', 'AC-6', 'EXACT', 0.95, 'Least privilege'),
    ('CIS-7', 'RA-5', 'EXACT', 0.95, 'Vulnerability management'),
    ('CIS-7', 'SI-2', 'EXACT', 0.95, 'Flaw remediation'),
    ('CIS-8', 'AU-2', 'EXACT', 0.95, 'Audit log management'),
    ('CIS-8', 'AU-6', 'RELATED', 0.90, 'Audit review'),
    ('CIS-9', 'SC-7', 'RELATED', 0.85, 'Email and web browser protections'),
    ('CIS-10', 'SI-3', 'EXACT', 0.95, 'Malware defenses'),
    ('CIS-11', 'CP-9', 'EXACT', 0.95, 'Data recovery'),
    ('CIS-11', 'CP-10', 'RELATED', 0.90, 'System recovery'),
    ('CIS-12', 'SC-7', 'EXACT', 0.95, 'Network infrastructure management'),
    ('CIS-13', 'SI-4', 'EXACT', 0.95, 'Network monitoring and defense'),
    ('CIS-14', 'AT-2', 'EXACT', 0.95, 'Security awareness training'),
    ('CIS-15', 'SA-9', 'RELATED', 0.85, 'Service provider management'),
    ('CIS-16', 'SA-11', 'RELATED', 0.85, 'Application software security'),
    ('CIS-16', 'SA-8', 'RELATED', 0.80, 'Security engineering principles'),
    ('CIS-17', 'IR-4', 'EXACT', 0.95, 'Incident response management'),
    ('CIS-17', 'IR-8', 'RELATED', 0.90, 'Incident response plan'),
    ('CIS-18', 'CA-2', 'RELATED', 0.85, 'Penetration testing'),
    ('CIS-18', 'CA-8', 'RELATED', 0.85, 'Penetration testing'),
]


# PCI-DSS to NIST 800-53 Mappings (Key mappings)
PCI_TO_NIST_MAPPINGS = [
    ('PCI-DSS-1', 'SC-7', 'EXACT', 0.95, 'Network security controls (firewalls)'),
    ('PCI-DSS-1', 'AC-4', 'RELATED', 0.85, 'Information flow enforcement'),
    ('PCI-DSS-2', 'CM-2', 'EXACT', 0.95, 'Secure configurations'),
    ('PCI-DSS-2', 'CM-6', 'EXACT', 0.95, 'Configuration settings'),
    ('PCI-DSS-3', 'SC-28', 'EXACT', 0.95, 'Protection of stored cardholder data'),
    ('PCI-DSS-3', 'MP-2', 'RELATED', 0.85, 'Media protection'),
    ('PCI-DSS-4', 'SC-8', 'EXACT', 0.95, 'Transmission protection with cryptography'),
    ('PCI-DSS-4', 'SC-13', 'EXACT', 0.95, 'Cryptographic protection'),
    ('PCI-DSS-5', 'SI-3', 'EXACT', 0.95, 'Malware protection'),
    ('PCI-DSS-6', 'SI-2', 'EXACT', 0.95, 'Secure systems and software'),
    ('PCI-DSS-6', 'RA-5', 'RELATED', 0.90, 'Vulnerability management'),
    ('PCI-DSS-7', 'AC-3', 'EXACT', 0.95, 'Restrict access by need to know'),
    ('PCI-DSS-7', 'AC-6', 'EXACT', 0.95, 'Least privilege'),
    ('PCI-DSS-8', 'IA-2', 'EXACT', 0.95, 'Identify and authenticate users'),
    ('PCI-DSS-8', 'IA-5', 'EXACT', 0.95, 'Authenticator management'),
    ('PCI-DSS-9', 'PE-2', 'EXACT', 0.95, 'Physical access restrictions'),
    ('PCI-DSS-9', 'PE-3', 'EXACT', 0.95, 'Physical access control'),
    ('PCI-DSS-10', 'AU-2', 'EXACT', 0.95, 'Logging and monitoring'),
    ('PCI-DSS-10', 'AU-6', 'EXACT', 0.95, 'Audit review'),
    ('PCI-DSS-11', 'CA-2', 'RELATED', 0.90, 'Security testing'),
    ('PCI-DSS-11', 'RA-5', 'EXACT', 0.95, 'Vulnerability scanning'),
    ('PCI-DSS-12', 'PL-1', 'RELATED', 0.85, 'Information security policies'),
    ('PCI-DSS-12', 'AT-2', 'RELATED', 0.85, 'Security awareness'),
]


def create_all_mappings():
    """Create all cross-framework mappings."""
    db_path = Path(__file__).parent.parent / 'data' / 'processed' / 'grc_analytics.db'
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return False
    
    logger.info("=" * 70)
    logger.info("CREATING CROSS-FRAMEWORK MAPPINGS")
    logger.info("=" * 70)
    
    with FrameworkMapper(str(db_path)) as mapper:
        total_created = 0
        
        # Create NIST to ISO mappings
        logger.info(f"\nCreating NIST 800-53 → ISO 27001 mappings...")
        for source, target, mtype, strength, rationale in NIST_TO_ISO_MAPPINGS:
            if mapper.add_mapping('NIST-800-53', source, 'ISO-27001', target, 
                                 mtype, strength, rationale):
                total_created += 1
        
        logger.info(f"✓ Created {len(NIST_TO_ISO_MAPPINGS)} NIST → ISO mappings")
        
        # Create CIS to NIST mappings
        logger.info(f"\nCreating CIS Controls → NIST 800-53 mappings...")
        for source, target, mtype, strength, rationale in CIS_TO_NIST_MAPPINGS:
            if mapper.add_mapping('CIS', source, 'NIST-800-53', target,
                                 mtype, strength, rationale):
                total_created += 1
        
        logger.info(f"✓ Created {len(CIS_TO_NIST_MAPPINGS)} CIS → NIST mappings")
        
        # Create PCI-DSS to NIST mappings
        logger.info(f"\nCreating PCI-DSS → NIST 800-53 mappings...")
        for source, target, mtype, strength, rationale in PCI_TO_NIST_MAPPINGS:
            if mapper.add_mapping('PCI-DSS', source, 'NIST-800-53', target,
                                 mtype, strength, rationale):
                total_created += 1
        
        logger.info(f"✓ Created {len(PCI_TO_NIST_MAPPINGS)} PCI-DSS → NIST mappings")
        
        # Show statistics
        logger.info("\n" + "=" * 70)
        logger.info("MAPPING STATISTICS")
        logger.info("=" * 70)
        
        stats = mapper.get_mapping_statistics()
        logger.info(f"\nTotal Mappings Created: {stats['total_mappings']}")
        
        logger.info(f"\nBy Mapping Type:")
        for mtype, count in stats['by_type'].items():
            logger.info(f"  {mtype:15} : {count:4} mappings")
        
        logger.info(f"\nBy Framework Pair:")
        for source, target, count in stats['by_framework_pair']:
            logger.info(f"  {source:15} → {target:15} : {count:4} mappings")
        
        logger.info(f"\nAverage Mapping Strength: {stats['average_strength']:.3f}")
        
        # Show coverage for key pairs
        logger.info("\n" + "=" * 70)
        logger.info("FRAMEWORK COVERAGE")
        logger.info("=" * 70)
        
        coverage_pairs = [
            ('NIST-800-53', 'ISO-27001'),
            ('CIS', 'NIST-800-53'),
            ('PCI-DSS', 'NIST-800-53'),
        ]
        
        for source, target in coverage_pairs:
            cov = mapper.get_framework_coverage(source, target)
            logger.info(f"\n{source} → {target}:")
            logger.info(f"  Source coverage: {cov['source_coverage_pct']}% "
                       f"({cov['source_mapped_controls']}/{cov['source_total_controls']})")
            logger.info(f"  Target coverage: {cov['target_coverage_pct']}% "
                       f"({cov['target_mapped_controls']}/{cov['target_total_controls']})")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ MAPPING CREATION COMPLETE")
        logger.info("=" * 70)
        
        return True


def main():
    """Main function."""
    success = create_all_mappings()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
