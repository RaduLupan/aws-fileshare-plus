# oac.tf

# Create a CloudFront Origin Access Control (OAC)
resource "aws_cloudfront_origin_access_control" "this" {
  name                              = "${var.bucket_name_prefix}-oac-${random_id.oac_suffix.hex}" # Include a random suffix for uniqueness
  description                       = "OAC for S3 frontend bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Random suffix for OAC name
resource "random_id" "oac_suffix" {
  byte_length = 4
}