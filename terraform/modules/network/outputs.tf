# outputs.tf

output "vpc_id" {
  description = "The ID of the VPC."
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "A list of IDs of the public subnets."
  value       = module.vpc.public_subnets
}

output "private_subnet_ids" {
  description = "A list of IDs of the private subnets."
  value       = module.vpc.private_subnets
}

output "alb_security_group_id" {
  description = "The ID of the security group for the ALB."
  value       = aws_security_group.alb.id
}

output "ecs_tasks_security_group_id" {
  description = "The ID of the security group for ECS tasks."
  value       = aws_security_group.ecs_tasks.id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC."
  value       = module.vpc.vpc_cidr_block
}