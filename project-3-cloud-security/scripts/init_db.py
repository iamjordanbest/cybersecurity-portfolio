import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import DatabaseManager
import sqlite3

def init_db():
    print("Initializing database...")
    db = DatabaseManager()
    
    # Populate CIS Controls
    controls = [
        # IAM
        ("CIS-1.4", "Root Account MFA Enabled", "The 'root' account has the most privileges and must be protected by MFA.", "Critical", "Identity & Access Management", "1.4"),
        ("CIS-1.12", "Strong Password Policy", "Ensure IAM password policy requires at least 14 characters.", "High", "Identity & Access Management", "1.12"),
        ("CIS-1.16", "IAM Policies Attached to Groups", "IAM policies should be attached to groups/roles, not users directly.", "Medium", "Identity & Access Management", "1.16"),
        ("CIS-1.20", "Access Keys Rotated Every 90 Days", "Access keys should be rotated every 90 days.", "High", "Identity & Access Management", "1.20"),
        ("CIS-1.14", "Hardware MFA for Root Account", "Root account uses hardware MFA device.", "Critical", "Identity & Access Management", "1.14"),
        
        # Logging
        ("CIS-2.1", "CloudTrail Enabled in All Regions", "Ensure CloudTrail is enabled in all regions.", "Critical", "Logging", "2.1"),
        ("CIS-2.2", "CloudTrail Log File Validation", "Ensure CloudTrail log file validation is enabled.", "Medium", "Logging", "2.2"),
        ("CIS-2.7", "CloudTrail Logs Encrypted with KMS", "Ensure CloudTrail logs are encrypted using KMS CMKs.", "High", "Logging", "2.7"),
        
        # Storage
        ("CIS-2.1.1", "S3 Bucket Encryption", "Ensure all S3 buckets have server-side encryption enabled.", "High", "Storage", "2.1.1"),
        ("CIS-2.1.2", "S3 Bucket Versioning", "Ensure S3 bucket versioning is enabled.", "Medium", "Storage", "2.1.2"),
        ("CIS-2.1.5", "S3 Block Public Access", "Ensure S3 buckets have Block Public Access enabled.", "Critical", "Storage", "2.1.5"),
        
        # Networking
        ("CIS-4.1", "No Unrestricted SSH/RDP Access", "Ensure no security groups allow ingress from 0.0.0.0/0 to port 22 or 3389.", "Critical", "Networking", "4.1"),
        ("CIS-4.2", "VPC Flow Logs Enabled", "Ensure VPC Flow Logs are enabled for all VPCs.", "High", "Networking", "4.2"),
        ("CIS-4.3", "Default Security Group Restricts All Traffic", "Ensure the default security group of every VPC restricts all traffic.", "High", "Networking", "4.3"),
        ("CIS-2.9", "VPC Flow Logs Enabled", "Ensure VPC Flow Logs are enabled for all VPCs.", "High", "Networking", "2.9"),
        
        # Monitoring
        ("CIS-4.4", "Metric Filter for IAM Policy Changes", "Ensure a log metric filter and alarm exist for IAM policy changes.", "Medium", "Monitoring", "4.4"),
        ("CIS-4.5", "Metric Filter for CloudTrail Changes", "Ensure a log metric filter and alarm exist for CloudTrail configuration changes.", "Medium", "Monitoring", "4.5"),
        ("CIS-4.9", "Metric Filter for AWS Config Changes", "Ensure a log metric filter and alarm exist for AWS Config changes.", "Medium", "Monitoring", "4.9"),
        
        # Placeholders for others to reach 20 if needed, or we stick to the implemented ones
        # We implemented ~15 controls so far. Let's add the ones we have code for.
    ]

    conn = sqlite3.connect(db.db_path)
    c = conn.cursor()
    
    print(f"Populating {len(controls)} controls...")
    for ctrl in controls:
        try:
            c.execute('INSERT INTO controls (control_id, title, description, severity, category, cis_reference) VALUES (?, ?, ?, ?, ?, ?)', ctrl)
        except sqlite3.IntegrityError:
            print(f"Control {ctrl[0]} already exists, skipping.")
            
    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
