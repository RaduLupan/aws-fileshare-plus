# alb.tf

# Create an Application Load Balancer (ALB)
resource "aws_lb" "this" {
  name               = "${var.project_name}-${var.environment}-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids # ALB typically lives in public subnets

  enable_deletion_protection = var.enable_alb_deletion_protection

  tags = {
    Name        = "${var.project_name}-${var.environment}-lb"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Create a Target Group for the ALB
resource "aws_lb_target_group" "this" {
  name        = "${var.project_name}-${var.environment}-tg"
  port        = var.container_port # Port your Flask container listens on
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip" # Required for Fargate

  health_check {
    enabled             = true
    path                = var.alb_health_check_path
    protocol            = "HTTP"
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200" # Expect HTTP 200 for a healthy target
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-tg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Create an HTTP listener for the ALB
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = var.alb_listener_http_port
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-http-listener"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Conditionally create an HTTPS listener for the ALB
resource "aws_lb_listener" "https" {
  count             = var.enable_https_listener ? 1 : 0 # Only create if enabled
  load_balancer_arn = aws_lb.this.arn
  port              = var.alb_listener_https_port
  protocol          = "HTTPS"

  ssl_policy      = "ELBSecurityPolicy-2016-08" # You might want a newer policy like "ELBSecurityPolicy-TLS13-1-2-2021-04"
  certificate_arn = var.alb_https_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-https-listener"
    Environment = var.environment
    Project     = var.project_name
  }
}