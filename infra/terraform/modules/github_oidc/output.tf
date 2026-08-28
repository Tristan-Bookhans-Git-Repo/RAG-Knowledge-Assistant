output "role_arn" {
  description = "ARN of the IAM role GitHub Actions assumes — set this as cd.yml's AWS_CD_ROLE_ARN secret"
  value       = aws_iam_role.github_actions.arn
}
