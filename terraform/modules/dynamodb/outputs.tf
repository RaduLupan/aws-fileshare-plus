# terraform/modules/dynamodb/outputs.tf

output "users_table_name" {
  description = "Name of the DynamoDB users table"
  value       = aws_dynamodb_table.users.name
}

output "users_table_arn" {
  description = "ARN of the DynamoDB users table"
  value       = aws_dynamodb_table.users.arn
}

output "urls_table_name" {
  description = "Name of the DynamoDB URLs table"
  value       = aws_dynamodb_table.urls.name
}

output "urls_table_arn" {
  description = "ARN of the DynamoDB URLs table"
  value       = aws_dynamodb_table.urls.arn
}

output "dynamodb_policy_arn" {
  description = "ARN of the IAM policy for DynamoDB access"
  value       = aws_iam_policy.dynamodb_access.arn
}

output "users_table_stream_arn" {
  description = "ARN of the DynamoDB users table stream"
  value       = aws_dynamodb_table.users.stream_arn
}

output "urls_table_stream_arn" {
  description = "ARN of the DynamoDB URLs table stream"
  value       = aws_dynamodb_table.urls.stream_arn
}