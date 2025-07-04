# main.tf for SES email configuration

# -----------------------------------------------------------------------------
# SES Domain Identity
# -----------------------------------------------------------------------------
resource "aws_ses_domain_identity" "domain" {
  domain = var.domain_name
}

# -----------------------------------------------------------------------------
# SES Email Identity  
# -----------------------------------------------------------------------------
resource "aws_ses_email_identity" "email" {
  email = var.from_email_address
}

# -----------------------------------------------------------------------------
# SES Domain DKIM
# -----------------------------------------------------------------------------
resource "aws_ses_domain_dkim" "domain_dkim" {
  domain = aws_ses_domain_identity.domain.domain
}

# -----------------------------------------------------------------------------
# SES Configuration Set (optional but recommended)
# -----------------------------------------------------------------------------
resource "aws_ses_configuration_set" "main" {
  name = "${var.project_name}-${var.environment}-ses-config"

  delivery_options {
    tls_policy = "Require"
  }

  reputation_metrics_enabled = true
}

# -----------------------------------------------------------------------------
# SES Identity Policy for Cognito
# -----------------------------------------------------------------------------
resource "aws_ses_identity_policy" "cognito_policy" {
  identity = aws_ses_domain_identity.domain.arn
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
        Resource = aws_ses_domain_identity.domain.arn
        Condition = {
          StringEquals = {
            "ses:FromAddress" = var.from_email_address
          }
        }
      }
    ]
  })
}
