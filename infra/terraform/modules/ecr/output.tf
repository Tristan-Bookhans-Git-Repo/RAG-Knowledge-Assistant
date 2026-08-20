output "repository_url" {
  description = "Push/pull URL for the ECR repository — used by cd.yml as $ECR_REGISTRY/$ECR_REPOSITORY"
  value       = module.ecr.repository_url
}

output "repository_arn" {
  description = "ARN of the ECR repository — for scoping IAM policies to just this repo"
  value       = module.ecr.repository_arn
}
