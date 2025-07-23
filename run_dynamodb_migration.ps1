# PowerShell script to run DynamoDB migration
# This script sets up the DynamoDB tables for the trial system

Write-Host "🚀 Starting DynamoDB Migration for AWS FileShare Plus" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

# Set environment variables
$env:AWS_REGION = "us-east-1"
$env:PROJECT_NAME = "aws-fileshare-plus"
$env:ENVIRONMENT = "prod"

Write-Host "📍 Using AWS Region: $env:AWS_REGION" -ForegroundColor Yellow
Write-Host "📋 Project: $env:PROJECT_NAME" -ForegroundColor Yellow
Write-Host "🌍 Environment: $env:ENVIRONMENT" -ForegroundColor Yellow
Write-Host ""

# Change to backend directory
Set-Location -Path "backend"

# Run the migration script
Write-Host "🔨 Running DynamoDB migration..." -ForegroundColor Green
python dynamodb_migration.py

# Check if migration was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Migration completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Next steps:" -ForegroundColor Cyan
    Write-Host "1. Deploy the updated Terraform configuration"
    Write-Host "2. The ECS task will now use DynamoDB instead of SQLite"
    Write-Host "3. Test the trial functionality with a new user"
} else {
    Write-Host ""
    Write-Host "❌ Migration failed. Please check the errors above." -ForegroundColor Red
    exit 1
}

# Return to original directory
Set-Location -Path ".." 