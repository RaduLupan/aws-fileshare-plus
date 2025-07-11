# Terraform Deployment Issues - Fixed

## Issues Resolved

### 1. S3 Lifecycle Configuration Error
**Error**: `Invalid Attribute Combination` in `aws_s3_bucket_lifecycle_configuration`

**Location**: `terraform/modules/ecs-flask-backend/s3_uploads.tf` line 39

**Problem**: The S3 lifecycle rule was missing a required `filter` block.

**Fix**: Added a `filter` block with an empty prefix to apply the lifecycle rule to all objects in the bucket:
```hcl
filter {
  prefix = ""
}
```

### 2. IAM Policy JSON Syntax Error
**Error**: `Invalid count argument` in `aws_iam_role_policy_attachment`

**Location**: `terraform/modules/ecs-flask-backend/iam.tf` line 101

**Problem**: The IAM policy JSON had syntax errors that prevented the count argument from working properly.

**Fix**: Corrected the JSON syntax in the IAM policy:
- Changed `Sid:` to `Sid =` (proper HCL syntax)
- Changed `Effect:` to `Effect =`
- Changed `Action:` to `Action =`
- Changed `Resource:` to `Resource =`
- Fixed bracket placement and comma positioning

## Files Modified

1. **terraform/modules/ecs-flask-backend/s3_uploads.tf**
   - Added `filter` block to S3 lifecycle configuration

2. **terraform/modules/ecs-flask-backend/iam.tf**
   - Fixed IAM policy JSON syntax
   - Applied proper HCL formatting

## Validation Results

- ✅ Terraform syntax validation passed
- ✅ Terraform formatting applied successfully
- ✅ Both files are now syntactically correct

## Next Steps

1. Run `terraform plan -var-file=dev.tfvars` to verify the deployment plan
2. Run `terraform apply -var-file=dev.tfvars` to deploy the infrastructure
3. Follow the DynamoDB deployment plan for backend configuration

The fixes ensure that:
- S3 lifecycle rules will properly manage file retention
- DynamoDB IAM policies will be correctly attached to the ECS task role
- The deployment can proceed without syntax errors