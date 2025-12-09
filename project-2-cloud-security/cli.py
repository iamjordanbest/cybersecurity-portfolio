import click
import boto3
import json
import logging
from datetime import datetime
from auditors.iam_auditor import IAMAuditor
from auditors.logging_auditor import LoggingAuditor
from auditors.storage_auditor import StorageAuditor
from auditors.network_auditor import NetworkAuditor
from auditors.monitoring_auditor import MonitoringAuditor
from auditors.iam_auditor import IAMAuditor
from models.compliance import ControlStatus

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """CSPM Auditor CLI - Cloud Security Posture Management"""
    pass

@cli.command()
@click.option('--profile', default='default', help='AWS CLI profile to use')
@click.option('--region', default='us-east-1', help='AWS region')
@click.option('--output', default='report.json', help='Output file for results')
def audit(profile, region, output):
    """Run full compliance audit against AWS account"""
    logger.info(f"Starting audit using profile: {profile} in region: {region}")
    
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
    except Exception as e:
        logger.error(f"Failed to create AWS session: {e}")
        return

    auditors = [
        IAMAuditor(session),
        LoggingAuditor(session),
        StorageAuditor(session),
        NetworkAuditor(session),
        MonitoringAuditor(session)
    ]

    all_results = []
    
    for auditor in auditors:
        name = auditor.__class__.__name__
        logger.info(f"Running {name}...")
        try:
            results = auditor.audit_all()
            # Handle list of results or single result (MonitoringAuditor returns list logic needs fix in real app)
            # For now assuming audit_all returns List[AssessmentResult]
            if isinstance(results, list):
                all_results.extend(results)
            else:
                all_results.append(results)
        except Exception as e:
            logger.error(f"Error running {name}: {e}")

    # Calculate summary
    total = len(all_results)
    passed = sum(1 for r in all_results if r.status == ControlStatus.PASS)
    failed = sum(1 for r in all_results if r.status == ControlStatus.FAIL)
    
    logger.info(f"Audit Complete. Total: {total}, Pass: {passed}, Fail: {failed}")

    # Save results to JSON
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "account_id": session.client('sts').get_caller_identity()['Account'],
        "summary": {
            "total_controls": total,
            "passed": passed,
            "failed": failed,
            "score": round((passed / total) * 100, 2) if total > 0 else 0
        },
        "results": [
            {
                "control_id": r.control_id,
                "status": r.status.value,
                "findings": [f.description for f in r.findings],
                "severity": r.findings[0].severity.value if r.findings else "None"
            }
            for r in all_results
        ]
    }

    with open(output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Results saved to {output}")

    # Save results to Database
    try:
        from data.database import DatabaseManager
        db = DatabaseManager()
        run_id = db.save_assessment(output_data['account_id'], all_results)
        logger.info(f"Results saved to database (Run ID: {run_id})")
    except Exception as e:
        logger.error(f"Failed to save to database: {e}")

@cli.command()
def dashboard():
    """Launch interactive Streamlit dashboard."""
    import os
    print("🚀 Starting CSPM Dashboard on port 8502...")
    os.system("streamlit run dashboard/app.py --server.port 8502")

if __name__ == '__main__':
    cli()
