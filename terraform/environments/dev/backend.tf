terraform {
  backend "s3" {
    bucket = "file-sharing-app-terraform-state-us-east-2"
    key    = "environments/dev/terraform.tfstate"
    region = "us-east-2"
  }
}
