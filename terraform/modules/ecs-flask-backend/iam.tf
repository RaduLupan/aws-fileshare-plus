# iam.tf

# IAM role for ECS task execution (pulling images, basic logs)
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-${var.environment}-ecs-task-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach the AmazonECSTaskExecutionRolePolicy managed policy
resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
  role       = aws_iam_role.ecs_task_execution.name
}

# IAM role for the Flask application task (for app-specific permissions like S3 access)
resource "aws_iam_role" "flask_app_task" {
  name = "${var.project_name}-${var.environment}-flask-app-task-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Define the policy containing only the S3 permissions needed by the application
resource "aws_iam_policy" "flask_app_s3_access" {
  name        = "${var.project_name}-${var.environment}-flask-s3-access-policy"
  description = "Allows Flask app task to access specific S3 bucket for uploads"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "AllowS3Access",
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket", # Required for listing objects, potentially by boto3
          "s3:DeleteObject" # Add if your app needs to delete files
        ]
        Resource = [
          aws_s3_bucket.uploads_backend.arn,
          "${aws_s3_bucket.uploads_backend.arn}/*"
        ]
      },
      {
        Sid: "AllowCognitoGroupManagement",
        Effect: "Allow",
        Action: [
          "cognito-idp:AdminAddUserToGroup",
          "cognito-idp:AdminRemoveUserFromGroup"
      ],
        Resource: "arn:aws:cognito-idp:us-east-2:481509955802:userpool/*"
    }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach the S3 access policy to the Flask application task role
resource "aws_iam_role_policy_attachment" "flask_app_s3_policy_attachment" {
  policy_arn = aws_iam_policy.flask_app_s3_access.arn
  role       = aws_iam_role.flask_app_task.name
}