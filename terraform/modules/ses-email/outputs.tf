# outputs.tf for SES email module

output "domain_identity_arn" {
  description = "The ARN of the SES domain identity (null if no custom domain)"
  value       = var.domain_name != null ? aws_ses_domain_identity.domain[0].arn : null
}

output "domain_verification_token" {
  description = "The domain verification token for DNS setup (null if no custom domain)"
  value       = var.domain_name != null ? aws_ses_domain_identity.domain[0].verification_token : null
}

output "dkim_tokens" {
  description = "DKIM tokens for DNS setup (empty if no custom domain)"
  value       = var.domain_name != null ? aws_ses_domain_dkim.domain_dkim[0].dkim_tokens : []
}

output "from_email_address" {
  description = "The from email address (null if no custom domain)"
  value       = var.from_email_address
}

output "domain_name" {
  description = "The configured domain name (null if no custom domain)"
  value       = var.domain_name
}

output "ses_enabled" {
  description = "Whether custom SES domain is enabled"
  value       = var.domain_name != null
}
