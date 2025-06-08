# main.tf

# Create a CloudFront distribution for the React app
resource "aws_cloudfront_distribution" "this" {
  origin {
    domain_name              = aws_s3_bucket.this.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.this.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.this.id
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = var.cloudfront_comment
  default_root_object = "index.html" # Your React app's entry point

  # Define default cache behavior
  default_cache_behavior {
    target_origin_id       = "S3-${aws_s3_bucket.this.id}"
    viewer_protocol_policy = var.viewer_protocol_policy # Controlled by variable
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    forwarded_values {
      query_string = false
      headers      = []
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }

  custom_error_response {
    error_code         = 403
    response_page_path = "/index.html"
    response_code      = 200
  }

  custom_error_response {
    error_code         = 404
    response_page_path = "/index.html"
    response_code      = 200
  }

  aliases = var.custom_domain_name != "" ? [var.custom_domain_name] : []

  viewer_certificate {
    cloudfront_default_certificate = var.custom_domain_name == "" ? true : false
    acm_certificate_arn            = var.custom_domain_name != "" ? var.acm_certificate_arn : null
    ssl_support_method             = "sni-only"
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
      locations        = []
    }
  }

  tags = {
    Environment = var.environment
    Service     = "Frontend"
  }
}