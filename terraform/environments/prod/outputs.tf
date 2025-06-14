# Output relevant values from the modules
output "frontend_url" {
  description = "The URL of the deployed frontend application."
  value       = "http://${module.frontend_app.cloudfront_domain_name}"
}

output "react_s3_bucket_name" {
  description = "The S3 bucket name for the React frontend."
  value       = module.frontend_app.s3_bucket_name
}

output "backend_alb_url" {
  description = "The URL of the backend ALB."
  value       = "http://${module.backend_app.alb_dns_name}" # Use http for now, update to https when ALB has certificate
}

output "s3_uploads_bucket_name" {
  description = "The S3 bucket name for file uploads."
  value       = module.backend_app.uploads_s3_bucket_name
}
