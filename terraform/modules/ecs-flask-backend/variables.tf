# variables.tf

#----------------------------------------------------------------------------
# REQUIRED PARAMETERS: You must provide a value for each of these parameters.
#----------------------------------------------------------------------------

variable "project_name" {
  description = "The name of your project, used as a prefix for resources."
  type        = string
}

variable "environment" {
  description = "The environment name (e.g., dev, staging, prod)."
  type        = string
}

variable "aws_region" {
  description = "The AWS region where resources are deployed."
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC where the ECS service will run."
  type        = string
}

variable "public_subnet_ids" {
  description = "A list of public subnet IDs for the ALB."
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "A list of private subnet IDs for the ECS tasks."
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "The ID of the security group for the ALB."
  type        = string
}

variable "ecs_tasks_security_group_id" {
  description = "The ID of the security group for ECS tasks."
  type        = string
}

variable "ecr_repository_url" {
  description = "The URL of the ECR repository for the Flask application."
  type        = string
}

variable "image_tag" {
  description = "The tag of the Docker image to deploy (e.g., 'dev', 'main', 'a1b2c3d4')."
  type        = string
}

variable "cognito_user_pool_id" {
  description = "The ID of the Cognito User Pool to be used by the backend."
  type        = string
}

variable "cognito_client_id" {
  description = "The ID of the Cognito User Pool Client to be used by the backend."
  type        = string
}

variable "frontend_domain" {
  description = "The CloudFront domain name for the frontend (used for constructing short URLs)"
  type        = string
  default     = ""
}

#---------------------------------------------------------------
# OPTIONAL PARAMETERS: These parameters have resonable defaults.
#---------------------------------------------------------------

variable "container_port" {
  description = "The port on which the Flask container listens."
  type        = number
  default     = 5000
}

variable "cpu" {
  description = "The amount of CPU to reserve for the task (in CPU units)."
  type        = number
  default     = 256 # 0.25 vCPU
}

variable "memory" {
  description = "The amount of memory to reserve for the task (in MiB)."
  type        = number
  default     = 512 # 0.5 GB
}

variable "desired_count" {
  description = "The desired number of running tasks for the ECS service."
  type        = number
  default     = 1 # Start with 1 for dev
}

variable "enable_alb_deletion_protection" {
  description = "Whether deletion protection is enabled for the ALB."
  type        = bool
  default     = false # Set to true for production
}

variable "alb_health_check_path" {
  description = "The path for the ALB health check."
  type        = string
  default     = "/" # Your Flask app's root path
}

variable "alb_listener_http_port" {
  description = "The HTTP port for the ALB listener."
  type        = number
  default     = 80
}

variable "enable_https_listener" {
  description = "Whether to enable the HTTPS listener on the ALB."
  type        = bool
  default     = false
}

variable "alb_listener_https_port" {
  description = "The HTTPS port for the ALB listener."
  type        = number
  default     = 443
}

variable "alb_https_certificate_arn" {
  description = "The ARN of the ACM certificate for the ALB HTTPS listener. Required if enable_https_listener is true."
  type        = string
  default     = null # Must be provided if enable_https_listener is true
}

variable "s3_uploads_bucket_name_prefix" {
  description = "A prefix for the S3 bucket name where files will be uploaded. A random suffix will be appended."
  type        = string
  default     = "my-file-sharing-uploads"
}

variable "log_retention_in_days" {
  description = "The number of days to retain logs in CloudWatch."
  type        = number
  default     = 30
}

variable "file_retention_days" {
  description = "The number of days to retain uploaded files in S3 before automatic deletion."
  type        = number
  default     = 30
}

variable "dynamodb_policy_arn" {
  description = "The ARN of the IAM policy for DynamoDB access. If provided, will be attached to the ECS task role."
  type        = string
  default     = null
}