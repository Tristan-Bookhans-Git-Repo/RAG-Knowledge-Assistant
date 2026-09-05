variable "identifier" {
  description = "The name of the RDS instance (lowercase letters, numbers, hyphens only)"
  type        = string
  default     = "rag-assistant-db"
}

variable "engine" {
  description = "The database engine to use"
  type        = string
  default     = "postgres"
}

variable "engine_version" {
  description = "The engine version to use. Major version only (e.g. \"16\"), not a pinned patch: RDS periodically retires specific patch releases, and a pinned version like \"16.1\" fails CreateDBInstance once AWS drops it. Major-version-only lets RDS resolve to whatever patch is currently available."
  type        = string
  default     = "16"
}

variable "instance_class" {
  description = "RDS instance size"
  type        = string
  default     = "db.t4g.micro" # small Graviton burstable instance — portfolio scale, not production load
}

variable "allocated_storage" {
  description = "The allocated storage in gigabytes (20 GiB is the RDS Postgres minimum)"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "The DB name to create. If omitted, no database is created initially"
  type        = string
  default     = "ragdb"
}

variable "username" {
  description = "Username for the master DB user"
  type        = string
  default     = "raguser"
}

variable "port" {
  description = "The port on which the DB accepts connections"
  type        = number
  default     = 5432
}

variable "deletion_protection" {
  description = "Whether to enable RDS deletion protection"
  type        = bool
  default     = true
}

variable "vpc_id" {
  description = "ID of the VPC to create the RDS security group in"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC — security group ingress is scoped to this range"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the DB subnet group — RDS must never sit in a public subnet"
  type        = list(string)
}
