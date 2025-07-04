# outputs.tf for SES email module

output "domain_identity_arn" {
  description = "The ARN of the SES domain identity"
  value       = aws_ses_domain_identity.domain.arn
}

output "email_identity_arn" {
  description = "The ARN of the SES email identity"
  value       = aws_ses_email_identity.email.arn
}

output "domain_verification_token" {
  description = "The domain verification token for DNS setup"
  value       = aws_ses_domain_identity.domain.verification_token
}

output "dkim_tokens" {
  description = "DKIM tokens for DNS setup"
  value       = aws_ses_domain_dkim.domain_dkim.dkim_tokens
}

output "from_email_address" {
  description = "The from email address"
  value       = var.from_email_address
}
