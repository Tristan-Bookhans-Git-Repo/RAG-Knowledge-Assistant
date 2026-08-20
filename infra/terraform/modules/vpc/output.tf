output "vpc_id" {
  description = "ID of the created VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC — used to scope security group ingress rules"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnet_ids" {
  description = "IDs of the private subnets — pass to the EKS and RDS modules"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "IDs of the public subnets — pass to the ALB ingress"
  value       = module.vpc.public_subnets
}
