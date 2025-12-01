# KMS Key for Encryption
# CIS Controls: 2.7 (CloudTrail Encryption)

# ============================================
# KMS Key for CloudTrail Log Encryption
# ============================================
resource "aws_kms_key" "cloudtrail" {
  description             = "KMS key for CloudTrail log encryption (CIS-2.7)"
  deletion_window_in_days = 10
  enable_key_rotation     = true  # Automatic yearly key rotation

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudTrail to encrypt logs"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = [
          "kms:GenerateDataKey*",
          "kms:DecryptDataKey"
        ]
        Resource = "*"
        Condition = {
          StringLike = {
            "kms:EncryptionContext:aws:cloudtrail:arn" = "arn:aws:cloudtrail:*:${data.aws_caller_identity.current.account_id}:trail/*"
          }
        }
      },
      {
        Sid    = "Allow CloudTrail to describe key"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "kms:DescribeKey"
        Resource = "*"
      }
    ]
  })

  tags = {
    Name      = "${var.project_name}-cloudtrail-kms"
    CISControl = "CIS-2.7"
  }
}

resource "aws_kms_alias" "cloudtrail" {
  name          = "alias/${var.project_name}-cloudtrail"
  target_key_id = aws_kms_key.cloudtrail.key_id
}

# ============================================
# Outputs
# ============================================
output "kms_key_id" {
  description = "KMS key ID for CloudTrail encryption"
  value       = aws_kms_key.cloudtrail.key_id
}

output "kms_key_arn" {
  description = "KMS key ARN for CloudTrail encryption"
  value       = aws_kms_key.cloudtrail.arn
}
