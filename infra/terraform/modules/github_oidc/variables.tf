variable "github_org" {
  description = "GitHub organization or username that owns the repo"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name, without the org prefix"
  type        = string
}

variable "name" {
  description = "Name for the IAM role GitHub Actions assumes"
  type        = string
  default     = "rag-assistant-github-actions"
}

variable "allowed_ref" {
  description = "Git ref allowed to assume this role, e.g. refs/heads/main — cd.yml only ever runs on main, so this is scoped to exactly that, not any branch in the repo"
  type        = string
  default     = "refs/heads/main"
}
