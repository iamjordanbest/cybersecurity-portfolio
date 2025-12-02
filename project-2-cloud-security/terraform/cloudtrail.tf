# CloudTrail Configuration
# CIS Controls: 2.1 (Multi-Region), 2.2 (Log Validation), 2.7 (Encryption)

# ============================================
# CloudTrail Multi-Region Trail
# ============================================
resource "aws_cloudtrail" "main" {
  name                          = "${var.project_name}-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail_logs.id
  include_global_service_events = true
  is_multi_region_trail         = true  # CIS-2.1: Multi-region trail
  enable_log_file_validation    = true  # CIS-2.2: Log file validation
  kms_key_id                    = aws_kms_key.cloudtrail.arn  # CIS-2.7: Encryption

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::"]  # Log all S3 object-level events
    }
  }

  tags = {
    Name       = "${var.project_name}-cloudtrail"
    CISControl = "CIS-2.1_CIS-2.2_CIS-2.7"
  }

  depends_on = [
    aws_s3_bucket_policy.cloudtrail_logs
  ]
}

# ============================================
# Outputs
# ============================================
output "cloudtrail_arn" {
  description = "CloudTrail ARN"
  value       = aws_cloudtrail.main.arn
}

output "cloudtrail_name" {
  description = "CloudTrail name"
  value       = aws_cloudtrail.main.name
}

output "cloudtrail_is_multi_region" {
  description = "Is CloudTrail multi-region enabled"
  value       = aws_cloudtrail.main.is_multi_region_trail
}

output "cloudtrail_log_validation_enabled" {
  description = "Is log file validation enabled"
  value       = aws_cloudtrail.main.enable_log_file_validation
}
