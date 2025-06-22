#!/bin/pwsh
# Script to extract Cognito values from AWS SSM Parameter Store and save them to .env file

# Set environment - can be passed as a parameter
param (
    [string]$Environment = "dev"
)

# Define AWS region
$region = "us-east-2"

# Fetch parameters from SSM Parameter Store
Write-Output "Fetching parameters from AWS SSM Parameter Store for environment: $Environment"

function Get-SSMParameter {
    param (
        [string]$ParamName
    )
    $fullPath = "/fileshare/$Environment/$ParamName"
    try {
        $param = aws ssm get-parameter --name $fullPath --query "Parameter.Value" --output text
        return $param
    }
    catch {
        Write-Error "Failed to retrieve parameter $fullPath"
        return $null
    }
}

# Get the necessary parameters
$userPoolId = Get-SSMParameter -ParamName "user_pool_id"
$userPoolClientId = Get-SSMParameter -ParamName "user_pool_client_id"
$cloudfrontDomain = Get-SSMParameter -ParamName "cloudfront_custom_domain_url"
$backendApiUrl = Get-SSMParameter -ParamName "backend_alb_url"

if (!$userPoolId -or !$userPoolClientId) {
    Write-Error "Failed to retrieve required parameters from SSM"
    exit 1
}

# Create or update .env file
$content = @"
# AWS Cognito Configuration
VITE_USER_POOL_ID=$userPoolId
VITE_USER_POOL_CLIENT_ID=$userPoolClientId
VITE_AWS_REGION=$region
VITE_CLOUDFRONT_CUSTOM_DOMAIN_URL=$cloudfrontDomain
VITE_BACKEND_API_URL=$backendApiUrl
"@

# Save the file
$content | Out-File -FilePath ".\.env" -Encoding utf8
Write-Output "Environment file created with values from AWS SSM Parameter Store."
Write-Output "You can now run 'npm start' or 'npm run dev' to start development."
