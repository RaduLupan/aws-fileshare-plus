# outputs.tf

output "s3_bucket_id" {
  description = "The ID of the S3 bucket."
  value       = aws_s3_bucket.this.id
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket."
  value       = aws_s3_bucket.this.bucket
}

output "cloudfront_distribution_id" {
  description = "The ID of the CloudFront distribution."
  value       = aws_cloudfront_distribution.this.id
}

output "cloudfront_domain_name" {
  description = "The domain name of the CloudFront distribution."
  value       = aws_cloudfront_distribution.this.domain_name
}

output "cloudfront_arn" {
  description = "The ARN of the CloudFront distribution."
  value       = aws_cloudfront_distribution.this.arn
}

output "custom_domain_url" {
  description = "The custom domain URL if configured."
  value       = var.custom_domain_name != "" ? "https://${var.custom_domain_name}" : "N/A"
}

output "react_s3_bucket_name" {
  description = "The name of the S3 bucket for the React frontend."
  value       = aws_s3_bucket.this.id
}
