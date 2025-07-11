# DynamoDB Deployment Plan

## 📋 **Overview**

This plan implements DynamoDB as the production database for FileShare Plus, replacing the ephemeral SQLite setup with a robust, scalable solution.

## 🏗️ **Architecture Changes**

### **Created Components**
1. **DynamoDB Module** (`terraform/modules/dynamodb/`)
   - Users table with email GSI
   - URLs table with user GSI
   - IAM policy for ECS access
   - SSM parameters for configuration

2. **Environment Integration** (`terraform/environments/dev/`)
   - DynamoDB module call
   - SSM parameter storage
   - ECS task policy attachment

3. **Backend Compatibility**
   - Environment-based database selection
   - DynamoDB adapter for production
   - SQLite fallback for development

## 🚀 **Deployment Steps**

### **Phase 1: Terraform Infrastructure**

#### **1.1 Deploy DynamoDB Tables**
```bash
# Navigate to dev environment
cd terraform/environments/dev

# Initialize Terraform (if needed)
terraform init

# Plan the deployment
terraform plan -var-file=dev.tfvars

# Apply the changes
terraform apply -var-file=dev.tfvars
```

**Expected Resources Created:**
- `file-sharing-app-dev-users` DynamoDB table
- `file-sharing-app-dev-urls` DynamoDB table
- IAM policy for DynamoDB access
- SSM parameters under `/fileshare/dev/`

#### **1.2 Verify SSM Parameters**
```bash
# Check that SSM parameters were created
aws ssm get-parameters-by-path --path "/fileshare/dev" --query "Parameters[*].{Name:Name,Value:Value}" --output table
```

**Expected SSM Parameters:**
- `/fileshare/dev/dynamodb_users_table_name`
- `/fileshare/dev/dynamodb_urls_table_name`
- `/fileshare/dev/dynamodb_users_table_arn`
- `/fileshare/dev/dynamodb_urls_table_arn`
- `/fileshare/dev/dynamodb_policy_arn`
- `/fileshare/dev/use_dynamodb` (set to "true")

### **Phase 2: Backend Deployment**

#### **2.1 Deploy Backend with DynamoDB Support**
```bash
# Use GitHub Actions workflow
# Go to: https://github.com/your-repo/actions/workflows/deploy-backend.yml
# Click "Run workflow"
# Select branch: dev
# Click "Run workflow"
```

**What happens:**
1. GitHub Actions reads SSM parameters
2. Sets `USE_DYNAMODB=true` environment variable
3. Deploys backend with DynamoDB configuration
4. ECS task gets DynamoDB permissions

#### **2.2 Verify Backend Configuration**
```bash
# Check ECS task environment variables
aws ecs describe-services --cluster file-sharing-app-dev-cluster --services file-sharing-app-dev-service

# Check task definition
aws ecs describe-task-definition --task-definition file-sharing-app-dev-flask-task
```

### **Phase 3: Data Migration** (if needed)

#### **3.1 Migrate Existing Data**
```bash
# If you have existing SQLite data to migrate
cd backend
python3 dynamodb_migration.py
```

**Note:** For a fresh deployment, no migration is needed.

### **Phase 4: Testing & Verification**

#### **4.1 Test Database Connection**
```bash
# SSH into ECS container or use ECS Exec
aws ecs execute-command \
  --cluster file-sharing-app-dev-cluster \
  --task <task-id> \
  --container file-sharing-app-dev-flask-container \
  --command "python3 -c 'from dynamodb_adapter import db_adapter; print(db_adapter.get_user_trial_status(\"test@example.com\", \"test-123\"))'"
```

#### **4.2 Test Trial Button**
1. Sign in as `radu@lupan.ca`
2. Verify button shows "Try Premium - Free for 30 days"
3. Click button to start trial
4. Verify trial starts successfully
5. Check DynamoDB tables for user data

## 📊 **Cost Estimation**

### **DynamoDB Costs**
- **Users table**: ~$0.25/month (1000 users, light usage)
- **URLs table**: ~$0.50/month (10,000 URLs, moderate usage)
- **Point-in-time recovery**: ~$0.20/month
- **Total monthly cost**: ~$1-2

