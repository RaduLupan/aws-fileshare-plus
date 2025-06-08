# cloudwatch.tf

# Define the CloudWatch Log Group for ECS tasks
resource "aws_cloudwatch_log_group" "ecs_log_group" {
  name              = "/ecs/${var.project_name}/${var.environment}/flask-app"
  retention_in_days = var.log_retention_in_days # Controlled by variable

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}