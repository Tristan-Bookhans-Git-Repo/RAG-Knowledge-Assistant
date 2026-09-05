module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = var.name
  kubernetes_version = var.kubernetes_version

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  # Module default is private-only (endpoint_public_access = false), which
  # blocks kubectl/helm run from an operator's own machine, needed by every
  # remaining runbook step (manifest apply, migration exec, LB controller
  # install), not just diagnostics. Open to 0.0.0.0/0 rather than a specific
  # CIDR: the real auth boundary is IAM + the EKS access entry, not network
  # reachability, and this cluster only exists for the duration of a single
  # apply/destroy cycle (ADR-007).
  endpoint_public_access = true

  # Without these, kube-system stays empty and every node sits at
  # NotReady/NetworkPluginNotReady forever, regardless of instance type or
  # size. `before_compute = true` on vpc-cni makes the node group wait for
  # the CNI addon before launching nodes, avoiding that exact race.
  addons = {
    coredns    = {}
    kube-proxy = {}
    vpc-cni = {
      before_compute = true
    }
  }

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

  tags = {
    Project = var.name
  }
}

# Grants cd.yml's OIDC role enough Kubernetes RBAC to run `kubectl set image`
# / `rollout status`. IAM policies alone don't grant this, EKS requires this
# separate principal-to-RBAC mapping (the modern "access entries" API,
# replacing the older aws-auth ConfigMap approach).
#
# Declared as standalone resources, not via the eks module's own
# `access_entries` variable: that variable's for_each keys are computed from
# an internal merge that becomes unknown-at-plan-time once one of the ARNs
# (github_actions_role_arn here) comes from a resource created in the same
# apply, which fails plan with "Invalid for_each argument". A `count`
# conditioned on `var.github_actions_role_arn == null` hits the same problem
# one level up (the ARN is unknown at plan time, so the comparison itself is
# unknown), so this is unconditional instead, matching how the variable is
# actually used: main.tf always passes a real ARN, never null.
resource "aws_eks_access_entry" "github_actions" {
  cluster_name  = module.eks.cluster_name
  principal_arn = var.github_actions_role_arn
}

resource "aws_eks_access_policy_association" "github_actions_deploy" {
  cluster_name  = module.eks.cluster_name
  principal_arn = var.github_actions_role_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy"

  access_scope {
    type = "cluster"
  }
}
