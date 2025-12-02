# Git Installation Guide for Windows

## Current Status: ❌ Git Not Installed

Git is not currently installed on your system. Let's fix that!

---

## 🔽 **Method 1: Download Official Installer (Recommended)**

### **Step 1: Download Git**
1. Go to: **https://git-scm.com/download/win**
2. Click **"Click here to download"** (64-bit version)
3. Save the file (Git-2.43.0-64-bit.exe or similar)

### **Step 2: Run Installer**
1. Double-click the downloaded `.exe` file
2. **Important settings during installation:**
   - ✅ Use Visual Studio Code as Git's default editor (or choose your preference)
   - ✅ "Git from the command line and also from 3rd-party software" (Default)
   - ✅ "Use bundled OpenSSH"
   - ✅ "Use the OpenSSL library"
   - ✅ "Checkout Windows-style, commit Unix-style line endings" (Recommended)
   - ✅ "Use MinTTY" (Default terminal)
   - ✅ "Default (fast-forward or merge)"
   - ✅ "Git Credential Manager"
   - ✅ "Enable file system caching"
   - ✅ "Enable symbolic links"

3. Click **Next** through all screens, then **Install**
4. Click **Finish**

### **Step 3: Verify Installation**
Open a **NEW** PowerShell window (important - must be new to reload PATH):
```powershell
git --version
```

Expected output:
```
git version 2.43.0.windows.1
```

---

## 🔽 **Method 2: Install via Chocolatey (Alternative)**

If you have Chocolatey package manager:
```powershell
# Run as Administrator
choco install git -y
```

Then restart your terminal and verify:
```powershell
git --version
```

---

## ⚙️ **Configure Git (After Installation)**

Set your name and email (required for commits):

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Verify configuration:
```powershell
git config --global --list
```

---

## 🎯 **Initialize Your Portfolio Repository**

Once Git is installed, navigate to your portfolio:

```powershell
cd C:\Users\19738\Desktop\cybersecurity-portfolio

# Initialize Git repository
git init

# Check status
git status

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Portfolio projects setup"
```

---

## 📝 **Create .gitignore (Important!)**

Make sure you have a `.gitignore` in the root of `cybersecurity-portfolio`:

```
# AWS Credentials (NEVER commit these!)
*.csv
.aws/
aws_credentials.txt
**/aws_access_keys.txt

# Terraform
**/terraform/.terraform/
**/terraform/*.tfstate
**/terraform/*.tfstate.backup
**/terraform/.terraform.lock.hcl

# Python
__pycache__/
*.pyc
*.pyo
**/venv/
**/.env

# Data
**/data/*.db
**/evidence/*.png
**/evidence/*.json

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

---

## ✅ **Verification Checklist**

After installation:
- [ ] `git --version` shows version 2.x
- [ ] `git config --global user.name` shows your name
- [ ] `git config --global user.email` shows your email
- [ ] `.gitignore` exists in portfolio root
- [ ] Successfully ran `git init` in portfolio directory

---

## 🚨 **Common Issues**

**"git: command not found" after install**
- Solution: **Close and reopen** your terminal (PATH needs to reload)

**"Please tell me who you are" error**
- Solution: Run the `git config` commands above

**Can't find Git installer**
- Direct link: https://github.com/git-for-windows/git/releases/latest

---

**Next:** After Git is installed, you can commit your Project 3 code and push to GitHub!
