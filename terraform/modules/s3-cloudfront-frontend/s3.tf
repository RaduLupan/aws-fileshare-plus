# s3.tf

# Create an S3 bucket for the React frontend
resource "aws_s3_bucket" "this" {
  bucket = "${var.bucket_name_prefix}-${random_id.bucket_suffix.hex}"
  tags = {
    Environment = var.environment
    Service     = "Frontend"
  }
}

# S3 Bucket Public Access Block (Recommended for all S3 buckets)
resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Policy to allow CloudFront OAC access
resource "aws_s3_bucket_policy" "this" {
  bucket = aws_s3_bucket.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.this.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.this.arn
          }
        }
      },
    ]
  })
}

# Random suffix to ensure unique bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 8
}