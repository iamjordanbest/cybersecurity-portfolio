# AWS Infrastructure Verification Guide

## 🔍 **Verify Your Deployment in AWS Console**

Follow these steps to confirm your Terraform deployment was successful.

### **1. Verify IAM Password Policy (CIS-1.12)**
1. Go to **IAM** service
2. Click **Account settings** in the left sidebar
3. Check "Password policy" section:
   - [ ] Minimum password length: **14**
   - [ ] Require at least one uppercase letter: **Yes**
   - [ ] Require at least one lowercase letter: **Yes**
   - [ ] Require at least one number: **Yes**
   - [ ] Require at least one non-alphanumeric character: **Yes**
   - [ ] Password expiration: **90 days**

### **2. Verify S3 Buckets (CIS-2.1)**
1. Go to **S3** service
2. You should see 2 new buckets starting with `cspm-auditor-`:
   - `cspm-auditor-cloudtrail-logs-...`
   - `cspm-auditor-compliance-evidence-...`
3. Click on **cloudtrail-logs** bucket -> **Properties** tab:
   - [ ] Bucket Versioning: **Enabled**
   - [ ] Default encryption: **Server-side encryption with Amazon S3 managed keys (SSE-S3)**
4. Click **Permissions** tab:
   - [ ] Block all public access: **On**

### **3. Verify CloudTrail (CIS-2.1, 2.2, 2.7)**
1. Go to **CloudTrail** service
2. Click **Trails** in the left sidebar
3. Click on **cspm-auditor-trail**:
   - [ ] Multi-region trail: **Yes**
   - [ ] Log file validation: **Enabled**
   - [ ] KMS Key Alias: **alias/cspm-auditor-cloudtrail**
   - [ ] Storage location: Matches your S3 bucket name

### **4. Verify VPC & Flow Logs (CIS-4.1)**
1. Go to **VPC** service
2. Click **Your VPCs**
3. Select **cspm-auditor-vpc**
4. Click **Flow logs** tab (bottom panel):
   - [ ] Status: **Active**
   - [ ] Destination name: **/aws/vpc/cspm-auditor-flow-logs**

### **5. Verify Security Group (CIS-4.2)**
1. In VPC Dashboard, click **Security groups**
2. Find **cspm-auditor-restricted-sg**:
   - [ ] Inbound rules: **0 rules** (Empty - this is correct/secure)
   - [ ] Outbound rules: **1 rule** (HTTPS/443 to 0.0.0.0/0)

---

## ✅ **Verification Checklist**

- [ ] IAM Password Policy correct
- [ ] 2 S3 Buckets created & secure
- [ ] CloudTrail active & encrypted
- [ ] VPC Flow Logs active
- [ ] Security Group restricted

**If all checks pass, your infrastructure is perfectly deployed!** 🚀
