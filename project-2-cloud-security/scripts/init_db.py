import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import DatabaseManager
import sqlite3

def init_db():
    print("Initializing database...")
    db = DatabaseManager()
    
    # "Golden List" of 32 CIS Controls (v1.4.0)
    controls = [
        # IAM (10)
        ("CIS-1.1", "Root Account MFA Enabled", "The 'root' account has the most privileges and must be protected by MFA.", "Critical", "Identity & Access Management", "1.1"),
        ("CIS-1.2", "Root Account Access Keys", "The 'root' account should not have access keys.", "Critical", "Identity & Access Management", "1.2"),
        ("CIS-1.3", "Credentials Unused > 90 Days", "Disable IAM users/credentials unused for >90 days.", "High", "Identity & Access Management", "1.3"),
        ("CIS-1.5", "Comprehensive Password Policy", "Ensure password policy requires: 14+ chars, upper, lower, numbers, symbols, reuse prevention.", "High", "Identity & Access Management", "1.5"),
        ("CIS-1.6", "Hardware MFA for Root", "Root account should use hardware MFA (not virtual).", "Critical", "Identity & Access Management", "1.6"),
        ("CIS-1.7", "Eliminate Usage of Root User", "Root user should not be used for daily administrative tasks.", "Critical", "Identity & Access Management", "1.7"),
        ("CIS-1.8", "IAM User MFA Enabled", "All IAM users with console access must have MFA enabled.", "High", "Identity & Access Management", "1.8"),
        ("CIS-1.9", "Access Key Rotation (90 Days)", "Access keys should be rotated every 90 days.", "High", "Identity & Access Management", "1.9"),
        ("CIS-1.15", "IAM Policies Attached to Groups", "IAM policies should be attached to groups/roles, not users directly.", "Medium", "Identity & Access Management", "1.15"),
        ("CIS-1.17", "Support Role Created", "Ensure a support role has been created to manage incidents with AWS Support.", "Medium", "Identity & Access Management", "1.17"),

        # Storage (8)
        ("CIS-2.1.1", "S3 Bucket Encryption", "Ensure all S3 buckets have server-side encryption enabled.", "High", "Storage", "2.1.1"),
        ("CIS-2.1.2", "S3 Bucket Versioning", "Ensure S3 bucket versioning is enabled.", "Medium", "Storage", "2.1.2"),
        ("CIS-2.1.5", "S3 Block Public Access", "Ensure S3 buckets have Block Public Access enabled.", "Critical", "Storage", "2.1.5"),
        ("CIS-2.3", "S3 Access Logging", "Ensure S3 buckets have server access logging enabled.", "Medium", "Storage", "2.3"),
        ("CIS-2.6", "S3 Public Read Disabled", "Ensure no S3 buckets allow public read via ACLs or Policy.", "Critical", "Storage", "2.6"),
        ("CIS-2.8", "KMS Key Rotation", "Ensure rotation for customer created CMKs is enabled.", "High", "Storage", "2.8"),
        ("CIS-2.10", "S3 Object Logging", "Ensure S3 object-level logging (write) is enabled in CloudTrail.", "Medium", "Storage", "2.10"),
        ("CIS-2.11", "Enforce SSL in S3 Policies", "Ensure S3 bucket policies deny HTTP checks.", "High", "Storage", "2.11"),

        # Logging (5)
        ("CIS-2.1", "CloudTrail Enabled in All Regions", "Ensure CloudTrail is enabled in all regions.", "Critical", "Logging", "2.1"),
        ("CIS-2.2", "CloudTrail Log File Validation", "Ensure CloudTrail log file validation is enabled.", "Medium", "Logging", "2.2"),
        ("CIS-2.4", "CloudWatch Logs Integration", "Ensure CloudTrail trails are integrated with CloudWatch Logs.", "High", "Logging", "2.4"),
        ("CIS-2.5", "AWS Config Enabled", "Ensure AWS Config is enabled in all regions.", "High", "Logging", "2.5"),
        ("CIS-2.7", "CloudTrail Logs Encrypted with KMS", "Ensure CloudTrail logs are encrypted using KMS CMKs.", "High", "Logging", "2.7"),

        # Monitoring (5)
        ("CIS-3.1", "Metric Filter: Unauthorized API", "Ensure a log metric filter exists for unauthorized API calls.", "Medium", "Monitoring", "3.1"),
        ("CIS-3.2", "Metric Filter: Console No MFA", "Ensure a log metric filter exists for console logins without MFA.", "Medium", "Monitoring", "3.2"),
        ("CIS-3.4", "Metric Filter: IAM Changes", "Ensure a log metric filter exists for IAM policy changes.", "Medium", "Monitoring", "3.4"),
        ("CIS-3.5", "Metric Filter: CloudTrail Config Changes", "Ensure a log metric filter exists for CloudTrail configuration changes.", "Medium", "Monitoring", "3.5"),
        ("CIS-3.9", "Metric Filter: AWS Config Changes", "Ensure a log metric filter exists for AWS Config changes.", "Medium", "Monitoring", "3.9"),

        # Networking (4)
        ("CIS-5.1", "No Unrestricted SSH/RDP Access", "Ensure no security groups allow ingress from 0.0.0.0/0 to port 22 or 3389.", "Critical", "Networking", "5.1"),
        ("CIS-5.2", "No Unrestricted Egress", "Ensure no security groups allow unrestricted egress to 0.0.0.0/0.", "Medium", "Networking", "5.2"),
        ("CIS-5.3", "Default Security Group Closed", "Ensure the default security group of every VPC restricts all traffic.", "High", "Networking", "5.3"),
        ("CIS-2.9", "VPC Flow Logs Enabled", "Ensure VPC Flow Logs are enabled for all VPCs.", "High", "Networking", "2.9")
        # Note: Kept 2.9 ID for VPC Flow Logs as originally planned but moved to Networking category logically here or keep in Logging? 
        # Plan said Networking 4 controls. 5.1, 5.2, 5.3, 2.9 makes 4.
    ]

    conn = sqlite3.connect(db.db_path)
    c = conn.cursor()
    
    # Wipe existing
    print("Clearing existing controls...")
    c.execute('DELETE FROM controls')
    
    print(f"Populating {len(controls)} controls...")
    for ctrl in controls:
        try:
            c.execute('INSERT INTO controls (control_id, title, description, severity, category, cis_reference) VALUES (?, ?, ?, ?, ?, ?)', ctrl)
        except sqlite3.IntegrityError:
            print(f"Control {ctrl[0]} already exists, skipping.")
            
    conn.commit()
    conn.close()
    print("Database re-initialization complete.")

if __name__ == "__main__":
    init_db()
