output "db_endpoint" {
  description = "Connection endpoint for the RDS instance (host:port)"
  value       = module.db.db_instance_endpoint
}

output "db_address" {
  description = "Hostname of the RDS instance, without the port"
  value       = module.db.db_instance_address
}

output "db_username" {
  description = "Master username configured on the RDS instance"
  value       = var.username
}

output "master_user_secret_arn" {
  description = "ARN of the Secrets Manager secret holding the auto-generated master password"
  value       = module.db.db_instance_master_user_secret_arn
}

output "security_group_id" {
  description = "ID of the security group attached to the RDS instance"
  value       = aws_security_group.rds.id
}
