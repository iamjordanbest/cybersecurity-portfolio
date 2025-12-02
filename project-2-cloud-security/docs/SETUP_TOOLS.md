# Week 1 Setup: Install Tools & Configure AWS

## 📦 **Tool Installation**

### **1. Install AWS CLI v2**

**Windows:**
```powershell
# Download MSI installer
# Visit: https://awscli.amazonaws.com/AWSCLIV2.msi
# Run the installer

# Verify installation
aws --version
# Expected: aws-cli/2.x.x Python/3.x.x Windows/...
```

**Or via PowerShell (alternative):**
```powershell
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

---

### **2. Install Terraform**

**Windows (using Chocolatey - recommended):**

If you have Chocolatey:
```powershell
choco install terraform
```

**Or Manual Install:**
1. Download from: https://w/yww.terraform.io/downloads
2. Choose **Windows AMD64** (ZIP file)
3. Extract `terraform.exe` to `C:\terraform`
4. Add to PATH:
   ```powershell
   $env:Path += ";C:\terraform"
   setx PATH "$env:Path;C:\terraform"
   ```

**Verify:**
```powershell
terraform --version
# Expected: Terraform v1.6.x or higher
```

---

## 🔧 **Configure AWS CLI**

After creating your IAM admin user (see AWS_SETUP_GUIDE.md):

```powershell
# Configure AWS credentials
aws configure

# You'll be prompted for:
# AWS Access Key ID: AKIA... (from IAM access key)
# AWS Secret Access Key: wJalrXUtn... (from IAM access key)
# Default region name: us-east-1 (recommended)
# Default output format: json
```

**Test your configuration:**
```powershell
# This should return your IAM user info
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDA...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/admin-user"
# }
```

✅ **If you see your user info, AWS CLI is configured correctly!**

---

## 📁 **Project Structure Setup**

From `project-3-cloud-security` directory:

```powershell
# Create directory structure
New-Item -ItemType Directory -Path terraform -Force
New-Item -ItemType Directory -Path auditors -Force
New-Item -ItemType Directory -Path models -Force
New-Item -ItemType Directory -Path data -Force
New-Item -ItemType Directory -Path evidence -Force
New-Item -ItemType Directory -Path tableau -Force
New-Item -ItemType Directory -Path tests -Force

# Create .gitignore
@"
# AWS credentials
*.csv
.aws/
aws_credentials.txt

# Terraform
terraform/.terraform/
terraform/*.tfstate
terraform/*.tfstate.backup
terraform/.terraform.lock.hcl

# Python
__pycache__/
*.pyc
*.pyo
venv/
.env

# Data
data/*.db
evidence/*.png
evidence/*.json

# IDE
.vscode/
.idea/
"@ | Out-File -FilePath .gitignore -Encoding utf8
```

---

## 🐍 **Python Environment Setup**

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate

# You should see (venv) in your prompt now
```

---

## ✅ **Verification Checklist**

Run these commands to verify everything is ready:

```powershell
# 1. AWS CLI configured
aws sts get-caller-identity
# Should show your IAM user

# 2. Terraform installed
terraform --version
# Should show v1.6.x+

# 3. Python virtual environment
python --version
# Should show Python 3.11+

# 4. In correct directory
pwd
# Should end with: project-3-cloud-security
```

**All good?** You're ready to deploy Terraform infrastructure! 🚀

---

## 🎯 **Next Steps**

1. Review the Terraform configs I'm generating
2. Run `terraform init` to initialize
3. Run `terraform plan` to preview changes
4. Run `terraform apply` to deploy to AWS
