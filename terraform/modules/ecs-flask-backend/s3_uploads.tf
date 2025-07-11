# s3_uploads.tf

# Create an S3 bucket for file uploads
resource "aws_s3_bucket" "uploads_backend" {
  bucket = lower("${var.s3_uploads_bucket_name_prefix}-${random_id.uploads_bucket_suffix.hex}")

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

# S3 Lifecycle policy to automatically delete files after retention period
resource "aws_s3_bucket_lifecycle_configuration" "uploads_backend_lifecycle" {
  bucket = aws_s3_bucket.uploads_backend.id

  rule {
    id     = "delete_old_files"
    status = "Enabled"

    # Add filter to apply to all objects
    filter {
      prefix = ""
    }

    # Delete objects after the specified retention period
    expiration {
      days = var.file_retention_days
    }

    # Also delete incomplete multipart uploads after 7 days to save costs
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    # Clean up old versions if versioning is enabled
    noncurrent_version_expiration {
      noncurrent_days = var.file_retention_days
    }
  }
}