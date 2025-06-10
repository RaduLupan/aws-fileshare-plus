# main.tf

# Create a CloudFront distribution for the React app
resource "aws_cloudfront_distribution" "this" {
  
  # S3 bucket as the origin (for static content)
  origin {
    domain_name              = aws_s3_bucket.this.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.this.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.this.id
  }

  # NEW: ALB Origin (for API calls)
  origin {
    domain_name = var.backend_alb_dns_name # This variable will be passed from the environment
    origin_id   = "ALB-Origin-${var.environment}" # A unique ID for this origin

    custom_origin_config {
      http_port              = var.alb_http_port # Pass this variable into the module
      https_port             = var.alb_https_port # Pass this variable into the module
      origin_protocol_policy = "https-only" # CloudFront will talk to your ALB over HTTPS
      origin_ssl_protocols   = ["TLSv1.2"]
      # You may need to add or adjust allowed headers, e.g., origin_read_timeout_seconds if needed
    }
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
  
  # NEW: Ordered Cache Behavior for API calls (to route to ALB origin)
  # This must be *before* the default behavior in priority.
  ordered_cache_behavior {
    path_pattern           = "/api/*" # All requests starting with /api/ will go here
    target_origin_id       = "ALB-Origin-${var.environment}" # Reference the ALB origin ID
    viewer_protocol_policy = "redirect-to-https" # Force HTTPS from browser to CloudFront for API calls too
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"] # Cache OPTIONS, GET, HEAD
    compress               = true

    # Forward all headers, query strings, and cookies to the API backend
    # This is crucial for POST requests, CORS, and any session handling
    forwarded_values {
      query_string = true
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method", "Host"] # Host header is important for ALB routing
      cookies {
        forward = "all"
      }
    }

    # API endpoints should typically not be cached, or have very short TTLs
    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
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