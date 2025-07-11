# Terraform DynamoDB Implementation - Complete Plan

## 📋 **Executive Summary**

This document provides a complete plan for implementing DynamoDB as the production database for FileShare Plus using Terraform modules and SSM Parameter Store integration.

## 🎯 **Objectives**

1. **Fix Trial Button Issue**: Permanent solution with persistent data
2. **Replace SQLite**: Eliminate ephemeral database problems
3. **Terraform Integration**: Follow existing module patterns
4. **SSM Parameter Store**: Integrate with existing deployment pipeline
5. **Zero Downtime**: Smooth deployment with rollback capability

## 🏗️ **Architecture Overview**

### **Current State**
- SQLite database in ECS Fargate (ephemeral)
- Data lost on every container restart
- Trial button issue persists across deployments

### **Target State**
- DynamoDB tables for persistent data
- SSM parameters for configuration
- Environment-based database selection
- Terraform-managed infrastructure

## 📦 **Components Created**

### **1. DynamoDB Module** (`terraform/modules/dynamodb/`)
```
terraform/modules/dynamodb/
├── main.tf           # DynamoDB tables and SSM parameters
├── variables.tf      # Input variables
├── outputs.tf        # Module outputs
├── versions.tf       # Terraform version constraints
└── README.md         # Documentation
```

**Resources:**
- `aws_dynamodb_table.users` - User data and trial status
- `aws_dynamodb_table.urls` - URL mappings
- `aws_iam_policy.dynamodb_access` - ECS access policy
- `aws_ssm_parameter.*` - Configuration parameters

### **2. Environment Integration** (`terraform/environments/dev/`)
**Modified Files:**
- `main.tf` - Added DynamoDB module call
- `variables.tf` - Added DynamoDB variables

**New Configuration:**
```hcl
module "dynamodb" {
  source = "../../modules/dynamodb"
  
  project_name                  = var.project_name
  environment                   = var.environment
  aws_region                    = var.aws_region
  enable_point_in_time_recovery = var.enable_point_in_time_recovery
}
```

### **3. ECS Backend Integration** (`terraform/modules/ecs-flask-backend/`)
**Modified Files:**
- `variables.tf` - Added `dynamodb_policy_arn` variable
- `iam.tf` - Added DynamoDB policy attachment

**New IAM Attachment:**
```hcl
resource "aws_iam_role_policy_attachment" "flask_app_dynamodb_policy_attachment" {
  count      = var.dynamodb_policy_arn != null ? 1 : 0
  policy_arn = var.dynamodb_policy_arn
  role       = aws_iam_role.flask_app_task.name
}
```

### **4. Backend Application** (`backend/`)
**No Changes Required:**
- `user_management.py` already has DynamoDB support
- Environment variable `USE_DYNAMODB` controls database selection
- GitHub Actions workflow already reads SSM parameters

## 🚀 **Deployment Plan**

### **Phase 1: Infrastructure Deployment**
```bash
# 1. Navigate to dev environment
cd terraform/environments/dev

# 2. Review changes
terraform plan -var-file=dev.tfvars

# 3. Deploy infrastructure
terraform apply -var-file=dev.tfvars
```

### **Phase 2: Verify SSM Parameters**
```bash
# Check SSM parameters were created
aws ssm get-parameters-by-path --path "/fileshare/dev" --output table
```

### **Phase 3: Backend Deployment**
```bash
# Use existing GitHub Actions workflow
# Workflow automatically reads SSM parameters
# Sets USE_DYNAMODB=true environment variable
```

### **Phase 4: Testing**
```bash
# Test trial button functionality
# Verify data persistence
# Check DynamoDB tables
```

## 📊 **SSM Parameter Store Integration**

### **Parameters Created**
```
/fileshare/dev/dynamodb_users_table_name    = "file-sharing-app-dev-users"
/fileshare/dev/dynamodb_urls_table_name     = "file-sharing-app-dev-urls"
/fileshare/dev/dynamodb_users_table_arn     = "arn:aws:dynamodb:..."
/fileshare/dev/dynamodb_urls_table_arn      = "arn:aws:dynamodb:..."
/fileshare/dev/dynamodb_policy_arn          = "arn:aws:iam:..."
/fileshare/dev/use_dynamodb                 = "true"
```

### **GitHub Actions Integration**
**Existing workflow** (`deploy-backend.yml`) already:
1. Reads SSM parameters from `/fileshare/{env}/`
2. Converts to environment variables
3. Passes to ECS task definition

**New environment variables:**
- `USE_DYNAMODB=true`
- `DYNAMODB_USERS_TABLE_NAME=file-sharing-app-dev-users`
- `DYNAMODB_URLS_TABLE_NAME=file-sharing-app-dev-urls`

