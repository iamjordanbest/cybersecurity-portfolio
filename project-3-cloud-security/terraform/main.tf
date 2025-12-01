# Terraform Configuration for CIS AWS Compliance
# Provider: AWS
# Purpose: Deploy compliant infrastructure for auditing

terraform {
  required_version = ">= 1.6.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure AWS provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "CSPM-Auditor"
      Environment = "Portfolio"
      ManagedBy   = "Terraform"
      Purpose     = "CIS-Compliance-Demo"
    }
  }
}

# Data source: Current AWS account
data "aws_caller_identity" "current" {}

# Data source: Current AWS region
data "aws_region" "current" {}
