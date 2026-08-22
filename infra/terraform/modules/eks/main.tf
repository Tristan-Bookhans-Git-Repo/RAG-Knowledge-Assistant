module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = var.name
  kubernetes_version = var.kubernetes_version

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  compute_config = {
    enabled = false
  }

  eks_managed_node_groups = {
    general = {
      instance_types = var.node_instance_types
      min_size       = var.node_min_size
      max_size       = var.node_max_size
      desired_size   = var.node_desired_size
    }
  }

  # Grants cd.yml's OIDC role enough Kubernetes RBAC to run `kubectl set
  # image` / `rollout status` — IAM policies alone don't grant this, EKS
  # requires this separate principal-to-RBAC mapping (the modern "access
  # entries" API, replacing the older aws-auth ConfigMap approach).
  access_entries = var.github_actions_role_arn == null ? {} : {
    github_actions = {
      principal_arn = var.github_actions_role_arn
      policy_associations = {
        deploy = {
          policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy"
          access_scope = {
            type = "cluster"
          }
        }
      }
    }
  }

  tags = {
    Project = var.name
  }
}
