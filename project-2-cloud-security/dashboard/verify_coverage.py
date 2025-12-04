import sqlite3

# Define the controls found in the code
implemented_controls = {
    'CIS-1.4': 'Root Account MFA',
    'CIS-1.12': 'Strong Password Policy / Unused Users', # Used twice in code!
    'CIS-1.20': 'Support Role',
    'CIS-4.2': 'Metric Filter Unauthorized API',
    'CIS-1.16': 'IAM Policies on Groups',
    'CIS-1.14': 'Access Key Rotation',
    'CIS-2.1': 'CloudTrail Enabled',
    'CIS-2.2': 'CloudTrail Log Validation',
    'CIS-2.7': 'CloudTrail Encryption',
    'CIS-2.5': 'AWS Config Enabled',
    'CIS-4.4': 'Metric Filter IAM',
    'CIS-4.5': 'Metric Filter CloudTrail',
    'CIS-4.9': 'Metric Filter Config',
    'CIS-4.1': 'SSH/RDP Access',
    'CIS-4.3': 'Default SG',
    'CIS-2.9': 'VPC Flow Logs',
    'CIS-2.1.1': 'S3 Encryption',
    'CIS-2.1.5': 'S3 Block Public Access',
    'CIS-2.1.2': 'S3 Versioning'
}

DB_PATH = "../data/cspm.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("=== AUDIT COVERAGE VERIFICATION ===\n")

# Get DB controls
c.execute("SELECT control_id, title FROM controls ORDER BY control_id")
db_controls = {row[0]: row[1] for row in c.fetchall()}

print(f"Total Controls in DB: {len(db_controls)}")
print(f"Total Controls Implemented in Code: {len(implemented_controls)}")

print("\n--- Detailed Comparison ---")
matched = []
missing_implementation = []
extra_implementation = []

for cid in db_controls:
    if cid in implemented_controls:
        matched.append(cid)
    else:
        missing_implementation.append(cid)

for cid in implemented_controls:
    if cid not in db_controls:
        extra_implementation.append(cid)

print(f"✅ Matched Controls: {len(matched)}")
if matched:
    print(f"   {', '.join(sorted(matched))}")

if missing_implementation:
    print(f"\n❌ Controls in DB but NO CODE found: {len(missing_implementation)}")
    for cid in missing_implementation:
        print(f"   - {cid}: {db_controls[cid]}")

if extra_implementation:
    print(f"\n⚠️ Controls in CODE but NOT in DB: {len(extra_implementation)}")
    for cid in extra_implementation:
        print(f"   - {cid}")

conn.close()
