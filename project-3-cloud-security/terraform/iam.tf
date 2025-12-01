# IAM Configuration
# CIS Controls: 1.12 (Password Policy), 1.16 (Policies on Groups)

# ============================================
# CIS-1.12: IAM Password Policy
# ============================================
resource "aws_iam_account_password_policy" "strict" {
  minimum_password_length        = 14  # CIS requirement: >= 14
  require_lowercase_characters   = true
  require_uppercase_characters   = true
  require_numbers                = true
  require_symbols                = true
  allow_users_to_change_password = true
  max_password_age               = 90   # Passwords expire after 90 days
  password_reuse_prevention      = 24   # Can't reuse last 24 passwords
}

# ============================================
# CIS-1.16: IAM Group for Permissions
# ============================================
resource "aws_iam_group" "security_auditors" {
  name = "${var.project_name}-security-auditors"
  path = "/"
}

# Attach read-only security audit policy
resource "aws_iam_group_policy_attachment" "security_audit" {
  group      = aws_iam_group.security_auditors.name
  policy_arn = "arn:aws:iam::aws:policy/SecurityAudit"
}

# ============================================
# Outputs for Evidence Collection
# ============================================
output "iam_password_policy" {
  description = "IAM password policy configuration"
  value = {
    min_length         = aws_iam_account_password_policy.strict.minimum_password_length
    require_symbols    = aws_iam_account_password_policy.strict.require_symbols
    require_numbers    = aws_iam_account_password_policy.strict.require_numbers
    max_age            = aws_iam_account_password_policy.strict.max_password_age
    reuse_prevention   = aws_iam_account_password_policy.strict.password_reuse_prevention
  }
}
