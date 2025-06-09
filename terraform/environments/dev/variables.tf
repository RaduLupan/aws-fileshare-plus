# terraform/environments/dev/variables.tf

variable "aws_region" {
  description = "The AWS region to deploy resources."
  type        = string
  default     = "us-east-1" # CloudFront requires S3 origin in us-east-1 if using default cert
}

variable "availability_zones" {
  description = "A list of availability zones to use for subnets."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"] # Match your region
}

variable "environment" {
  description = "The environment name (e.g., dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "The name of your project, used as a prefix for resources."
  type        = string
  default     = "my-file-sharing-app"
}

variable "cloudfront_custom_domain_name" {
  description = "The custom domain name for CloudFront distribution - frontend."
  type        = string
  default     = "dev.example.com" # Change this to your actual dev domain
}

variable "alb_custom_domain_name" {
  description = "The custom domain name for the ALB - backend."
  type        = string
  default     = "dev-backend.example.com" # Change this to your actual dev backend domain
}