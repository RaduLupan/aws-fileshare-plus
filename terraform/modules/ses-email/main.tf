# main.tf for SES email configuration

# -----------------------------------------------------------------------------
# Data sources
# -----------------------------------------------------------------------------
data "aws_route53_zone" "domain" {
  count = var.domain_name != null ? 1 : 0
  name  = var.domain_name
}

# -----------------------------------------------------------------------------
# SES Domain Identity (only if domain is provided)
# -----------------------------------------------------------------------------
resource "aws_ses_domain_identity" "domain" {
  count  = var.domain_name != null ? 1 : 0
  domain = var.domain_name
}

# -----------------------------------------------------------------------------
# SES Email Identity (only if domain is provided)
# -----------------------------------------------------------------------------
resource "aws_ses_email_identity" "email" {
  count = var.from_email_address != null ? 1 : 0
  email = var.from_email_address
}

# -----------------------------------------------------------------------------
# SES Domain DKIM (only if domain is provided)
# -----------------------------------------------------------------------------
resource "aws_ses_domain_dkim" "domain_dkim" {
  count  = var.domain_name != null ? 1 : 0
  domain = aws_ses_domain_identity.domain[0].domain
}

# -----------------------------------------------------------------------------
# Route 53 DNS Records for SES Verification
# -----------------------------------------------------------------------------

# Domain verification TXT record
resource "aws_route53_record" "ses_verification" {
  count   = var.domain_name != null ? 1 : 0
  zone_id = data.aws_route53_zone.domain[0].zone_id
  name    = "_amazonses.${var.domain_name}"
  type    = "TXT"
  ttl     = 300
  records = [aws_ses_domain_identity.domain[0].verification_token]
}

# DKIM CNAME records
resource "aws_route53_record" "dkim" {
  count   = var.domain_name != null ? 3 : 0
  zone_id = data.aws_route53_zone.domain[0].zone_id
  name    = "${aws_ses_domain_dkim.domain_dkim[0].dkim_tokens[count.index]}._domainkey.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = ["${aws_ses_domain_dkim.domain_dkim[0].dkim_tokens[count.index]}.dkim.amazonses.com"]
}

# SPF TXT record
resource "aws_route53_record" "spf" {
  count   = var.domain_name != null ? 1 : 0
  zone_id = data.aws_route53_zone.domain[0].zone_id
  name    = var.domain_name
  type    = "TXT"
  ttl     = 300
  
  # Check if SPF record already exists and merge
  records = ["v=spf1 include:amazonses.com ~all"]
}

# -----------------------------------------------------------------------------
# SES Configuration Set (optional but recommended)
# -----------------------------------------------------------------------------
resource "aws_ses_configuration_set" "main" {
  count = var.domain_name != null ? 1 : 0
  name  = "${var.project_name}-${var.environment}-ses-config"

  delivery_options {
    tls_policy = "Require"
  }

  reputation_metrics_enabled = true
}

# -----------------------------------------------------------------------------
# SES Identity Policy for Cognito (only if domain is provided)
# -----------------------------------------------------------------------------
resource "aws_ses_identity_policy" "cognito_policy" {
  count    = var.domain_name != null ? 1 : 0
  identity = aws_ses_domain_identity.domain[0].arn
  name     = "${var.project_name}-${var.environment}-cognito-ses-policy"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cognito-idp.amazonaws.com"
        }
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = aws_ses_domain_identity.domain[0].arn
        Condition = {
          StringEquals = {
            "ses:FromAddress" = var.from_email_address
          }
        }
      }
    ]
  })
}
