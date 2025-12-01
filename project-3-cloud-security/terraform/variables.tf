# Input variables for Terraform configuration

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "cspm-auditor"
}

variable "enable_mfa_delete" {
  description = "Enable MFA delete on S3 buckets (requires root account to configure)"
  type        = bool
  default     = false  # Set to true after manual MFA setup
}
