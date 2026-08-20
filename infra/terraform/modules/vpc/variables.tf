variable "name" {
  description = "Name prefix for VPC resources"
  type        = string
  default     = "rag-assistant"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "Availability zones to spread subnets across"
  type        = list(string)
  default = ["af-south-1a", "af-south-1b", "af-south-1c"]
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets — EKS nodes and RDS live here"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets — ALB and NAT gateway live here"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}
