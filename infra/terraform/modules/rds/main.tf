# PostgreSQL RDS instance with pgvector support. pgvector itself is enabled
# via `CREATE EXTENSION IF NOT EXISTS vector` in the app's own Alembic
# migration (app/db/migrations/versions/..._init_migration.py) — RDS
# allow-lists pgvector as a "trusted extension", so no parameter-group
# configuration is needed here to support it.
module "db" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = var.identifier

  engine               = var.engine
  engine_version       = var.engine_version
  family               = "postgres16" # parameter group family — must match engine_version's major version
  major_engine_version = "16"
  instance_class       = var.instance_class
  allocated_storage    = var.allocated_storage

  db_name  = var.db_name
  username = var.username
  port     = var.port

  # AWS generates and rotates the master password in its own Secrets Manager
  # secret — avoids ever storing a plaintext password in Terraform state.
  manage_master_user_password = true

  vpc_security_group_ids = [aws_security_group.rds.id]

  create_db_subnet_group = true
  subnet_ids             = var.private_subnet_ids

  maintenance_window = "Mon:00:00-Mon:03:00"
  backup_window      = "03:00-06:00"

  monitoring_interval    = 30
  monitoring_role_name   = "${var.identifier}-monitoring-role"
  create_monitoring_role = true

  deletion_protection = var.deletion_protection

  tags = {
    Project = var.identifier
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.identifier}-rds-"
  description = "Allow Postgres access from within the VPC"
  vpc_id      = var.vpc_id

  ingress {
    description = "Postgres from within the VPC"
    from_port   = var.port
    to_port     = var.port
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = var.identifier
  }
}
