# variables.tf for the cognito-user-management module

variable "project_name" {
  description = "The name of the project."
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., 'dev', 'prod')."
  type        = string
}
