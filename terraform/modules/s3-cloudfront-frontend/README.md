# Terraform Module: S3 + CloudFront Frontend

This Terraform module provisions the necessary AWS infrastructure to host a static frontend application (e.g., a React, Angular, or Vue.js build) using an S3 bucket as the origin and CloudFront as the Content Delivery Network (CDN).

## Features

* Creates a private Amazon S3 bucket for storing static assets.
* Configures an S3 Bucket Policy to allow access only from CloudFront.
* Sets up a CloudFront Origin Access Control (OAC) for secure S3 integration (recommended over OAI).
* Deploys an Amazon CloudFront distribution for global content delivery and caching.
* Configures CloudFront for Single-Page Application (SPA) routing (e.g., `/index.html` for 403/404 errors).
* Supports both HTTP and HTTPS access (via CloudFront's default certificate or optional custom domain).
* Optionally configures a custom domain with an ACM certificate.
* Optionally configures a second origin and behavior for proxying API calls through CloudFront (e.g., `/api/*` to an ALB).

## Usage

```terraform
module "frontend_app" {
  source = "../../modules/s3-cloudfront-frontend" # Adjust path as necessary

  environment            = var.environment
  bucket_name_prefix     = "${var.project_name}-${var.environment}-frontend"
  cloudfront_comment     = "${var.environment} CloudFront distribution for ${var.project_name} frontend"
  viewer_protocol_policy = "allow-all" # Options: "allow-all", "redirect-to-https", "https-only"

  # Optional: For custom domain (requires ACM cert in us-east-1)
  # custom_domain_name     = "app.yourdomain.com"
  # acm_certificate_arn    = "arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id"

  # Optional: For proxying API calls through CloudFront (requires ALB DNS name)
  # backend_alb_dns_name = module.backend_app.alb_dns_name
  # alb_http_port        = module.network.alb_http_port
  # alb_https_port       = module.network.alb_https_port
}
```

## Inputs
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `bucket_name_prefix` | A prefix for the S3 bucket name. A random suffix will be appended. | `string` | `"my-file-sharing-frontend"` | no |
| `environment` | The environment name (e.g., dev, staging, prod). | `string` | | yes |
| `cloudfront_comment` | Comment for the CloudFront distribution. | `string` | `"CloudFront distribution for the frontend application"` | no |
| `viewer_protocol_policy` | The protocol policy for viewers. Set to `redirect-to-https` for production. | `string` | `"allow-all"` | no |
| `custom_domain_name` | Your custom domain name (e.g., `app.yourdomain.com`). Leave empty if not using. | `string` | `""` | no |
| `acm_certificate_arn` | The ARN of the ACM SSL certificate for your custom domain (must be in `us-east-1`). | `string` | `""` | no |
| `backend_alb_dns_name` | The DNS name of the backend ALB, if proxying API calls through CloudFront. | `string` | `null` | no |
| `alb_http_port` | The HTTP port of the ALB (for CloudFront origin). | `number` | `80` | no |
| `alb_https_port` | The HTTPS port of the ALB (for CloudFront origin). | `number` | `443` | no |

## Outputs
| Name | Description |
|------|-------------|
| `s3_bucket_id` | The ID of the S3 bucket. |
| `s3_bucket_name` | The name of the S3 bucket. |
| `cloudfront_distribution_id` | The ID of the CloudFront distribution. |
| `cloudfront_domain_name` | The domain name of the CloudFront distribution. |
| `cloudfront_arn` | The ARN of the CloudFront distribution. |
| `custom_domain_url` | The custom domain URL if configured. |