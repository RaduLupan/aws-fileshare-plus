# terraform/environments/dev/main.tf

provider "aws" {
  region = var.aws_region
}

# Call the network module first to create VPC, subnets, and other networking resources
module "network" {
  source = "../../modules/network" # Path to your network module

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = var.aws_region
  vpc_cidr           = "10.0.0.0/16"          # Or use a variable if you want this to be configurable per env
  availability_zones = var.availability_zones # Use the availability zones defined in variables.tf
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
  bucket_name_prefix     = var.project_name
  cloudfront_comment     = "${var.environment} CloudFront distribution for ${var.project_name} frontend"
  viewer_protocol_policy = var.cloudfront_viewer_protocol_policy # For dev testing, change to "redirect-to-https" for production env

  # If you decide to use a custom domain later for dev:
  custom_domain_name  = var.cloudfront_custom_domain_name
  acm_certificate_arn = var.cloudfront_https_certificate_arn

  # Pass backend ALB details for CloudFront proxying
  backend_alb_dns_name = module.backend_app.alb_dns_name # the raw ALB DNS name. var.alb_custom_domain_name also works if you want to use a custom domain for the ALB  
  alb_http_port        = var.alb_http_port_for_frontend  # From a new variable in dev/variables.tf
  alb_https_port       = var.alb_https_port_for_frontend # From a new variable in dev/variables.tf
}

# Call the backend module
module "backend_app" {
  source = "../../modules/ecs-flask-backend"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region # Pass the region to backend module

  vpc_id                = module.network.vpc_id
  public_subnet_ids     = module.network.public_subnet_ids
  private_subnet_ids    = module.network.private_subnet_ids
  alb_security_group_id = module.network.alb_security_group_id

  ecr_repository_url = "481509955802.dkr.ecr.us-east-2.amazonaws.com/file-sharing-app-radulupan-test" # Update with your ECR repository URL
  image_tag          = "dev"

  ecs_tasks_security_group_id = module.network.ecs_tasks_security_group_id
  container_port              = 5000

  cpu           = 256
  memory        = 512
  desired_count = 1 # Start 1 task for the backend service

  enable_alb_deletion_protection = false # Set to true for production environments
  alb_health_check_path          = "/"

  alb_listener_http_port  = 80
  alb_listener_https_port = 443

  enable_https_listener     = var.alb_enable_https_listener # Set to true to enable HTTPS, and provide alb_https_certificate_arn
  alb_https_certificate_arn = var.alb_https_certificate_arn # Uncomment and provide if enable_https_listener is true

  s3_uploads_bucket_name_prefix = "${var.project_name}-${var.environment}-uploads"
  log_retention_in_days         = 30
  # Add this line to connect the modules:
  cognito_user_pool_id = module.cognito.user_pool_id
  cognito_client_id    = module.cognito.user_pool_client_id

  # Configure file retention period for S3 lifecycle policy
  file_retention_days = var.file_retention_days
  
  # Pass CloudFront domain for short URL construction
  frontend_domain = var.cloudfront_custom_domain_name != "" ? var.cloudfront_custom_domain_name : module.frontend_app.cloudfront_domain_name
  
  # Pass DynamoDB policy ARN for database access
  dynamodb_policy_arn = module.dynamodb.dynamodb_policy_arn
}

module "cognito" {
  source = "../../modules/cognito-user-management"

  project_name = var.project_name
  environment  = var.environment
  
  # Pass SES configuration for custom email (only if SES is enabled)
  ses_email_identity_arn = module.ses_email.ses_enabled ? module.ses_email.domain_identity_arn : null
  from_email_address     = module.ses_email.ses_enabled ? module.ses_email.from_email_address : null
  reply_to_email_address = module.ses_email.ses_enabled ? module.ses_email.from_email_address : null
}

# Call the SES email module for better email deliverability
module "ses_email" {
  source = "../../modules/ses-email"

  project_name       = var.project_name
  environment        = var.environment
  domain_name        = var.ses_domain_name        # Will be set in dev.tfvars
  from_email_address = var.ses_from_email_address # Will be set in dev.tfvars
}

# Call the DynamoDB module for database tables
module "dynamodb" {
  source = "../../modules/dynamodb"

  project_name                  = var.project_name
  environment                   = var.environment
  aws_region                    = var.aws_region
  enable_point_in_time_recovery = var.enable_point_in_time_recovery
}

# Output relevant values from the modules
output "frontend_cloudfront_url" {
  description = "The URL of the deployed frontend application."
  value       = "https://${module.frontend_app.cloudfront_domain_name}"
}

output "s3_react_bucket_name" {
  description = "The S3 bucket name for the React frontend."
  value       = module.frontend_app.s3_bucket_name
}

output "backend_alb_url" {
  description = "The URL of the backend ALB."
  value       = var.alb_enable_https_listener ? "https://${var.alb_custom_domain_name}" : "http://${module.backend_app.alb_dns_name}"
}

output "s3_uploads_bucket_name" {
  description = "The S3 bucket name for file uploads."
  value       = module.backend_app.uploads_s3_bucket_name
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster."
  value       = module.backend_app.ecs_cluster_name
}

output "ecs_service_name" {
  description = "The name of the ECS service."
  value       = module.backend_app.ecs_service_name
}

output "cloudfront_distribution_id" {
  description = "The ID of the CloudFront distribution."
  value       = module.frontend_app.cloudfront_distribution_id
}

output "cloudfront_custom_domain_url" {
  description = "The custom domain URL for the CloudFront distribution."
  # It's important to prepend "https://"
  value       = "https://${var.cloudfront_custom_domain_name}" # Assuming you pass the domain as a variable
}

output "user_pool_id" {
  description = "The ID of the Cognito User Pool."
  value       = module.cognito.user_pool_id
}

output "user_pool_client_id" {
  description = "The ID of the Cognito User Pool Client."
  value       = module.cognito.user_pool_client_id
}

# SES Email Configuration Outputs
output "ses_domain_verification_token" {
  description = "The SES domain verification token for DNS setup (null if no custom domain)"
  value       = module.ses_email.domain_verification_token
}

output "ses_dkim_tokens" {
  description = "The SES DKIM tokens for DNS setup (JSON string, empty array if no custom domain)"
  value       = jsonencode(module.ses_email.dkim_tokens)
}

output "ses_from_email" {
  description = "The configured from email address (null if no custom domain)"
  value       = module.ses_email.from_email_address
}

output "ses_enabled" {
  description = "Whether custom SES domain is enabled"
  value       = module.ses_email.ses_enabled
}

output "ses_domain_name" {
  description = "The SES domain name (null if no custom domain)"
  value       = module.ses_email.domain_name
}

# DynamoDB Outputs
output "dynamodb_users_table_name" {
  description = "The name of the DynamoDB users table"
  value       = module.dynamodb.users_table_name
}

output "dynamodb_urls_table_name" {
  description = "The name of the DynamoDB URLs table"
  value       = module.dynamodb.urls_table_name
}

output "dynamodb_users_table_arn" {
  description = "The ARN of the DynamoDB users table"
  value       = module.dynamodb.users_table_arn
}

output "dynamodb_urls_table_arn" {
  description = "The ARN of the DynamoDB URLs table"
  value       = module.dynamodb.urls_table_arn
}

output "dynamodb_policy_arn" {
  description = "The ARN of the IAM policy for DynamoDB access"
  value       = module.dynamodb.dynamodb_policy_arn
}