# terraform/modules/dynamodb/main.tf

# DynamoDB Table for Users
resource "aws_dynamodb_table" "users" {
  name           = "${var.project_name}-${var.environment}-users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  # Global Secondary Index for email lookups
  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-users"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

# DynamoDB Table for URL mappings
resource "aws_dynamodb_table" "urls" {
  name           = "${var.project_name}-${var.environment}-urls"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "short_code"

  attribute {
    name = "short_code"
    type = "S"
  }

  attribute {
    name = "created_by_user"
    type = "S"
  }

  # Global Secondary Index for user-based lookups
  global_secondary_index {
    name            = "user-index"
    hash_key        = "created_by_user"
    projection_type = "ALL"
  }

  # TTL for automatic cleanup of expired URLs
  ttl {
    attribute_name = "expires_at_ttl"
    enabled        = true
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-urls"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

# IAM Policy for DynamoDB access
resource "aws_iam_policy" "dynamodb_access" {
  name        = "${var.project_name}-${var.environment}-dynamodb-access"
  description = "Policy for ECS tasks to access DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.users.arn,
          "${aws_dynamodb_table.users.arn}/index/*",
          aws_dynamodb_table.urls.arn,
          "${aws_dynamodb_table.urls.arn}/index/*"
        ]
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Store DynamoDB configuration in SSM Parameter Store
resource "aws_ssm_parameter" "dynamodb_users_table_name" {
  name  = "/fileshare/${var.environment}/dynamodb_users_table_name"
  type  = "String"
  value = aws_dynamodb_table.users.name

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_ssm_parameter" "dynamodb_urls_table_name" {
  name  = "/fileshare/${var.environment}/dynamodb_urls_table_name"
  type  = "String"
  value = aws_dynamodb_table.urls.name

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_ssm_parameter" "dynamodb_users_table_arn" {
  name  = "/fileshare/${var.environment}/dynamodb_users_table_arn"
  type  = "String"
  value = aws_dynamodb_table.users.arn

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_ssm_parameter" "dynamodb_urls_table_arn" {
  name  = "/fileshare/${var.environment}/dynamodb_urls_table_arn"
  type  = "String"
  value = aws_dynamodb_table.urls.arn

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_ssm_parameter" "dynamodb_policy_arn" {
  name  = "/fileshare/${var.environment}/dynamodb_policy_arn"
  type  = "String"
  value = aws_iam_policy.dynamodb_access.arn

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Enable DynamoDB flag for backend
resource "aws_ssm_parameter" "use_dynamodb" {
  name  = "/fileshare/${var.environment}/use_dynamodb"
  type  = "String"
  value = "true"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}