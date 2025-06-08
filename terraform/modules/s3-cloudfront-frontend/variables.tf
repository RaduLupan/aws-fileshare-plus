# variables.tf

#----------------------------------------------------------------------------
# REQUIRED PARAMETERS: You must provide a value for each of these parameters.
#----------------------------------------------------------------------------

variable "environment" {
  description = "The environment name (e.g., dev, staging, prod)."
  type        = string
}

#---------------------------------------------------------------
# OPTIONAL PARAMETERS: These parameters have resonable defaults.
#---------------------------------------------------------------

variable "bucket_name_prefix" {
  description = "A prefix for the S3 bucket name. A random suffix will be appended."
  type        = string
  default     = "my-file-sharing-frontend" 
}


variable "cloudfront_comment" {
  description = "Comment for the CloudFront distribution."
  type        = string
  default     = "CloudFront distribution for the frontend application"
}

variable "viewer_protocol_policy" {
  description = "The protocol policy for viewers. Set to 'redirect-to-https' for production."
  type        = string
  default     = "allow-all" # Set to "redirect-to-https" for production
  validation {
    condition     = contains(["allow-all", "redirect-to-https", "https-only"], var.viewer_protocol_policy)
    error_message = "viewer_protocol_policy must be one of 'allow-all', 'redirect-to-https', or 'https-only'."
  }
}

# Optional: Custom Domain variables (kept for future proofing, even if not used now)
variable "custom_domain_name" {
  description = "Your custom domain name (e.g., app.yourdomain.com). Leave empty if not using."
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "The ARN of the ACM SSL certificate for your custom domain (must be in us-east-1)."
  type        = string
  default     = ""
}