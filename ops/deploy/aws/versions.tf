terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Auth via the standard AWS chain (env vars, shared config, SSO, instance role).
provider "aws" {
  region = var.region
}
