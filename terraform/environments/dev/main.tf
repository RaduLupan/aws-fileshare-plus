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
  desired_count = 0 # Explicitly set to 0 for dev environment's initial deploy

  enable_alb_deletion_protection = false # Set to true for production environments
  alb_health_check_path          = "/"

  alb_listener_http_port  = 80
  alb_listener_https_port = 443

  enable_https_listener     = var.alb_enable_https_listener # Set to true to enable HTTPS, and provide alb_https_certificate_arn
  alb_https_certificate_arn = var.alb_https_certificate_arn # Uncomment and provide if enable_https_listener is true

  s3_uploads_bucket_name_prefix = "${var.project_name}-${var.environment}-uploads"
  log_retention_in_days         = 30
}

# Output relevant values from the modules
output "frontend_cloudfront_url" {
  description = "The URL of the deployed frontend application."
  value       = "http://${module.frontend_app.cloudfront_domain_name}"
}

output "s3_react_bucket_name" {
  description = "The S3 bucket name for the React frontend."
  value       = module.frontend_app.s3_bucket_name
}

/* output "backend_alb_url" {
  description = "The URL of the backend ALB."
  value       = "http://${module.backend_app.alb_dns_name}" # Use http for now, update to https when ALB has certificate
}
 */
output "s3_uploads_bucket_name" {
  description = "The S3 bucket name for file uploads."
  value       = module.backend_app.uploads_s3_bucket_name
}