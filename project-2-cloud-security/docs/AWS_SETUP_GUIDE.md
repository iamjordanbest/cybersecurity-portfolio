# AWS IAM Admin User Setup Guide

## ⚠️ **Important Security Principle**

**Never use your root account for daily work.** Root has unlimited permissions and no audit trail of who did what. Instead, create an IAM admin user with MFA.

---

## 📋 **Step-by-Step IAM Admin Setup**

### **Step 1: Enable MFA on Root Account** (CIS-1.4 requirement)

1. In AWS Console, click your account name (top right) → **Security credentials**
2. Scroll to **Multi-factor authentication (MFA)**
3. Click **Assign MFA device**
4. Choose **Authenticator app** (use Microsoft Authenticator, Google Authenticator, or Authy)
5. Scan QR code with your phone app
6. Enter two consecutive MFA codes
7. Click **Assign MFA**

✅ **You just passed CIS-1.4!** Your first compliance control is done.

---

### **Step 2: Create IAM Admin User**

1. In AWS Console search bar, type **IAM** and select the service
2. In left sidebar, click **Users**
3. Click **Create user** button

**User details:**
- User name: `admin-user` (or your preferred name)
- ✅ Check **"Provide user access to the AWS Management Console"**
- Select **"I want to create an IAM user"**
- Custom password: Create a strong password (14+ chars for CIS-1.12)
- ✅ **Uncheck** "Users must create a new password at next sign-in" (you already made it strong)
- Click **Next**

**Set permissions:**
- Select **"Attach policies directly"**
- Search for and check: **AdministratorAccess**
  - This gives full AWS permissions (we'll restrict later if needed)
- Click **Next**

**Review and create:**
- Review settings
- Click **Create user**

**Save credentials:**
- On success screen, you'll see:
  - Console sign-in URL (bookmark this!)
  - Username: `admin-user`
  - Console password: (your password)
- Click **Download .csv** to save these credentials
- Click **Return to users list**

---

### **Step 3: Enable MFA for Admin User**

1. In **Users** list, click on your new `admin-user`
2. Click **Security credentials** tab
3. Scroll to **Multi-factor authentication (MFA)**
4. Click **Assign MFA device**
5. Device name: `admin-user-mfa`
6. MFA device: **Authenticator app**
7. Scan QR code with your phone (can use same auth app as root)
8. Enter two consecutive codes
9. Click **Assign MFA**

✅ **Admin user is now MFA-protected!**

---

### **Step 4: Create Access Keys for CLI**

1. Still in `admin-user` → **Security credentials** tab
2. Scroll to **Access keys**
3. Click **Create access key**
4. Use case: Select **"Command Line Interface (CLI)"**
5. ✅ Check the confirmation box
6. Click **Next**
7. Description tag (optional): `Terraform and boto3 automation`
8. Click **Create access key**

**Save your keys:**
```
Access key ID: AKIA... (from Step 4)
Secret access key: wJalrXUtn... (from Step 4)

⚠️ **CRITICAL:** Download the CSV or copy these now. You can't see the secret again!

---

### **Step 5: Sign Out of Root, Sign In as Admin User**

1. Click account dropdown (top right) → **Sign Out**
2. Go to the console sign-in URL from Step 2 (or https://console.aws.amazon.com/)
3. Sign in as:
   - **IAM user**: `admin-user`
   - **Password**: (your password)
4. Enter MFA code when prompted

✅ **You're now working as IAM admin (best practice)**

---

## 🎯 **What You Just Accomplished**

| Control | Status | Evidence |
|---------|--------|----------|
| CIS-1.4 | ✅ PASS | Root has MFA enabled |
| CIS-1.16 | ✅ PASS | Using IAM user, not root |
| Best Practice | ✅ PASS | Admin user has MFA |

---

## 📝 **Save These for Later**

You'll need these when configuring AWS CLI:

```
AWS Access Key ID: AKIA... (from Step 4)
AWS Secret Access Key: wJalrXUtn... (from Step 4)
Default region: us-east-1 (recommended, or choose your preference)
```

---

## ⚠️ **Security Reminder**

- **Never commit AWS keys to Git!** (We'll add them to .gitignore)
- **Never share your secret access key**
- **Root account**: Use only for account recovery, not daily work
- **Admin user**: This is your daily work account

---

**Next:** Configure AWS CLI with your new access keys
