# terraform/environments/dev/variables.tf

variable "aws_region" {
  description = "The AWS region to deploy resources."
  type        = string
  default     = "us-east-1" # CloudFront requires S3 origin in us-east-1 if using default cert
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
