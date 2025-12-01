# S3 Buckets for CloudTrail
# CIS Controls: 2.1.1 (S3 Encryption), 2.1.2 (Versioning), 2.1.4 (Block Public Access)

# ============================================
# S3 Bucket for CloudTrail Logs
# ============================================
resource "aws_s3_bucket" "cloudtrail_logs" {
  bucket = "${var.project_name}-cloudtrail-logs-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name       = "${var.project_name}-cloudtrail-logs"
    CISControl = "CIS-2.3"
    Purpose    = "CloudTrail audit logs"
  }
}

# CIS-2.1.2: Enable versioning
resource "aws_s3_bucket_versioning" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

# CIS-2.1.1: Enable encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CIS-2.1.4: Block all public access
resource "aws_s3_bucket_public_access_block" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bucket policy to allow CloudTrail to write logs
resource "aws_s3_bucket_policy" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail_logs.arn
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail_logs.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

# ============================================
# S3 Bucket for Compliance Evidence
# ============================================
resource "aws_s3_bucket" "compliance_evidence" {
  bucket = "${var.project_name}-compliance-evidence-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name       = "${var.project_name}-compliance-evidence"
    Purpose    = "Compliance assessment evidence storage"
  }
}

# CIS-2.1.2: Enable versioning
resource "aws_s3_bucket_versioning" "compliance_evidence" {
  bucket = aws_s3_bucket.compliance_evidence.id

  versioning_configuration {
    status = "Enabled"
  }
}

# CIS-2.1.1: Enable encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "compliance_evidence" {
  bucket = aws_s3_bucket.compliance_evidence.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CIS-2.1.4: Block all public access
resource "aws_s3_bucket_public_access_block" "compliance_evidence" {
  bucket = aws_s3_bucket.compliance_evidence.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================
# Outputs
# ============================================
output "cloudtrail_bucket_name" {
  description = "S3 bucket name for CloudTrail logs"
  value       = aws_s3_bucket.cloudtrail_logs.id
}

output "cloudtrail_bucket_arn" {
  description = "S3 bucket ARN for CloudTrail logs"
  value       = aws_s3_bucket.cloudtrail_logs.arn
}

output "evidence_bucket_name" {
  description = "S3 bucket name for compliance evidence"
  value       = aws_s3_bucket.compliance_evidence.id
}
