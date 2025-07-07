# FileShare - A Simple File Sharing Application

## Overview

FileShare is a minimalist web application designed to allow users to easily upload files and share them via a unique download link. This project serves as a proof-of-concept (MVP) demonstrating a full-stack deployment on AWS using React for the frontend, Flask for the backend, and Terraform for infrastructure as code.

### Key Features (MVP)

* **File Uploads:** Users can select a file from their local machine and upload it.
* **Unique Download Links:** Upon successful upload, a unique, time-limited download URL is generated for sharing.
* **Cloud-Native Architecture:** Deployed entirely on AWS, leveraging managed services for scalability and reliability.

## Architecture

The application is composed of three main components:

1.  **Frontend (React App):** A static single-page application (SPA) providing the user interface for file uploads.
2.  **Backend (Flask API):** A Python Flask application handling file uploads to S3, generating presigned download URLs, and acting as the API layer.
3.  **Infrastructure (Terraform):** All AWS resources are provisioned and managed using Terraform.

## Architecture Flow Diagram

```
+----------------+    +-------------------+    +-----------------+
|                |    |                   |    |                 |
| User Browser   +--> | CloudFront (CDN)  +--> | S3 (Frontend)   |
| (HTTP Access)  |    |                   |    | (Static Hosting)|
|                |    |                   |    | (React App)     |
+----------------+    +-------------------+    +-----------------+
                                                        |         
                                                        |         
                                                        | API Calls (HTTP)
                                                        | (via Submit button)
                                                        |         
                                                        v         
                                               +----------------+    +-------------------+
                                               |                |    |                   |
                                               | ALB (Load      +--> | ECS Fargate       |
                                               | Balancer)      |    | (Backend API)     |
                                               | (HTTP Listener)|    | (Flask App)       |
                                               |                |    |                   |
                                               +----------------+    +-------------------+
                                                        |                        |         
                                                        |                        |         
                                                        |            +-----------+         
                                                        |            |                     
                                                        |            v                     
                                                        |    +----------------+            
                                                        |    |                |            
                                                        +--> | S3 (Uploads)   |            
                                                             | (File Storage) |            
                                                             | (Backend       |            
                                                             | Module)        |            
                                                             |                |            
                                                             +----------------+            
```

## Traffic Flow Description

