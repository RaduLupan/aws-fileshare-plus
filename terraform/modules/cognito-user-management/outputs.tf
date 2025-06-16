# outputs.tf for the cognito-user-management module

output "user_pool_id" {
  description = "The ID of the Cognito User Pool."
  value       = aws_cognito_user_pool.this.id
}

output "user_pool_client_id" {
  description = "The ID of the Cognito User Pool Client."
  value       = aws_cognito_user_pool_client.this.id
}
