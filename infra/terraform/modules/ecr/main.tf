module "ecr" {
  source  = "terraform-aws-modules/ecr/aws"
  version = "~> 2.0" # check the registry for the current major version

  repository_name = var.repository_name

  # No repository_read_write_access_arns set — push/pull access is governed
  # by normal account-level IAM permissions on the CD pipeline's IAM user,
  # not a repo-specific resource policy. Add it back only if you need to
  # grant access to a specific role/account beyond that.

  repository_lifecycle_policy = jsonencode({
    rules = [
      {
        rulePriority = 1,
        description  = "Keep last 30 tagged images",
        selection = {
          tagStatus      = "tagged", # every image cd.yml pushes is tagged with the commit SHA
          tagPatternList = ["*"],    # required alongside tagStatus=tagged, "*" means any tag
          countType      = "imageCountMoreThan",
          countNumber    = 30
        },
        action = {
          type = "expire"
        }
      }
    ]
  })

  tags = {
    Project = var.repository_name
  }
}
