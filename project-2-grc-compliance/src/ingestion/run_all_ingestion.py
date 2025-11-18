#!/usr/bin/env python3
"""
Master Ingestion Orchestrator

This script runs all ingestion scripts in the correct order to populate
the GRC Analytics database with data from all sources.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_script(script_path: Path, script_name: str) -> bool:
    """
    Run a Python script and return success status.
    
    Args:
        script_path: Path to the script
        script_name: Name of the script for logging
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("\n" + "=" * 70)
    logger.info(f"Running: {script_name}")
    logger.info("=" * 70)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info(f"✓ {script_name} completed successfully")
            return True
        else:
            logger.error(f"✗ {script_name} failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error running {script_name}: {e}")
        return False


def check_database_exists(db_path: Path) -> bool:
    """Check if the database file exists."""
    return db_path.exists()


def check_data_files(project_root: Path) -> dict:
    """
    Check which data files are available.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with data file availability
    """
    data_files = {
        'cisa_kev': project_root / 'data' / 'raw' / 'cisa_kev' / 'known_exploited_vulnerabilities.json',
        'nvd_cves': project_root / 'data' / 'raw' / 'nist_nvd' / 'nvd_recent_cves.json',
        'nist_controls': project_root / 'data' / 'raw' / 'nist_oscal' / 'oscal-content' / 'nist.gov' / 'SP800-53' / 'rev5' / 'json' / 'NIST_SP-800-53_rev5_catalog.json',
        'mitre_attack': project_root / 'data' / 'raw' / 'mitre_attack' / 'cti' / 'enterprise-attack' / 'enterprise-attack.json'
    }
    
    availability = {}
    for name, path in data_files.items():
        availability[name] = path.exists()
        status = "✓ Available" if availability[name] else "✗ Not found"
        logger.info(f"{name}: {status}")
    
    return availability


def main():
    """Main execution function."""
    start_time = datetime.now()
    
    logger.info("\n" + "=" * 70)
    logger.info("GRC ANALYTICS PLATFORM - MASTER INGESTION ORCHESTRATOR")
    logger.info("=" * 70)
    logger.info(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    ingestion_dir = project_root / 'src' / 'ingestion'
    db_file = project_root / 'data' / 'processed' / 'grc_analytics.db'
    
    # Check database
    logger.info("\n" + "-" * 70)
    logger.info("Database Check:")
    logger.info("-" * 70)
    if check_database_exists(db_file):
        logger.info(f"✓ Database exists: {db_file}")
    else:
        logger.warning(f"⚠ Database not found: {db_file}")
        logger.info("Please run the database schema creation script first.")
        logger.info("Example: sqlite3 grc_analytics.db < scripts/create_enhanced_schema.sql")
    
    # Check data files
    logger.info("\n" + "-" * 70)
    logger.info("Data Files Check:")
    logger.info("-" * 70)
    availability = check_data_files(project_root)
    
    # Define ingestion sequence
    ingestion_steps = [
        {
            'name': 'NIST 800-53 Controls',
            'script': ingestion_dir / 'ingest_nist_controls.py',
            'required': True,
            'data_key': 'nist_controls'
        },
        {
            'name': 'CISA KEV (Known Exploited Vulnerabilities)',
            'script': ingestion_dir / 'ingest_cisa_kev.py',
            'required': False,
            'data_key': 'cisa_kev'
        },
        {
            'name': 'NVD CVEs',
            'script': ingestion_dir / 'ingest_nvd_cves.py',
            'required': False,
            'data_key': 'nvd_cves'
        },
        {
            'name': 'MITRE ATT&CK',
            'script': ingestion_dir / 'ingest_mitre_attack.py',
            'required': False,
            'data_key': 'mitre_attack'
        },
        {
            'name': 'CVE to Controls Auto-Mapping',
            'script': ingestion_dir / 'automap_cve_to_controls.py',
            'required': False,
            'data_key': None  # Runs after CVE ingestion
        }
    ]
    
    # Execute ingestion steps
    logger.info("\n" + "=" * 70)
    logger.info("STARTING INGESTION SEQUENCE")
    logger.info("=" * 70)
    
    results = []
    
    for step in ingestion_steps:
        step_name = step['name']
        script_path = step['script']
        required = step['required']
        data_key = step['data_key']
        
        # Check if data file is available (if applicable)
        if data_key and not availability.get(data_key, False):
            logger.warning(f"\n⚠ Skipping {step_name}: Data file not available")
            results.append({
                'name': step_name,
                'status': 'skipped',
                'reason': 'Data file not available'
            })
            continue
        
        # Check if script exists
        if not script_path.exists():
            logger.error(f"\n✗ Script not found: {script_path}")
            if required:
                logger.error("This is a required step. Aborting.")
                sys.exit(1)
            results.append({
                'name': step_name,
                'status': 'failed',
                'reason': 'Script not found'
            })
            continue
        
        # Run the script
        success = run_script(script_path, step_name)
        
        results.append({
            'name': step_name,
            'status': 'success' if success else 'failed',
            'reason': None
        })
        
        if not success and required:
            logger.error(f"\n✗ Required step '{step_name}' failed. Aborting.")
            sys.exit(1)
    
    # Print summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("\n" + "=" * 70)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Duration: {duration}")
    logger.info("")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    skipped_count = sum(1 for r in results if r['status'] == 'skipped')
    
    for result in results:
        status_symbol = {
            'success': '✓',
            'failed': '✗',
            'skipped': '⊘'
        }.get(result['status'], '?')
        
        status_msg = f"{status_symbol} {result['name']}: {result['status'].upper()}"
        if result['reason']:
            status_msg += f" ({result['reason']})"
        
        logger.info(status_msg)
    
    logger.info("")
    logger.info(f"Total Steps: {len(results)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {failed_count}")
    logger.info(f"Skipped: {skipped_count}")
    
    if failed_count == 0:
        logger.info("\n✓ All ingestion steps completed successfully!")
    else:
        logger.warning(f"\n⚠ {failed_count} step(s) failed. Review the logs above for details.")
    
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