## 🔧 **Technical Implementation Details**

### **DynamoDB Table Design**

#### **Users Table**
```json
{
  "TableName": "file-sharing-app-dev-users",
  "KeySchema": [
    {"AttributeName": "user_id", "KeyType": "HASH"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "email-index",
      "KeySchema": [
        {"AttributeName": "email", "KeyType": "HASH"}
      ]
    }
  ],
  "BillingMode": "PAY_PER_REQUEST"
}
```

#### **URLs Table**
```json
{
  "TableName": "file-sharing-app-dev-urls",
  "KeySchema": [
    {"AttributeName": "short_code", "KeyType": "HASH"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "user-index",
      "KeySchema": [
        {"AttributeName": "created_by_user", "KeyType": "HASH"}
      ]
    }
  ],
  "BillingMode": "PAY_PER_REQUEST",
  "TimeToLiveSpecification": {
    "AttributeName": "expires_at_ttl",
    "Enabled": true
  }
}
```

### **Backend Database Selection**
```python
# Environment-based database selection
USE_DYNAMODB = os.getenv('USE_DYNAMODB', 'false').lower() == 'true'

if USE_DYNAMODB:
    # Use DynamoDB for production
    from dynamodb_adapter import db_adapter
    # ... DynamoDB implementation
else:
    # Use SQLite for development
    import sqlite3
    # ... SQLite implementation
```

### **IAM Permissions**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/file-sharing-app-dev-users",
        "arn:aws:dynamodb:*:*:table/file-sharing-app-dev-users/index/*",
        "arn:aws:dynamodb:*:*:table/file-sharing-app-dev-urls",
        "arn:aws:dynamodb:*:*:table/file-sharing-app-dev-urls/index/*"
      ]
    }
  ]
}
```

## 💰 **Cost Analysis**

### **DynamoDB Costs (Monthly)**
- **Users table**: ~$0.25 (1000 users, light read/write)
- **URLs table**: ~$0.50 (10,000 URLs, moderate read/write)
- **Point-in-time recovery**: ~$0.20
- **Total**: ~$1-2/month

### **Cost Optimization**
- PAY_PER_REQUEST billing (no capacity planning)
- TTL for automatic URL cleanup
- Point-in-time recovery configurable per environment

## 🛠️ **Operations & Maintenance**

### **Monitoring**
- CloudWatch metrics for DynamoDB tables
- ECS task logs for database operations
- Application performance monitoring

### **Backup & Recovery**
- Point-in-time recovery enabled
- Automated backups
- Cross-region replication (optional)

### **Scaling**
- Auto-scaling with PAY_PER_REQUEST
- Global secondary indexes for query performance
- Connection pooling in application

## 🔄 **Rollback Strategy**

### **Quick Rollback**
```bash
# Update SSM parameter
aws ssm put-parameter \
  --name "/fileshare/dev/use_dynamodb" \
  --value "false" \
  --overwrite

# Redeploy backend
# Run deploy-backend workflow
```

### **Complete Rollback**
```bash
# Remove DynamoDB module from terraform
# Comment out module "dynamodb" block
terraform apply -var-file=dev.tfvars
```

## ✅ **Success Criteria**

### **Infrastructure**
- [ ] DynamoDB tables created successfully
- [ ] SSM parameters populated
- [ ] ECS task role has DynamoDB permissions
- [ ] No terraform errors or warnings

### **Application**
- [ ] Trial button shows correctly for new users
- [ ] Trial functionality works end-to-end
- [ ] User data persists across deployments
- [ ] URL shortening works with DynamoDB
- [ ] No application errors in logs

### **Performance**
- [ ] Response times within acceptable limits
- [ ] No DynamoDB throttling
- [ ] ECS tasks healthy and stable

## 📞 **Next Steps**

1. **Review Implementation**: Verify all Terraform code
2. **Deploy to Dev**: Run terraform apply
3. **Test Thoroughly**: Verify all functionality
4. **Monitor Performance**: Watch metrics and logs
5. **Deploy to Production**: Apply same changes to prod environment

---

## 🎉 **Expected Outcomes**

### **Immediate Benefits**
- ✅ **Trial button fixed permanently**
- ✅ **Data persistence across deployments**
- ✅ **No more SQLite-related issues**
- ✅ **Scalable database solution**

### **Long-term Benefits**
- ✅ **Production-ready architecture**
- ✅ **Cost-effective scaling**
- ✅ **Simplified operations**
- ✅ **Better monitoring and alerting**

**This implementation provides a robust, scalable solution that follows infrastructure as code best practices and integrates seamlessly with your existing deployment pipeline.**