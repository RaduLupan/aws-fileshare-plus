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
  description = "The domain name to verify in SES (e.g., lupan.ca)"
  type        = string
}

variable "from_email_address" {
  description = "The email address to send from (e.g., noreply@lupan.ca)"
  type        = string
}
