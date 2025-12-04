# Terraform Outputs
# Consolidated outputs for evidence collection

output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}

output "terraform_version" {
  description = "Terraform version used"
  value       = "~> 1.6"
}

output "deployment_summary" {
  description = "Summary of deployed CIS-compliant resources"
  value = {
    iam_password_policy_min_length = aws_iam_account_password_policy.strict.minimum_password_length
    cloudtrail_multi_region        = aws_cloudtrail.main.is_multi_region_trail
    cloudtrail_log_validation      = aws_cloudtrail.main.enable_log_file_validation
    cloudtrail_encryption_key      = aws_kms_key.cloudtrail.id
    s3_buckets_created             = 2
    vpc_flow_logs_enabled          = true
    rds_endpoint                   = aws_db_instance.postgresql.endpoint
    rds_port                       = aws_db_instance.postgresql.port
  }
}

# RDS connection details for applications
output "rds_connection_details" {
  description = "RDS PostgreSQL connection details for Grafana"
  value = {
    endpoint = aws_db_instance.postgresql.endpoint
    port     = aws_db_instance.postgresql.port
    database = aws_db_instance.postgresql.db_name
    username = aws_db_instance.postgresql.username
  }
  sensitive = false
}