### **Cost Optimization**
- Uses PAY_PER_REQUEST billing (no capacity planning needed)
- TTL configured for automatic URL cleanup
- Point-in-time recovery can be disabled in dev to save costs

## 🔧 **Configuration Details**

### **Environment Variables (automatically set by GitHub Actions)**
```bash
# Read from SSM Parameter Store
USE_DYNAMODB=true
AWS_REGION=us-east-2
DYNAMODB_USERS_TABLE_NAME=file-sharing-app-dev-users
DYNAMODB_URLS_TABLE_NAME=file-sharing-app-dev-urls
```

### **DynamoDB Table Specifications**

#### **Users Table**
- **Primary Key**: `user_id` (String)
- **GSI**: `email-index` on `email` field
- **Attributes**: user_id, email, user_tier, trial_used, trial_started_at, trial_expires_at, created_at, updated_at
- **Features**: Encryption at rest, point-in-time recovery

#### **URLs Table**
- **Primary Key**: `short_code` (String)
- **GSI**: `user-index` on `created_by_user` field
- **Attributes**: short_code, full_url, created_at, expires_at, created_by_user, file_key, filename, click_count
- **Features**: TTL on `expires_at_ttl`, encryption at rest, point-in-time recovery

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **SSM Parameters Not Found**
```bash
# Check if terraform apply completed successfully
terraform output -json

# Verify SSM parameters exist
aws ssm get-parameters-by-path --path "/fileshare/dev"
```

#### **DynamoDB Access Denied**
```bash
# Check ECS task role has DynamoDB policy attached
aws iam list-attached-role-policies --role-name file-sharing-app-dev-flask-app-task-role

# Verify policy permissions
aws iam get-policy --policy-arn <dynamodb-policy-arn>
```

#### **Backend Still Using SQLite**
```bash
# Check USE_DYNAMODB environment variable
aws ecs describe-task-definition --task-definition file-sharing-app-dev-flask-task | grep -A 20 "environment"

# Force new deployment
aws ecs update-service --cluster file-sharing-app-dev-cluster --service file-sharing-app-dev-service --force-new-deployment
```

### **Rollback Plan**

#### **If DynamoDB Issues Occur**
1. **Quick rollback**: Update SSM parameter `/fileshare/dev/use_dynamodb` to "false"
2. **Redeploy backend**: Run deploy-backend workflow
3. **Backend will revert to SQLite**: (with data loss, but functional)

#### **Complete Rollback**
```bash
# Remove DynamoDB module from terraform
# Comment out module "dynamodb" block in main.tf
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars

# Deploy backend without DynamoDB
# Run deploy-backend workflow
```

## ✅ **Success Criteria**

### **Infrastructure**
- [ ] DynamoDB tables created successfully
- [ ] SSM parameters populated
- [ ] ECS task role has DynamoDB permissions
- [ ] Backend deployed with DynamoDB configuration

### **Functionality**
- [ ] Trial button shows correctly for new users
- [ ] Trial functionality works end-to-end
- [ ] User data persists across deployments
- [ ] URL shortening works with DynamoDB

### **Monitoring**
- [ ] CloudWatch metrics for DynamoDB tables
- [ ] ECS task logs show DynamoDB connections
- [ ] No errors in application logs

## 📞 **Support & Monitoring**

### **CloudWatch Dashboards**
- DynamoDB table metrics (read/write capacity, throttles)
- ECS task health and performance
- Application logs and errors

### **Alerts**
- DynamoDB throttling alerts
- ECS task failure alerts
- Application error rate alerts

---

## 🎯 **Next Steps After Deployment**

1. **Monitor Performance**: Watch DynamoDB metrics and ECS logs
2. **Test Thoroughly**: Verify all application functionality
3. **Optimize Costs**: Adjust point-in-time recovery settings
4. **Scale to Production**: Apply same changes to prod environment
5. **Remove SQLite Code**: After stable operation, remove SQLite fallback

**This deployment will permanently fix the trial button issue and provide a scalable database solution for production use.**