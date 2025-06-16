# main.tf for the cognito-user-management module

# -----------------------------------------------------------------------------
# Cognito User Pool and Client
# -----------------------------------------------------------------------------
resource "aws_cognito_user_pool" "this" {
  name = "${var.project_name}-${var.environment}-user-pool"

  # Configure users to sign in with email addresses
  alias_attributes = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  # Configure the Lambda function to trigger after a user confirms their account
  lambda_config {
    post_confirmation = aws_lambda_function.post_confirmation_trigger.arn
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cognito_user_pool_client" "this" {
  name = "${var.project_name}-${var.environment}-app-client"
  user_pool_id = aws_cognito_user_pool.this.id

  # This is for a web-based SPA, so we don't generate a client secret
  generate_secret = false

  # Required for the authentication flow
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]
}

# -----------------------------------------------------------------------------
# Cognito User Groups for Tiers
# -----------------------------------------------------------------------------
resource "aws_cognito_user_group" "free_tier" {
  name          = "free-tier"
  user_pool_id  = aws_cognito_user_pool.this.id
  description   = "Users with free access"
}

resource "aws_cognito_user_group" "premium_tier" {
  name          = "premium-tier"
  user_pool_id  = aws_cognito_user_pool.this.id
  description   = "Users with premium access"
}

# -----------------------------------------------------------------------------
# Lambda Trigger to Add New Users to the Free Tier
# -----------------------------------------------------------------------------

# NOTE: The data "archive_file" block has been removed.

resource "aws_lambda_function" "post_confirmation_trigger" {
  # This now points to a file we expect the CI/CD workflow to create.
  filename         = "${path.module}/add_to_group.zip"
  function_name    = "${var.project_name}-${var.environment}-post-confirmation-trigger"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "add_to_group.handler"
  runtime          = "python3.13"
  # This hash is now calculated directly from the .py file, so Terraform
  # will correctly detect when your Lambda code changes.
  source_code_hash = filebase64sha256("${path.module}/add_to_group.py")

  environment {
    variables = {
      FREE_TIER_GROUP_NAME = "free-tier"
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Allow Cognito service to invoke the Lambda function
resource "aws_lambda_permission" "allow_cognito" {
  statement_id  = "AllowCognitoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.post_confirmation_trigger.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.this.arn
}

# -----------------------------------------------------------------------------
# IAM Role and Policy for the Lambda Function
# -----------------------------------------------------------------------------
resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.project_name}-${var.environment}-lambda-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name        = "${var.project_name}-${var.environment}-lambda-policy"
  description = "IAM policy for Cognito trigger Lambda"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Action = [
          "cognito-idp:AdminAddUserToGroup"
        ],
        Effect   = "Allow",
        Resource = aws_cognito_user_pool.this.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}
