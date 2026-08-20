locals {
  app_secrets = {
    jwt_secret     = var.jwt_secret
    openai_api_key = var.openai_api_key
  }
}

resource "aws_secretsmanager_secret" "app" {
  for_each = local.app_secrets

  name        = "${var.name_prefix}/${each.key}"
  description = "Application secret: ${each.key}"

  tags = {
    Project = var.name_prefix
  }
}

resource "aws_secretsmanager_secret_version" "app" {
  for_each = local.app_secrets

  secret_id     = aws_secretsmanager_secret.app[each.key].id
  secret_string = each.value
}

resource "aws_secretsmanager_secret" "database_url" {
  name        = "${var.name_prefix}/database_url"
  description = "Database connection details, excluding password — see password_secret_arn"

  tags = {
    Project = var.name_prefix
  }
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id = aws_secretsmanager_secret.database_url.id
  secret_string = jsonencode({
    host                = var.db_host
    port                = var.db_port
    dbname              = var.db_name
    username            = var.db_username
    password_secret_arn = var.db_password_secret_arn
  })
}
