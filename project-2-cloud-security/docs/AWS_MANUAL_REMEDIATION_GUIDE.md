# AWS Manual Remediation Guide: 32 CIS Controls

This guide provides step-by-step instructions to manually configure your AWS environment using the **AWS Management Console** to pass all 32 CIS Controls checked by the project's auditor.

---

## 🛡️ Identity & Access Management (IAM) - 10 Controls

### CIS-1.1: Root Account MFA
**Goal:** Enable Multi-Factor Authentication (MFA) for the root user.
1. Sign in to the AWS Console as **Root User**.
2. Go to **IAM Dashboard** (search "IAM").
3. You will see a security alert "Add MFA for root user". Click **Add MFA**.
4. Choose **MFA device** (Virtual Authenticator App like Google Authenticator is easiest).
5. Follow the on-screen steps to scan the QR code and enter two consecutive codes.
6. **Result:** Dashboard 'Root Account MFA' check will pass.

### CIS-1.2: Root Account Access Keys
**Goal:** Remove all programmatic access keys for the root user.
1. Sign in as **Root User**.
2. Click your account name (top right) -> **Security credentials**.
3. Expand **Access keys**.
4. If any keys exist, click **Delete** for each one.
5. **Result:** Dashboard 'Root Account Access Keys' check will pass.

### CIS-1.3: Unused Credentials (>90 Days)
**Goal:** Disable users or keys not used for 3 months.
1. Go to **IAM Dashboard** -> **Users**.
2. Look at the **Last activity** column.
3. If "None" or date > 90 days ago:
   - Select user -> **Delete user** (if obsolete).
   - OR Select user -> **Security credentials** -> **Console login** -> **Manage** -> **Disable**.
   - AND under **Access keys**, assume Action -> **Deactivate** or **Delete**.

### CIS-1.5: Password Policy
**Goal:** Set a strong password policy.
1. Go to **IAM Dashboard** -> **Account settings** (sidebar).
2. Click **Change password policy**.
3. Configure:
   - **Minimum password length**: 14+
   - [x] Require at least one uppercase letter
   - [x] Require at least one lowercase letter
   - [x] Require at least one number
   - [x] Require at least one non-alphanumeric character
   - [x] Prevent password reuse (set to 24)
4. Click **Save changes**.

### CIS-1.6: Hardware MFA for Root
**Goal:** Use a physical key (YubiKey) for Root MFA.
*Note: This check usually requires manual verification as API can only see "MFA Enabled" type. If you used a Virtual MFA in 1.1, the automated check might flag a warning or simple PASS based on MFA presence. To be strictly compliant:*
1. Buy a hardware key (e.g., YubiKey).
2. Follow CIS-1.1 steps but choose **Security Key** instead of Virtual App.

### CIS-1.7: Eliminate Root User Usage
**Goal:** Don't log in as root for everyday tasks.
1. Create an IAM User with Admin permissions (see CIS-1.16).
2. **Stop using the root user** for daily work.
3. The check looks at CloudTrail for events by "root". Wait >90 days without root login for clean pass, or manually verify "last login" date in IAM dashboard is old.

### CIS-1.8: IAM User MFA
**Goal:** All users with Console Access must have MFA.
1. Go to **IAM Dashboard** -> **Users**.
2. For *every user* with "Console password" enabled:
   - Click user name -> **Security credentials**.
   - **Multi-factor authentication (MFA)** -> **Assign MFA device**.

### CIS-1.9: Access Key Rotation
**Goal:** Rotate keys older than 90 days.
1. Go to **IAM Dashboard** -> **Users**.
2. Select user -> **Security credentials**.
3. Under **Access keys**, check "Created" date.
4. If >90 days:
   - Create **Create access key**.
   - Update your applications with the new key.
   - **Make inactive** the old key.
   - **Delete** the old key after verification.

### CIS-1.15: IAM Policies on Groups
**Goal:** Don't attach policies directly to users. Use Groups.
1. Go to **IAM Dashboard** -> **Users**.
2. Click a user -> **Permissions** tab.
3. If you see policies under "Attached directly":
   - **Remove** them.
4. Go to **User groups** -> **Create group**.
5. Attach the policies to the **Group**.
6. Add the user to the **Group**.

