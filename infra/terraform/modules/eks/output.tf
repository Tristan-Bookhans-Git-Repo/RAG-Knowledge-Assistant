output "cluster_name" {
  description = "Name of the EKS cluster, used by `aws eks update-kubeconfig --name`"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for the Kubernetes API server"
  value       = module.eks.cluster_endpoint
}
