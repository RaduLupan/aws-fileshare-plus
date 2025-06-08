# s3_uploads.tf

# Create an S3 bucket for file uploads
resource "aws_s3_bucket" "uploads_backend" {
  bucket = "${var.s3_uploads_bucket_name_prefix}-${random_id.uploads_bucket_suffix.hex}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-file-uploads"
    Service     = "Backend"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Ensure the uploads bucket is not publicly accessible
resource "aws_s3_bucket_public_access_block" "uploads_backend_public_access_block" {
  bucket = aws_s3_bucket.uploads_backend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning on the S3 bucket (good for data protection)
resource "aws_s3_bucket_versioning" "uploads_backend_versioning" {
  bucket = aws_s3_bucket.uploads_backend.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Random suffix for the uploads bucket name
resource "random_id" "uploads_bucket_suffix" {
  byte_length = 6
}