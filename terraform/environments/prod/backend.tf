terraform {
  backend "s3" {
    bucket = "file-sharing-app-terraform-state-us-east-2"
    key    = "environments/prod/terraform.tfstate"
    region = "us-east-2"
  }
}
