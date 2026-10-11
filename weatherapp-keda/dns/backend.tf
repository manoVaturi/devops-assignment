terraform {
  backend "s3" {
    bucket       = "mano-tf-state-bucket"
    key          = "eks-dns/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true
  }
}
