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

variable "alb_enable_https_listener" {
  description = "Enable HTTPS listener for the ALB."
  type        = bool
  default     = false # Set to true if you want to enable HTTPS in dev
}

variable "alb_https_certificate_arn" {
  description = "The ARN of the ACM certificate for HTTPS listener on the ALB."
  type        = string
  default     = "" # Provide your certificate ARN if alb_enable_https_listener is true
}

variable "cloudfront_https_certificate_arn" {
  description = "The ARN of the ACM certificate for CloudFront distribution."
  type        = string
  default     = "" # Provide your certificate ARN if using a custom domain with CloudFront
}

variable "cloudfront_viewer_protocol_policy" {
  description = "The viewer protocol policy for CloudFront distribution."
  type        = string
  default     = "redirect-to-https" # Change to "https-only" for production
}