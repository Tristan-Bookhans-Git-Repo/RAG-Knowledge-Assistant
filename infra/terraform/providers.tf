terraform {
  required_version = ">= 1.1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  cloud {
    organization = "Tristan-Bookhan-Terraform-Org"

    workspaces {
      name = "RAG-Assistant-Workspace"
    }
  }
}

provider "aws" {
  region = var.aws_region
}
