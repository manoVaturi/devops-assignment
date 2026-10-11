terraform {
  required_version = ">= 1.10"

  backend "s3" {
    bucket       = "mano-tf-state-bucket"
    key          = "docker-monitor/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = "docker-monitor" }
  }
}