### CIS-1.17: Support Role
**Goal:** Creating a role for AWS Support.
1. Go to **IAM Dashboard** -> **Roles**.
2. **Create role**.
3. Trusted entity: **AWS account** -> **Another AWS account** -> Enter your Account ID.
   *Note: CIS strictly wants a role that allows AWS Support access, often assumes a specific support policy.*
4. Permissions: Search and select **AWSSupportAccess**.
5. Role name: Enter a name (e.g., `AWSSupportRole`).
6. Create.

---

## 📦 Storage (S3 + KMS) - 8 Controls

### CIS-2.1.1: S3 Encryption
**Goal:** Encrypt all buckets.
1. Go to **S3 Console**.
2. For each bucket -> **Properties** tab.
3. Scroll to **Default encryption**.
4. Click **Edit** -> Enable **Server-side encryption with Amazon S3 managed keys (SSE-S3)**.
5. Save.

### CIS-2.1.2: S3 Versioning
**Goal:** Enable versioning.
1. For each bucket -> **Properties** tab.
2. **Bucket Versioning** -> Edit -> **Enable**.

### CIS-2.1.5: S3 Block Public Access
**Goal:** Global block of public access.
1. For each bucket -> **Permissions** tab.
2. **Block public access (bucket settings)** -> Edit.
3. Check **Block all public access**.
4. Save (type "confirm").

### CIS-2.3: S3 Access Logging
**Goal:** Log bucket access requests.
1. Create a "Logging Bucket" (e.g., `my-logs-bucket`) first.
2. For your data bucket -> **Properties**.
3. **Server access logging** -> Edit -> **Enable**.
4. Start bucket: Select your `my-logs-bucket`.

### CIS-2.6: S3 Public Read Disabled
**Goal:** No public Read/Write ACLs.
*Step 2.1.5 usually covers this.*
1. Go to **Permissions** tab.
2. **Access control list (ACL)** -> Edit.
3. Ensure "Everyone (public access)" has **List** and **Read** unchecked.

### CIS-2.8: KMS Key Rotation
**Goal:** Rotate Customer Managed Keys (CMKs).
1. Go to **KMS Console** -> **Customer managed keys**.
2. Click your key (not AWS managed keys).
3. **Key rotation** tab -> Check **Automatically rotate this key every year**.
4. Save.

### CIS-2.10: S3 Object Logging
**Goal:** Log data events in CloudTrail.
1. Go to **CloudTrail Console** -> **Trails**.
2. Select your trail.
3. **Data events** -> Edit.
4. **Add data event type** -> Source: **S3**.
5. Log: **Write only** (or All).
6. Save.

### CIS-2.11: Enforce SSL
**Goal:** Deny HTTP traffic.
1. Go to bucket -> **Permissions** -> **Bucket Policy**.
2. Add this statement:
```json
{
  "Sid": "EnforceSSL",
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:*",
  "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*",
  "Condition": {
    "Bool": {
      "aws:SecureTransport": "false"
    }
  }
}
```

---

## 📝 Logging - 5 Controls

### CIS-2.1: CloudTrail Enabled
**Goal:** Enable CloudTrail in all regions.
1. Go to **CloudTrail Console**.
2. **Create trail**.
3. Name: `management-events-trail`.
4. Ensure **Multi-region trail** is CHECKED.
5. Create new S3 bucket for logs.
6. Create.

### CIS-2.2: Log Validation
**Goal:** Integrity checks.
1. Select your Trail -> **General details** -> Edit.
2. **Log file validation** -> **Enabled**.
3. Save.

### CIS-2.4: CloudWatch Integration
**Goal:** Send Trail logs to CloudWatch.
1. Select your Trail -> **CloudWatch Logs** section -> Edit.
2. **Enabled**.
3. Log Group: Leave default or create new (`CloudTrail/DefaultLogGroup`).
4. IAM Role: Create new (auto-generated).
5. Save.

### CIS-2.5: AWS Config
**Goal:** Enable recording.
1. Go to **AWS Config Console**.
2. Click **Get Started** (or Settings -> Edit).
3. **Recording strategy**: Record all resources supported in this region.
4. **Include global resources**: Checked.
5. **Delivery method**: Choose/Create S3 bucket.
6. Save.

