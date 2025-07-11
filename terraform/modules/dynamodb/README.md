# DynamoDB Module

This module creates DynamoDB tables for the FileShare Plus application and stores configuration in SSM Parameter Store.

## Resources Created

### DynamoDB Tables
- **Users Table**: Stores user information and trial status
  - Primary Key: `user_id` (String)
  - Global Secondary Index: `email-index` for email lookups
  - Features: Point-in-time recovery, server-side encryption

- **URLs Table**: Stores URL mappings and metadata
  - Primary Key: `short_code` (String)
  - Global Secondary Index: `user-index` for user-based lookups
  - Features: TTL for automatic cleanup, point-in-time recovery, server-side encryption

### IAM Policy
- **DynamoDB Access Policy**: Allows ECS tasks to read/write to DynamoDB tables

### SSM Parameters
All DynamoDB configuration is stored in SSM Parameter Store under `/fileshare/{environment}/`:
- `dynamodb_users_table_name`
- `dynamodb_urls_table_name`
- `dynamodb_users_table_arn`
- `dynamodb_urls_table_arn`
- `dynamodb_policy_arn`
- `use_dynamodb` (set to "true")

## Usage

```hcl
module "dynamodb" {
  source = "../../modules/dynamodb"

  project_name                   = var.project_name
  environment                    = var.environment
  aws_region                     = var.aws_region
  enable_point_in_time_recovery  = true
}
```

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_name | Name of the project | string | n/a | yes |
| environment | Environment name (dev, staging, prod) | string | n/a | yes |
| aws_region | AWS region | string | n/a | yes |
| enable_point_in_time_recovery | Enable point-in-time recovery for DynamoDB tables | bool | true | no |
| tags | Additional tags to apply to resources | map(string) | {} | no |

## Outputs

| Name | Description |
|------|-------------|
| users_table_name | Name of the DynamoDB users table |
| users_table_arn | ARN of the DynamoDB users table |
| urls_table_name | Name of the DynamoDB URLs table |
| urls_table_arn | ARN of the DynamoDB URLs table |
| dynamodb_policy_arn | ARN of the IAM policy for DynamoDB access |

## Backend Integration

The backend application will automatically use DynamoDB when the `USE_DYNAMODB` environment variable is set to "true". The GitHub Actions workflow reads this from SSM Parameter Store and sets it as an environment variable for the ECS tasks.

## Cost Optimization

- Uses PAY_PER_REQUEST billing mode for cost efficiency
- TTL configured for automatic cleanup of expired URLs
- Point-in-time recovery can be disabled in non-production environments to reduce costs