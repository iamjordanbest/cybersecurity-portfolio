# Terraform Deployment Quick Start

## 🚀 **Deploy AWS Infrastructure**

From the `project-3-cloud-security/terraform` directory:

### **Step 1: Initialize Terraform**
```powershell
terraform init
```

This downloads the AWS provider and sets up the backend.

**Expected output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.x.x...

Terraform has been successfully initialized!
```

---

### **Step 2: Preview Changes**
```powershell
terraform plan
```

This shows what resources Terraform will create. You should see:
- 1 IAM password policy
- 1 IAM group (security-auditors)
- 1 KMS key (for CloudTrail encryption)
- 2 S3 buckets (cloudtrail-logs, compliance-evidence)
- 1 CloudTrail trail (multi-region)
- 1 VPC with flow logs
- 1 Security group (restrictive)

**Review the plan** - make sure there are no unexpected changes.

---

### **Step 3: Deploy Infrastructure**
```powershell
terraform apply
```

Type **`yes`** when prompted.

**Deployment takes ~2-3 minutes.**

**Expected output:**
```
Apply complete! Resources: 15 added, 0 changed, 0 destroyed.

Outputs:

account_id = "123456789012"
cloudtrail_arn = "arn:aws:cloudtrail:us-east-1:123456789012:trail/cspm-auditor-trail"
cloudtrail_is_multi_region = true
cloudtrail_log_validation_enabled = true
iam_password_policy = {
  "max_age" = 90
  "min_length" = 14
  "require_numbers" = true
  "require_symbols" = true
  "reuse_prevention" = 24
}
kms_key_arn = "arn:aws:kms:us-east-1:123456789012:key/abc123..."
vpc_id = "vpc-0a1b2c3d4e5f6"
```

---

### **Step 4: Verify in AWS Console**

1. **IAM Password Policy:**
   - Go to IAM → Account settings
   - Verify: Minimum length = 14, complexity requirements enabled

2. **CloudTrail:**
   - Go to CloudTrail → Trails
   - Verify: `cspm-auditor-trail` is active, multi-region, encrypted

3. **S3 Buckets:**
   - Go to S3
   - Verify: 2 buckets exist with versioning and encryption enabled

4. **VPC Flow Logs:**
   - Go to VPC → Your VPCs
   - Select your VPC → Flow logs tab
   - Verify: Flow log is active

---

## 🎯 **What You Just Accomplished**

| CIS Control | Status | Evidence Location |
|-------------|--------|-------------------|
| CIS-1.12 | ✅ PASS | IAM → Account settings |
| CIS-2.1 | ✅ PASS | CloudTrail → Trails |
| CIS-2.2 | ✅ PASS | CloudTrail log validation enabled |
| CIS-2.7 | ✅ PASS | KMS key ARN in CloudTrail config |
| CIS-2.1.1 | ✅ PASS | S3 buckets → Properties → Encryption |
| CIS-2.1.2 | ✅ PASS | S3 buckets → Properties → Versioning |
| CIS-2.1.4 | ✅ PASS | S3 buckets → Permissions → Block public access |
| CIS-4.1 | ✅ PASS | VPC → Flow logs |

**You're now ~40% compliant with the 20 CIS controls!**

---

## 🔍 **Collecting Evidence**

Take screenshots of:
1. **IAM password policy** (IAM → Account settings)
2. **CloudTrail configuration** (CloudTrail → cspm-auditor-trail)
3. **S3 bucket encryption** (S3 → bucket → Properties)
4. **VPC flow logs** (VPC → Flow logs tab)

Save these to `evidence/` directory with naming:
- `CIS-1.12_password_policy.png`
- `CIS-2.1_cloudtrail_multi_region.png`
- `CIS-2.7_cloudtrail_encryption.png`
- `CIS-4.1_vpc_flow_logs.png`

---

## 💰 **Cost Check**

Run this to verify you're still in free tier:
```powershell
# Check S3 storage
aws s3 ls

# Check CloudTrail status
aws cloudtrail describe-trails
```

**Expected cost: $0.00/month** (all resources are free tier eligible)

---

## 🛠️ **If You Need to Destroy**

⚠️ **Only run this if you want to tear down all infrastructure:**
```powershell
terraform destroy
```

Type **`yes`** when prompted. This will delete all AWS resources.

---

**Next Step:** Build Python auditors to verify these controls automatically!
