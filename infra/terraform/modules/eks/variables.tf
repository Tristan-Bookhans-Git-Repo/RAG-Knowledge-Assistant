variable "name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "rag-assistant-eks"
}

variable "kubernetes_version" {
  description = "Kubernetes version for the EKS control plane"
  type        = string
  default     = "1.33"
}

variable "vpc_id" {
  description = "ID of the VPC to create the EKS cluster in"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the EKS cluster and its managed node group"
  type        = list(string)
}

variable "node_instance_types" {
  description = "Instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_min_size" {
  description = "Minimum number of nodes in the managed node group"
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of nodes in the managed node group"
  type        = number
  default     = 4
}

variable "node_desired_size" {
  description = "Desired number of nodes in the managed node group"
  type        = number
  default     = 2
}

variable "github_actions_role_arn" {
  description = "ARN of the IAM role cd.yml assumes via OIDC — granted EKS access so kubectl commands in the deploy workflow can authenticate. Optional so this module doesn't hard-depend on github_oidc."
  type        = string
  default     = null
}
