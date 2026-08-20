output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets (EKS nodes, RDS)"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets (ALB, NAT gateway)"
  value       = module.vpc.public_subnet_ids
}

output "db_endpoint" {
  description = "Connection endpoint for the RDS instance (host:port)"
  value       = module.rds.db_endpoint
}

output "db_master_user_secret_arn" {
  description = "ARN of the Secrets Manager secret holding the RDS master password"
  value       = module.rds.master_user_secret_arn
}

output "ecr_repository_url" {
  description = "Push/pull URL for the ECR repository"
  value       = module.ecr.repository_url
}

output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint for the Kubernetes API server"
  value       = module.eks.cluster_endpoint
}

output "app_secret_arns" {
  description = "ARNs of the JWT_SECRET / OPENAI_API_KEY secrets"
  value       = module.secrets.app_secret_arns
}

output "database_url_secret_arn" {
  description = "ARN of the database connection-details secret (excludes the password)"
  value       = module.secrets.database_url_secret_arn
}
