# security_groups.tf

# Security group for the Application Load Balancer (ALB)
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Security group for the Application Load Balancer"
  vpc_id      = module.vpc.vpc_id

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Allow inbound HTTP traffic to ALB from anywhere
resource "aws_vpc_security_group_ingress_rule" "alb_allow_http" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = var.alb_http_port
  ip_protocol       = "tcp"
  to_port           = var.alb_http_port
  description       = "Allow HTTP from internet"
}

# Allow inbound HTTPS traffic to ALB from anywhere (even if not used initially, define for future)
resource "aws_vpc_security_group_ingress_rule" "alb_allow_https" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = var.alb_https_port
  ip_protocol       = "tcp"
  to_port           = var.alb_https_port
  description       = "Allow HTTPS from internet"
}

# Allow all outbound traffic from the ALB
resource "aws_vpc_security_group_egress_rule" "alb_allow_all_outbound" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1" # Allows all protocols and ports
  description       = "Allow all outbound traffic"
}


# Security group for the ECS Fargate tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  description = "Security group for ECS Fargate tasks"
  vpc_id      = module.vpc.vpc_id

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecs-tasks-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Allow inbound traffic to ECS tasks from the ALB security group
resource "aws_vpc_security_group_ingress_rule" "ecs_tasks_allow_from_alb" {
  security_group_id            = aws_security_group.ecs_tasks.id
  from_port                    = var.ecs_service_port
  ip_protocol                  = "tcp"
  to_port                      = var.ecs_service_port
  referenced_security_group_id = aws_security_group.alb.id # Only allow traffic from the ALB
  description                  = "Allow inbound from ALB SG on ECS service port"
}

# Allow all outbound traffic from ECS tasks (e.g., to S3, external APIs, etc.)
resource "aws_vpc_security_group_egress_rule" "ecs_tasks_allow_all_outbound" {
  security_group_id = aws_security_group.ecs_tasks.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1" # Allows all protocols and ports
  description       = "Allow all outbound traffic"
}