1. **User Browser** makes HTTP requests to **CloudFront (CDN)**.
2. **CloudFront (CDN)** serves the React application from **S3 (Frontend)** static hosting.
3. **React App** (running in user's browser) makes API calls directly to **ALB (Load Balancer)** when users interact with forms.
4. **ALB (Load Balancer)** receives API calls and distributes them to **ECS Fargate** containers.
5. **ECS Fargate (Backend API)** processes requests and interacts with **S3 (Uploads)** for file storage operations.

### AWS Services Used

* **Amazon S3:** For hosting the static React frontend and storing uploaded files.
* **Amazon CloudFront:** Content Delivery Network (CDN) to serve the frontend quickly and globally.
* **Amazon ECS (Fargate):** Container orchestration for deploying the Flask backend without managing servers.
* **Amazon EC2 Container Registry (ECR):** Docker image repository for the Flask backend.
* **Amazon EC2 Application Load Balancer (ALB):** Distributes traffic to the Flask API.
* **Amazon VPC:** Isolated network environment for AWS resources.
* **AWS IAM:** Identity and Access Management for secure permissions.
* **AWS CloudWatch Logs:** For centralized logging of the Flask application.

## Getting Started

### Prerequisites

* **AWS Account:** With sufficient permissions to create the listed resources.
* **AWS CLI:** Configured with your AWS credentials.
* **Terraform CLI:** Version 1.0.0 or higher.
* **Node.js & npm/yarn:** For building the React frontend.
* **Docker:** For building and pushing the Flask backend image.
* **Python 3 & pip:** For Flask development.

### Local Development

#### 1. Backend (Flask API)

Navigate to the `backend/` directory.

```bash
cd backend/
pip install -r requirements.txt
# For local testing with S3, you might need to set these env vars
# export S3_BUCKET_NAME="your-local-dev-s3-bucket"
# export AWS_REGION="your-aws-region"
flask run --host=0.0.0.0 --port=5000
```

The Flask API will be accessible at `http://localhost:5000`.

#### 2. Frontend (React App)

Navigate to the `frontend/` directory.

```bash
cd frontend/
npm install
npm start
```

The React app will typically open in your browser at `http://localhost:3000`. You will need to update `frontend/src/UploadForm.js` to point to your local Flask backend URL (`http://localhost:5000`) for local testing.

### Deployment to AWS

#### 1. Infrastructure Setup (Terraform)

Navigate to the `terraform/environments/dev/` directory.

```bash
cd terraform/environments/dev/
```

Initialize Terraform:

```bash
terraform init
```

Plan and Apply Infrastructure:

Review the plan before applying. Set `desired_count = 0` in `terraform/modules/ecs-flask-backend/variables.tf` (or override in `environments/dev/main.tf`) for the initial deployment, as the Docker image won't be in ECR yet.

```bash
terraform plan
terraform apply
```

#### 2. Backend Docker Image Build & Push

Once Terraform applies, an ECR repository will be created.

```bash
# Get the ECR repository URL
cd ../../
ECR_REPO_URL=<span class="math-inline">\(terraform \-chdir\=terraform/environments/dev output \-raw backend\_app\.ecr\_repository\_url\)
AWS\_REGION\=</span>(terraform -chdir=terraform/environments/dev output -raw aws_region) # Get the region output

# Navigate to your backend application directory
cd backend/

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(echo $ECR_REPO_URL | awk -F'.' '{print $1}')

# Build your Docker image
docker build -t file-share-flask-app .

# Tag and push the image to ECR
docker tag file-share-flask-app:latest "$ECR_REPO_URL:latest"
docker push "$ECR_REPO_URL:latest"
```

#### 3. Update ECS Service (Desired Count)

Now that the image is in ECR, `update desired_count` in `terraform/modules/ecs-flask-backend/variables.tf` (or override in `environments/dev/main.tf`) to your desired number of tasks (e.g., `1` or `2`).

```bash
cd terraform/environments/dev/
terraform apply
```

Alternatively, you can force a new deployment via AWS CLI:

```bash
CLUSTER_ID=<span class="math-inline">\(terraform \-chdir\=terraform/environments/dev output \-raw backend\_app\.ecs\_cluster\_id\)
SERVICE\_NAME\=</span>(terraform -chdir=terraform/environments/dev output -raw backend_app.ecs_service_name)
aws ecs update-service --cluster $CLUSTER_ID --service $SERVICE_NAME --force-new-deployment
```

#### Frontend Build & Deploy

The frontend needs to know the ALB URL of the backend.

```bash
# Get the ALB URL from Terraform output
cd terraform/environments/dev/
ALB_URL=<span class="math-inline">\(terraform output \-raw backend\_alb\_url\) \# This will be the HTTP URL for now
FRONTEND\_S3\_BUCKET\=</span>(terraform output -raw frontend_app.s3_bucket_name)
CLOUDFRONT_DIST_ID=$(terraform output -raw frontend_app.cloudfront_distribution_id)

# Navigate to your frontend application directory
cd ../../frontend/

# Set the environment variable and build the React app
# IMPORTANT: REACT_APP_ prefix is mandatory for Create React App
# Note: For production, you'd likely use the HTTPS ALB URL here.
REACT_APP_BACKEND_API_URL="$ALB_URL" npm run build

# Sync the build folder to your S3 bucket
aws s3 sync ./build/ "s3://$FRONTEND_S3_BUCKET" --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id "$CLOUDFRONT_DIST_ID" --paths "/*"
```

### Accessing the Application

Once all steps are complete, you can access your frontend application via the CloudFront distribution URL:

```bash
cd terraform/environments/dev/
terraform output frontend_url
```

### Important Notes (Current MVP Limitations)

* **HTTP Only for Backend:** Currently, the backend API is served over HTTP. This means the frontend also connects via HTTP. For production, HTTPS is highly recommended for all traffic.
* **CORS Configuration:** CORS is currently set to allow all origins in the Flask app for testing. This should be restricted to your CloudFront domain in a production environment.
* **No Authentication/Authorization:** There is no user authentication or authorization in this MVP.
* **No Database:** File metadata (like associated emails) is not persisted in a database.
* **No File Expiration Logic (beyond Presigned URL):** Files uploaded to S3 will persist indefinitely unless manually deleted or lifecycle policies are applied. The download link itself has a 1-hour expiry.

## Recommended Next Steps (Post-MVP)

1. **Implement HTTPS for ALB:** Secure your backend API with an SSL certificate. This is critical for production.
2. **Custom Domain & SSL:** Configure a custom domain for your frontend and backend, serving all content over HTTPS (e.g., `app.yourdomain.com`).
3. **Database Integration:** Store file metadata (email, filename, S3 key, expiration) in a database (e.g., Amazon RDS, DynamoDB).
4. **User Authentication:** Add user login/signup for secure file management.
5. **Enhanced File Management:** Implement features like viewing uploaded files, deleting files, setting custom expiry times, or sharing with specific users.
6. **CI/CD Pipeline:** Automate the build, test, and deployment process (e.g., with GitHub Actions, AWS CodePipeline).
7. **Error Handling & Monitoring:** Improve error handling in both frontend and backend, add more robust logging and monitoring (e.g., with CloudWatch Alarms).
8. **Cost Optimization:** Implement S3 lifecycle policies for uploaded files (e.g., move to Glacier after a period, delete after X days).

## 🎉 Milestone: Premium File Explorer Complete (July 6, 2025)

### ✅ Core Features Working
- **User Authentication**: Complete AWS Cognito integration with auto-confirmation in dev environment
- **File Upload**: Users can upload files to user-specific S3 folders
- **File Download**: Generated presigned URLs work with special characters (including "&", quotes, etc.)
- **Premium File Explorer**: Full file management system for Premium users
- **Password Reset**: Complete forgot password flow with email verification
- **Custom Email Domain**: SES integration with Route 53 DNS automation
- **Infrastructure**: Full Terraform deployment with ECS, ALB, CloudFront, and S3
- **Security**: JWT validation, CORS properly configured, user isolation in S3

### 🎯 Premium File Explorer Features
- **File Listing**: View all uploaded files with timestamps and download counts
- **Link Management**: Generate new download links for existing files (max 7 days)
- **File Deletion**: Remove files from S3 storage permanently
- **Real-time Updates**: Refresh functionality to see latest file status
- **Tier-based Access**: Premium-only feature with automatic free upgrades for testing

### 🔧 Technical Achievements
- **Email-based Storage**: Changed S3 folder structure from GUID to `user@email.com/filename`
- **S3 Lifecycle Management**: Automatic file deletion after 30 days (configurable)
- **File Name Sanitization**: Backend automatically replaces problematic characters for safe S3 storage
- **Robust URL Handling**: Uses standard `encodeURIComponent`/`unquote` for reliable parameter passing
- **Premium Backend APIs**: Secure endpoints for file listing, link generation, and deletion
- **SES Custom Domain**: Professional email delivery with automated DNS setup
- **Production-Ready**: GitHub Actions workflows for automated deployment

### 📁 Current Architecture Status
```
✅ Frontend (React + Vite) → CloudFront → S3
✅ Backend (Flask) → ECS Fargate → ALB  
✅ Authentication → AWS Cognito with password reset
✅ Email Delivery → SES with custom domain + Route 53
✅ File Storage → S3 with user folders (email-based)
✅ File Management → Premium File Explorer (list/renew/delete)
✅ S3 Lifecycle → Auto-delete after 30 days
✅ Infrastructure → Terraform modules
✅ CI/CD → GitHub Actions
```

### 🎯 Completed Premium Features
1. ✅ **File Explorer Interface**: Clean UI for managing uploaded files
2. ✅ **File Listing**: View all files with metadata (size, upload date, expiry)
3. ✅ **Link Renewal**: Generate new download links for existing files
4. ✅ **File Deletion**: Permanently remove files from S3
5. ✅ **Real-time Updates**: Refresh functionality for latest file status
6. ✅ **Premium Access Control**: Tier-based feature restriction

### 🚀 Next Steps for Enhancement
1. **URL Shortening Service**: Fix Email Link functionality with short URLs (next major feature)
2. **Payment Integration**: Implement actual Premium paywall (currently free upgrade)
3. **File Sharing**: Allow Premium users to share files with other users
4. **Advanced Search**: Filter files by date, type, size
5. **Bulk Operations**: Multi-select for batch delete/renewal
6. **File Versioning**: Keep multiple versions of the same file
7. **Analytics Dashboard**: File access statistics and usage metrics

### ⚠️ Known Issues (v0.6.1)
#### Email Link Functionality
- **Problem**: Email Link buttons don't open email client reliably
- **Root Cause**: CloudFront download URLs are too long (~1500+ characters) for mailto protocol
- **Workaround**: Use "Copy Link" then paste manually into email
- **Planned Fix**: URL shortening service (internal) to create short links like `cf.aws.lupan.ca/s/abc123`
- **Implementation**: Phase 1 of next development cycle

---
