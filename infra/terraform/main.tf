module "vpc" {
  source = "./modules/vpc"
}

module "rds" {
  source = "./modules/rds"

  vpc_id             = module.vpc.vpc_id
  vpc_cidr           = module.vpc.vpc_cidr
  private_subnet_ids = module.vpc.private_subnet_ids
}

module "ecr" {
  source = "./modules/ecr"
}

module "eks" {
  source = "./modules/eks"

  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
}

module "secrets" {
  source = "./modules/secrets"

  jwt_secret     = var.jwt_secret
  openai_api_key = var.openai_api_key

  db_host                = module.rds.db_address
  db_username            = module.rds.db_username
  db_password_secret_arn = module.rds.master_user_secret_arn
}
