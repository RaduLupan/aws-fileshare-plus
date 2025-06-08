# outputs.tf

output "alb_dns_name" {
  description = "The DNS name of the Application Load Balancer."
  value       = aws_lb.this.dns_name
}

output "alb_arn" {
  description = "The ARN of the Application Load Balancer."
  value       = aws_lb.this.arn
}

output "ecs_cluster_id" {
  description = "The ID of the ECS cluster."
  value       = aws_ecs_cluster.this.id
}

output "ecs_service_name" {
  description = "The name of the ECS service."
  value       = aws_ecs_service.this.name
}

output "uploads_s3_bucket_name" {
  description = "The name of the S3 bucket for file uploads."
  value       = aws_s3_bucket.uploads_backend.id
}

output "uploads_s3_bucket_arn" {
  description = "The ARN of the S3 bucket for file uploads."
  value       = aws_s3_bucket.uploads_backend.arn
}

output "flask_app_task_role_arn" {
  description = "The ARN of the IAM role for the Flask application task."
  value       = aws_iam_role.flask_app_task.arn
}

output "ecr_repository_url" {
  description = "The URL of the ECR repository for the Flask application."
  value       = aws_ecr_repository.flask_app.repository_url
}

output "ecr_repository_name" {
  description = "The name of the ECR repository for the Flask application."
  value       = aws_ecr_repository.flask_app.name
}