# main.tf

# Create a VPC with public and private subnets using the community module
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "${var.project_name}-${var.environment}-vpc"
  cidr = var.vpc_cidr

  azs = var.availability_zones

  # Dynamically generate subnet CIDRs if not provided, ensuring they are unique within the VPC CIDR
  public_subnets = length(var.public_subnet_cidrs) > 0 ? var.public_subnet_cidrs : [
    cidrsubnet(var.vpc_cidr, 8, 0), # 10.0.0.0/24 if vpc_cidr is 10.0.0.0/16
    cidrsubnet(var.vpc_cidr, 8, 1)  # 10.0.1.0/24
  ]
  private_subnets = length(var.private_subnet_cidrs) > 0 ? var.private_subnet_cidrs : [
    cidrsubnet(var.vpc_cidr, 8, 2), # 10.0.2.0/24
    cidrsubnet(var.vpc_cidr, 8, 3)  # 10.0.3.0/24
  ]

  enable_nat_gateway         = var.enable_nat_gateway
  single_nat_gateway         = var.single_nat_gateway
  manage_default_network_acl = true # This is good practice

  tags = {
    Terraform   = "true"
    Environment = var.environment
    Project     = var.project_name
  }
}