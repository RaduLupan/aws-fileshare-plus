aws_region         = "us-east-2"
availability_zones = ["us-east-2a", "us-east-2b"]

environment  = "dev"
project_name = "file-sharing-app"

cloudfront_custom_domain_name = "cf.aws.lupan.ca"
alb_custom_domain_name        = "alb.aws.lupan.ca"

alb_enable_https_listener         = true
alb_https_certificate_arn         = "arn:aws:acm:us-east-2:481509955802:certificate/126b4acc-63fb-49b5-b1aa-ebb8238157ce"
cloudfront_https_certificate_arn  = "arn:aws:acm:us-east-1:481509955802:certificate/947ae640-6dbb-4fff-933e-15eae8fbb7fa" # ACM cert in us-east-1 for CloudFront
cloudfront_viewer_protocol_policy = "redirect-to-https" # Change to "https-only" for production