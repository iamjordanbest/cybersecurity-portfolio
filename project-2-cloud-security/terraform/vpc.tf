# VPC and Network Configuration
# CIS Controls: 4.1 (VPC Flow Logs), 4.2 (Default SG Restrictive)

# ============================================
# VPC
# ============================================
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# ============================================
# CIS-4.1: VPC Flow Logs
# ============================================
# CloudWatch Log Group for Flow Logs
resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/aws/vpc/${var.project_name}-flow-logs"
  retention_in_days = 7  # Retain for 7 days (adjust as needed)

  tags = {
    Name       = "${var.project_name}-flow-logs"
    CISControl = "CIS-4.1"
  }
}

# IAM Role for Flow Logs
resource "aws_iam_role" "flow_logs" {
  name = "${var.project_name}-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "vpc-flow-logs.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "flow_logs" {
  name = "${var.project_name}-flow-logs-policy"
  role = aws_iam_role.flow_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# VPC Flow Logs
resource "aws_flow_log" "main" {
  iam_role_arn    = aws_iam_role.flow_logs.arn
  log_destination = aws_cloudwatch_log_group.flow_logs.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = {
    Name       = "${var.project_name}-flow-log"
    CISControl = "CIS-4.1"
  }
}

# ============================================
# CIS-4.2: Restrictive Default Security Group
# ============================================
# Note: AWS creates a default SG automatically, we'll restrict it via auditor
# Here we create a more restrictive custom SG for actual use

resource "aws_security_group" "restricted" {
  name        = "${var.project_name}-restricted-sg"
  description = "Restricted security group - no inbound from internet"
  vpc_id      = aws_vpc.main.id

  # No ingress rules = deny all inbound
  
  # Allow outbound HTTPS only (for AWS API calls)
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS outbound for AWS APIs"
  }

  tags = {
    Name       = "${var.project_name}-restricted-sg"
    CISControl = "CIS-4.2_CIS-4.3"
  }
}

# ============================================
# Subnets for RDS (Multi-AZ requirement)
# ============================================
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name = "${var.project_name}-private-subnet-a"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = {
    Name = "${var.project_name}-private-subnet-b"
  }
}

# ============================================
# Outputs
# ============================================
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "flow_logs_enabled" {
  description = "VPC Flow Logs status"
  value       = true
}

output "security_group_id" {
  description = "Restricted security group ID"
  value       = aws_security_group.restricted.id
}
