# Lets cd.yml assume an AWS role via short-lived OIDC tokens instead of the
# long-lived AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY secrets it currently
# uses. GitHub issues a signed OIDC token to the workflow run; AWS verifies
# it against this identity provider and, if the trust conditions below
# match, hands back temporary credentials. Nothing long-lived ever sits in
# GitHub secrets for this identity.

data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github.certificates[0].sha1_fingerprint]
}

resource "aws_iam_role" "github_actions" {
  name = var.name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          # Restricts which repo AND which ref can assume this role — not
          # any GitHub Actions run anywhere, only this repo's own main branch.
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:ref:${var.allowed_ref}"
          }
        }
      }
    ]
  })

  tags = {
    Project = var.name
  }
}

# Scoped to exactly what cd.yml does: push images to ECR. EKS access is
# handled separately via the cluster's own access entries (see the eks
# module), since IAM policies alone don't grant kubectl-level permissions —
# EKS requires a separate mapping between the IAM principal and Kubernetes
# RBAC, which is a different mechanism from a plain policy attachment.
resource "aws_iam_role_policy_attachment" "ecr_push" {
  role       = aws_iam_role.github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser"
}