### CIS-2.7: CloudTrail Encryption
**Goal:** Encrypt Trail logs with KMS.
1. Go to **KMS** -> Create Symmetric Key -> Name `CloudTrailKey`.
2. Add CloudTrail service policy to Key Policy (Advanced step).
3. Go to **CloudTrail** -> Select Trail -> **General details** -> Edit.
4. **AWS KMS key** -> Enabled.
5. Select your `CloudTrailKey`.

---

## 📊 Monitoring - 5 Controls (Metric Filters)

**General Process for all 3.x Controls:**
1. Go to **CloudWatch Console** -> **Logs** -> **Log groups**.
2. Select the Log Group used by CloudTrail in Step 2.4.
3. **Metric filters** tab -> **Create metric filter**.

### CIS-3.1: Unauthorized API
- **Filter pattern:** `{($.errorCode = "*UnauthorizedOperation") || ($.errorCode = "AccessDenied*")}`
- **Metric name:** `UnauthorizedAPICalls`
- **Value:** `1`
- **Next** -> **Create Alarm** (Threshold >= 1).

### CIS-3.2: Console No MFA
- **Filter pattern:** `{($.eventName = "ConsoleLogin") && ($.additionalEventData.MFAUsed != "Yes")}`
- **Metric name:** `ConsoleSignInWithoutMFA`

### CIS-3.4: IAM Changes
- **Filter pattern:** `{($.eventName=DeleteGroupPolicy)||($.eventName=DeleteRolePolicy)||($.eventName=DeleteUserPolicy)||($.eventName=PutGroupPolicy)||($.eventName=PutRolePolicy)||($.eventName=PutUserPolicy)||($.eventName=CreatePolicy)||($.eventName=DeletePolicy)||($.eventName=CreatePolicyVersion)||($.eventName=DeletePolicyVersion)||($.eventName=AttachRolePolicy)||($.eventName=DetachRolePolicy)||($.eventName=AttachUserPolicy)||($.eventName=DetachUserPolicy)||($.eventName=AttachGroupPolicy)||($.eventName=DetachGroupPolicy)}`
- **Metric name:** `IAMPolicyChanges`

### CIS-3.5: CloudTrail Config Changes
- **Filter pattern:** `{($.eventName=CreateTrail)||($.eventName=UpdateTrail)||($.eventName=DeleteTrail)||($.eventName=StartLogging)||($.eventName=StopLogging)}`
- **Metric name:** `CloudTrailChanges`

### CIS-3.9: AWS Config Changes
- **Filter pattern:** `{($.eventSource=config.amazonaws.com) && (($.eventName=StopConfigurationRecorder)||($.eventName=DeleteDeliveryChannel)||($.eventName=PutDeliveryChannel)||($.eventName=PutConfigurationRecorder))}`
- **Metric name:** `AWSConfigChanges`

---

## 🌐 Networking - 4 Controls

### CIS-2.9: VPC Flow Logs
**Goal:** Enable network traffic logging.
1. Go to **VPC Console** -> **Your VPCs**.
2. Select VPC -> **Flow logs** tab -> **Create flow log**.
3. Filter: **All**.
4. Destination: **CloudWatch Logs**.
5. Target Log Group: Create/Select one.
6. IAM Role: Create/Select role with permissions.
7. Create.

### CIS-5.1: No Unrestricted SSH/RDP
**Goal:** Close risky ports/
1. Go to **EC2 Console** -> **Security Groups**.
2. Review Inbound Rules for **port 22 (SSH)** and **3389 (RDP)**.
3. If Source is `0.0.0.0/0`, **Edit rule**.
4. Change Source to **My IP** or specific corporate VPN CIDR.

### CIS-5.2: No Unrestricted Egress
**Goal:** Restrict outbound calls.
*Note: This often breaks apps if strict. Common failure.*
1. Go to Security Group -> **Outbound rules**.
2. If you see `All traffic` to `0.0.0.0/0`, replace with specific restrictions (e.g., HTTPS 443 only) if verifying strict compliance.

### CIS-5.3: Default Security Group
**Goal:** Remove all rules from the "default" group.
1. In **Security Groups**, search "default".
2. Select the SG named `default`.
3. **Inbound rules** -> Edit -> Delete all.
4. **Outbound rules** -> Edit -> Delete all.
5. Save.
