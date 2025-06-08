# terraform/environments/dev/main.tf

provider "aws" {
  region = var.aws_region
}

# Define your remote backend here
# terraform {
#   backend "s3" {
#     bucket         = "your-dev-terraform-state-bucket" # Create this bucket manually once
#     key            = "frontend/state"
#     region         = "us-east-1"
#     dynamodb_table = "your-dev-terraform-state-lock" # Create this DynamoDB table manually once
#     encrypt        = true
#   }
# }

# Call the network module first to create VPC, subnets, and other networking resources
module "network" {
  source = "../../modules/network" # Path to your network module

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = var.aws_region
  vpc_cidr           = "10.0.0.0/16"                # Or use a variable if you want this to be configurable per env
  availability_zones = ["us-east-1a", "us-east-1b"] # Ensure this matches your region
  # public_subnet_cidrs and private_subnet_cidrs can be left empty to use defaults
  enable_nat_gateway = true
  single_nat_gateway = true
  ecs_service_port   = 5000
  alb_http_port      = 80
  alb_https_port     = 443
}

# Call the frontend module
module "frontend_app" {
  source = "../../modules/s3-cloudfront-frontend" # Path to your module

  # Pass variables to the module
  environment            = var.environment
  bucket_name_prefix     = "my-file-share-dev" # Unique prefix for this environment
  cloudfront_comment     = "Dev CloudFront distribution for My File Share"
  viewer_protocol_policy = "allow-all" # For dev testing, change to "redirect-to-https" for production env

  # If you decide to use a custom domain later for dev:
  # custom_domain_name   = "dev.example.com"
  # acm_certificate_arn  = "arn:aws:acm:us-east-1:123456789012:certificate/abc-123"
}

# Call the backend module
module "backend_app" {
  source = "../../modules/ecs-flask-backend"

  project_name                   = var.project_name
  environment                    = var.environment
  aws_region                     = var.aws_region # Pass the region to backend module
  vpc_id                         = module.network.vpc_id
  public_subnet_ids              = module.network.public_subnet_ids
  private_subnet_ids             = module.network.private_subnet_ids
  alb_security_group_id          = module.network.alb_security_group_id
  ecs_tasks_security_group_id    = module.network.ecs_tasks_security_group_id
  container_port                 = 5000
  cpu                            = 256
  memory                         = 512
  desired_count                  = 0 # Explicitly set to 0 for dev environment's initial deploy
  enable_alb_deletion_protection = false # Set to true for production environments
  alb_health_check_path          = "/"
  alb_listener_http_port         = 80
  enable_https_listener          = false # Set to true to enable HTTPS, and provide alb_https_certificate_arn
  alb_listener_https_port        = 443
  # alb_https_certificate_arn   = "arn:aws:acm:us-east-2:123456789012:certificate/abc-123" # Uncomment and provide if enable_https_listener is true
  s3_uploads_bucket_name_prefix = "${var.project_name}-${var.environment}-uploads"
  log_retention_in_days         = 30
}

# Output relevant values from the modules
output "frontend_url" {
  description = "The URL of the deployed frontend application."
  value       = "http://${module.frontend_app.cloudfront_domain_name}"
}

output "react_s3_bucket_name" {
  description = "The S3 bucket name for the React frontend."
  value       = module.frontend_app.s3_bucket_name
}

output "backend_alb_url" {
  description = "The URL of the backend ALB."
  value       = "http://${module.backend_app.alb_dns_name}" # Use http for now, update to https when ALB has certificate
}

output "s3_uploads_bucket_name" {
  description = "The S3 bucket name for file uploads."
  value       = module.backend_app.uploads_s3_bucket_name
}
