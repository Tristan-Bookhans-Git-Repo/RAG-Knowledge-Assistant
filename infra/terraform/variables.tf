variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "af-south-1"
}

# Set these as sensitive Terraform Cloud workspace variables — never as a
# default here, and never in a committed .tfvars file.
variable "jwt_secret" {
  description = "Value for the JWT_SECRET application secret"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "Value for the OPENAI_API_KEY application secret — blank if using LLM_PROVIDER=ollama"
  type        = string
  sensitive   = true
  default     = ""
}
