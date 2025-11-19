import boto3
import logging
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudSecurityScanner:
    """
    Scans AWS environment for common security misconfigurations.
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.session = boto3.Session(region_name=region)
        self.s3 = self.session.client('s3')
        self.ec2 = self.session.client('ec2')
        self.iam = self.session.client('iam')
        
    def scan_s3_buckets(self) -> List[Dict[str, Any]]:
        """Check for public S3 buckets."""
        findings = []
        try:
            response = self.s3.list_buckets()
            for bucket in response['Buckets']:
                name = bucket['Name']
                try:
                    # Check public access block
                    pab = self.s3.get_public_access_block(Bucket=name)
                    conf = pab['PublicAccessBlockConfiguration']
                    if not (conf['BlockPublicAcls'] and conf['BlockPublicPolicy'] and 
                            conf['IgnorePublicAcls'] and conf['RestrictPublicBuckets']):
                        findings.append({
                            'resource_id': name,
                            'type': 's3_bucket',
                            'issue': 'Public Access Block not fully enabled',
                            'severity': 'High'
                        })
                except self.s3.exceptions.NoSuchPublicAccessBlockConfiguration:
                     findings.append({
                            'resource_id': name,
                            'type': 's3_bucket',
                            'issue': 'No Public Access Block configuration found',
                            'severity': 'High'
                        })
                except Exception as e:
                    logger.error(f"Error scanning bucket {name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error listing buckets: {e}")
            
        return findings

    def scan_security_groups(self) -> List[Dict[str, Any]]:
        """Check for overly permissive security groups."""
        findings = []
        try:
            response = self.ec2.describe_security_groups()
            for sg in response['SecurityGroups']:
                for perm in sg['IpPermissions']:
                    # Check for 0.0.0.0/0 on sensitive ports
                    for range in perm.get('IpRanges', []):
                        if range.get('CidrIp') == '0.0.0.0/0':
                            port_range = f"{perm.get('FromPort', 'All')}-{perm.get('ToPort', 'All')}"
                            if perm.get('FromPort') in [22, 3389, 3306, 5432]:
                                findings.append({
                                    'resource_id': sg['GroupId'],
                                    'type': 'security_group',
                                    'issue': f"Open access (0.0.0.0/0) on port {port_range}",
                                    'severity': 'Critical'
                                })
        except Exception as e:
            logger.error(f"Error scanning security groups: {e}")
            
        return findings

    def run_full_scan(self) -> Dict[str, Any]:
        """Run all scans and return aggregated findings."""
        logger.info("Starting full cloud security scan...")
        
        s3_findings = self.scan_s3_buckets()
        sg_findings = self.scan_security_groups()
        
        all_findings = s3_findings + sg_findings
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_findings': len(all_findings),
            'findings': all_findings
        }

if __name__ == "__main__":
    # Example usage (requires AWS credentials)
    try:
        scanner = CloudSecurityScanner()
        results = scanner.run_full_scan()
        print(f"Scan Complete. Found {results['total_findings']} issues.")
        for f in results['findings']:
            print(f"- [{f['severity']}] {f['type']} {f['resource_id']}: {f['issue']}")
    except Exception as e:
        print(f"Scan failed (check AWS credentials): {e}")
