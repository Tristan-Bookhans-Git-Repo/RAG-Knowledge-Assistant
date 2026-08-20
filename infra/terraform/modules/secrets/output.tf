output "app_secret_arns" {
  description = "ARNs of the JWT_SECRET / OPENAI_API_KEY secrets, keyed by name"
  value       = { for k, v in aws_secretsmanager_secret.app : k => v.arn }
}

output "database_url_secret_arn" {
  description = "ARN of the database connection-details secret (excludes the password)"
  value       = aws_secretsmanager_secret.database_url.arn
}
