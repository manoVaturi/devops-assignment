terraform {
  backend "s3" {
    bucket       = "mano-tf-state-bucket"
    key          = "eks/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true
  }
}
