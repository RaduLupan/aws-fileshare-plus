# variables.tf for the cognito-user-management module

variable "project_name" {
  description = "The name of the project."
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., 'dev', 'prod')."
  type        = string
}

# Email configuration variables for better deliverability
variable "ses_email_identity_arn" {
  description = "ARN of the verified SES email identity for sending emails"
  type        = string
  default     = null
}

variable "from_email_address" {
  description = "Email address to send verification emails from (e.g., noreply@yourdomain.com)"
  type        = string
  default     = null
}

variable "reply_to_email_address" {
  description = "Email address for replies (optional)"
  type        = string
  default     = null
}
