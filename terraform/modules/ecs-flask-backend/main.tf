# terraform/modules/ecs-flask-backend/main.tf

# Create an ECS cluster
resource "aws_ecs_cluster" "this" {
  name = "${var.project_name}-${var.environment}-cluster"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# NOTE: The aws_ecr_repository resource has been removed from this module.
# The repository is now considered a global resource, managed outside of this module.

# Create the ECS task definition
resource "aws_ecs_task_definition" "flask" {
  family                   = "${var.project_name}-${var.environment}-flask-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory

  execution_role_arn = aws_iam_role.ecs_task_execution.arn # Role for ECS agent
  task_role_arn      = aws_iam_role.flask_app_task.arn     # Role for your application container

  container_definitions = jsonencode([{
    name      = "${var.project_name}-${var.environment}-flask-container"
    # IMPORTANT: The image is now composed from variables passed into the module.
    # This decouples the module from the ECR repository and the image tag.
    image     = "${var.ecr_repository_url}:${var.image_tag}"
    essential = true
    portMappings = [{
      containerPort = var.container_port
      hostPort      = var.container_port
    }]
    environment = [ # Add this block for environment variables
      {
        name  = "S3_BUCKET_NAME"
        value = aws_s3_bucket.uploads_backend.bucket # Reference the bucket name here
      },
      {
        name  = "AWS_REGION" # Also good to pass the region
        value = var.aws_region
      },      # --- ADD THIS NEW BLOCK ---
      {
        name  = "COGNITO_USER_POOL_ID"
        value = var.cognito_user_pool_id # Use the new input variable
      },
      {
        name  = "COGNITO_CLIENT_ID"
        value = var.cognito_client_id # Use the new input variable
      },
      {
        name  = "FRONTEND_DOMAIN"
        value = var.frontend_domain # CloudFront domain for short URL construction
      }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.ecs_log_group.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
  }])

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Create the ECS service
resource "aws_ecs_service" "this" {
  name            = "${var.project_name}-${var.environment}-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.flask.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  health_check_grace_period_seconds = 60
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  network_configuration {
    assign_public_ip = false
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_tasks_security_group_id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = "${var.project_name}-${var.environment}-flask-container"
    container_port   = var.container_port
  }

  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"

  # CORRECT FIX for depends_on with conditional resources
  # NOTE: The dependency on aws_ecr_repository.flask_app has been removed.
  depends_on = [
    aws_lb_listener.http,
    aws_lb_listener.https, # Refer to the resource, even if its count is 0
  ]

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}
