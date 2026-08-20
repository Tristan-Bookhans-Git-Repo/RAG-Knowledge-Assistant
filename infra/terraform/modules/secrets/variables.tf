variable "name_prefix" {
  description = "Prefix for secret names in Secrets Manager"
  type        = string
  default     = "rag-assistant"
}

variable "jwt_secret" {
  description = "Value for the JWT_SECRET application secret — no default, must be supplied explicitly"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "Value for the OPENAI_API_KEY application secret — blank if using LLM_PROVIDER=ollama"
  type        = string
  sensitive   = true
  default     = ""
}

variable "db_host" {
  description = "RDS endpoint hostname (no port)"
  type        = string
}

variable "db_port" {
  description = "RDS port"
  type        = number
  default     = 5432
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "ragdb"
}

variable "db_username" {
  description = "Database master username"
  type        = string
}

variable "db_password_secret_arn" {
  description = "ARN of the RDS-managed master password secret (manage_master_user_password on the rds module) — the real password is never duplicated into this module's own secret, only pointed to"
  type        = string
}
