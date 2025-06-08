# variables.tf

#----------------------------------------------------------------------------
# REQUIRED PARAMETERS: You must provide a value for each of these parameters.
#----------------------------------------------------------------------------

variable "environment" {
  description = "The environment name (e.g., dev, staging, prod)."
  type        = string
}

variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
}

#---------------------------------------------------------------
# OPTIONAL PARAMETERS: These parameters have resonable defaults.
#---------------------------------------------------------------

variable "project_name" {
  description = "The name of your project, used as a prefix for resources."
  type        = string
  default     = "my-file-sharing-app"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "A list of availability zones to use for subnets."
  type        = list(string)
  default     = ["us-east-2a", "us-east-2b"] # Match your region
}

variable "public_subnet_cidrs" {
  description = "A list of CIDR blocks for public subnets."
  type        = list(string)
  default     = [] # Will be dynamically generated if empty
}

variable "private_subnet_cidrs" {
  description = "A list of CIDR blocks for private subnets."
  type        = list(string)
  default     = [] # Will be dynamically generated if empty
}

variable "enable_nat_gateway" {
  description = "Whether to create a NAT Gateway for outbound internet access from private subnets."
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Whether to create a single NAT Gateway (true) or one per public subnet (false)."
  type        = bool
  default     = true
}

variable "ecs_service_port" {
  description = "The port on which the ECS service listens (e.g., Flask app port)."
  type        = number
  default     = 5000
}

variable "alb_http_port" {
  description = "The HTTP port for the ALB."
  type        = number
  default     = 80
}

variable "alb_https_port" {
  description = "The HTTPS port for the ALB."
  type        = number
  default     = 443
}