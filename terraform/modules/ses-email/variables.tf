# variables.tf for SES email module

variable "project_name" {
  description = "The name of the project"
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., 'dev', 'prod')"
  type        = string
}

variable "domain_name" {
  description = "The domain name to verify in SES (e.g., aws.lupan.ca). Must be hosted in Route 53. Set to null to use default SES domain."
  type        = string
  default     = null
}

variable "from_email_address" {
  description = "The email address to send from (e.g., noreply@aws.lupan.ca). Only used if domain_name is provided."
  type        = string
  default     = null
}
