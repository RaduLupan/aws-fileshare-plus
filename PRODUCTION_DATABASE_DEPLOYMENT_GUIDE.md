# Production Database Deployment Guide

## 🚨 **CRITICAL ISSUE: SQLite in ECS Fargate**

Your current SQLite setup **will lose all user data** every time containers restart. This is why the trial button issue keeps coming back!

### **The Problem**
- ❌ ECS Fargate containers are **ephemeral** - filesystem is lost on restart
- ❌ SQLite data disappears with each deployment
- ❌ No persistence across container restarts
- ❌ Cannot scale to multiple containers

## 🔧 **Immediate Solutions**

### **Option 1: Quick Fix - Add EFS Volume**

Add persistent storage to your ECS task definition:

```json
{
  "family": "fileshare-backend",
  "volumes": [
    {
      "name": "database-storage",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxxxxxx",
        "rootDirectory": "/data"
      }
    }
  ],
  "containerDefinitions": [
    {
      "name": "backend",
      "mountPoints": [
        {
          "sourceVolume": "database-storage",
          "containerPath": "/app/data"
        }
      ],
      "environment": [
        {
          "name": "DB_PATH",
          "value": "/app/data/url_shortener.db"
        }
      ]
    }
  ]
}
```

**Steps:**
1. Create EFS filesystem in AWS Console
2. Update ECS task definition with EFS volume
3. Redeploy containers

### **Option 2: Recommended - DynamoDB Migration**

## 🏗️ **DynamoDB Migration (Recommended)**

### **Why DynamoDB?**
- ✅ **Serverless** - no infrastructure management
- ✅ **Highly available** - built-in redundancy
- ✅ **Auto-scaling** - handles traffic spikes
- ✅ **Cost-effective** - pay per request
- ✅ **Perfect for your use case** - user data and URLs

### **Step-by-Step Migration**

#### **Step 1: Create DynamoDB Tables**

```bash
# Run from your local machine or EC2 instance
cd backend
pip install boto3
python3 dynamodb_migration.py
```

This creates:
- `fileshare-users` table - user data and trial status
- `fileshare-urls` table - URL mappings

#### **Step 2: Update Backend Configuration**

Add to your ECS task definition environment variables:

```json
{
  "environment": [
    {
      "name": "USE_DYNAMODB",
      "value": "true"
    },
    {
      "name": "AWS_REGION",
      "value": "us-east-1"
    }
  ]
}
```

#### **Step 3: Update IAM Role**

Add DynamoDB permissions to your ECS task role:

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
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/fileshare-users",
        "arn:aws:dynamodb:*:*:table/fileshare-users/index/*",
        "arn:aws:dynamodb:*:*:table/fileshare-urls",
        "arn:aws:dynamodb:*:*:table/fileshare-urls/index/*"
      ]
    }
  ]
}
```

#### **Step 4: Update requirements.txt**

```txt
# Add to backend/requirements.txt
boto3>=1.34.0
```

#### **Step 5: Deploy**

```bash
# Build and deploy your containers with:
# - Updated environment variables
# - Updated IAM role
# - Updated requirements.txt
```

## 📋 **Complete Deployment Checklist**

### **Immediate Fix (Today)**
- [ ] **Fix API response field** - Already done in code
- [ ] **Deploy backend** with API fix
- [ ] **Initialize database** (if using SQLite temporarily)
- [ ] **Reset user trial status** for affected users

### **Production Fix (This Week)**
- [ ] **Create DynamoDB tables**
- [ ] **Update IAM role** with DynamoDB permissions
- [ ] **Add environment variables** to ECS task
- [ ] **Deploy with DynamoDB enabled**
- [ ] **Test trial button functionality**
- [ ] **Monitor for issues**

## 🚀 **Deployment Commands**

### **For Immediate Fix**
```bash
# 1. Deploy backend with API fix
# (Use your existing CI/CD pipeline)

# 2. Initialize database (if using SQLite)
# SSH into one of your containers or use ECS Exec
aws ecs execute-command \
  --cluster your-cluster \
  --task your-task-id \
  --container backend \
  --command "python3 -c 'from database import init_database; init_database()'"

# 3. Reset user trial status
aws ecs execute-command \
  --cluster your-cluster \
  --task your-task-id \
  --container backend \
  --command "python3 reset_user_trial.py reset radu@lupan.ca"
```

### **For DynamoDB Migration**
```bash
# 1. Create DynamoDB tables
python3 dynamodb_migration.py

# 2. Update ECS task definition
aws ecs register-task-definition \
  --cli-input-json file://updated-task-definition.json

# 3. Update ECS service
aws ecs update-service \
  --cluster your-cluster \
  --service your-service \
  --task-definition your-task-definition:NEW_REVISION
```

## 🧪 **Testing**

### **Test DynamoDB Connection**
```bash
# Test from your container
python3 -c "
from dynamodb_adapter import db_adapter
result = db_adapter.get_user_trial_status('test@example.com', 'test-123')
print('DynamoDB test:', result)
"
```

### **Test Trial Button**
1. Sign in as `radu@lupan.ca`
2. Check button text: Should show "Try Premium - Free for 30 days"
3. Click button to start trial
4. Verify trial starts successfully

## 📊 **Cost Estimation**

### **DynamoDB Costs**
- **Users table**: ~$0.25/month for 1000 users
- **URLs table**: ~$0.50/month for 10,000 URLs
- **Total**: ~$1-2/month for small-medium usage

### **EFS Costs** (Alternative)
- **Storage**: $0.30/GB/month
- **Database file**: ~$0.03/month (100MB)

## 🔒 **Security Considerations**

### **DynamoDB Security**
- ✅ Data encrypted at rest
- ✅ Data encrypted in transit
- ✅ IAM-based access control
- ✅ VPC endpoints available

### **EFS Security**
- ✅ Data encrypted at rest/transit
- ✅ POSIX file permissions
- ⚠️ Requires VPC configuration

## 🚨 **Rollback Plan**

If DynamoDB migration fails:

1. **Immediate rollback**:
   ```bash
   # Set environment variable
   USE_DYNAMODB=false
   
   # Redeploy with SQLite + EFS
   ```

2. **Data recovery**:
   - DynamoDB tables remain intact
   - Can re-run migration script
   - SQLite backup should be available

## 📞 **Support**

If you encounter issues:

1. **Check logs**:
   ```bash
   aws logs tail /aws/ecs/fileshare-backend --follow
   ```

2. **Test database connection**:
   ```bash
   python3 -c "
   import os
   print('USE_DYNAMODB:', os.getenv('USE_DYNAMODB'))
   print('AWS_REGION:', os.getenv('AWS_REGION'))
   "
   ```

3. **Verify IAM permissions**:
   ```bash
   aws sts get-caller-identity
   aws dynamodb list-tables
   ```

---

## 🎯 **Next Steps**

1. **Today**: Deploy immediate fix with API response field
2. **This Week**: Complete DynamoDB migration
3. **Test thoroughly**: Verify trial button works correctly
4. **Monitor**: Watch for any issues post-deployment

**The trial button issue will be permanently fixed once you implement either solution!**