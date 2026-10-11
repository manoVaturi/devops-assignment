module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "21.29.0"

  name               = "interview-eks-cluster"
  kubernetes_version = "1.35"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  endpoint_public_access       = true
  endpoint_public_access_cidrs = var.api_allowed_cidrs

  # whoever runs terraform gets admin on the cluster
  enable_cluster_creator_admin_permissions = true

  compute_config = {
    enabled = false
  }

  # EKS already tags the cluster SG. two tagged SGs = load balancer creation fails
  node_security_group_tags = {
    "kubernetes.io/cluster/interview-eks-cluster" = null
  }
}

module "eks_managed_node_group" {
  source  = "terraform-aws-modules/eks/aws//modules/eks-managed-node-group"
  version = "21.29.0"

  name               = "general-nodes"
  cluster_name       = module.eks.cluster_name
  kubernetes_version = "1.35"

  cluster_service_cidr = module.eks.cluster_service_cidr

  subnet_ids                        = module.vpc.private_subnets
  cluster_primary_security_group_id = module.eks.cluster_primary_security_group_id
  vpc_security_group_ids            = [module.eks.node_security_group_id]

  min_size     = 1
  max_size     = 2
  desired_size = 2

  instance_types = ["t3.medium"]
  ami_type       = "AL2023_x86_64_STANDARD"

  labels = {
    environment = "interview-project"
    managed-by  = "terraform"
  }

  # nodes need the CNI and kube-proxy to become Ready
  depends_on = [
    aws_eks_addon.vpc_cni,
    aws_eks_addon.kube_proxy,
  ]
}

resource "aws_eks_addon" "vpc_cni" {
  cluster_name = module.eks.cluster_name
  addon_name   = "vpc-cni"
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name = module.eks.cluster_name
  addon_name   = "kube-proxy"
}

# coredns needs nodes to run on
resource "aws_eks_addon" "coredns" {
  cluster_name = module.eks.cluster_name
  addon_name   = "coredns"

  depends_on = [module.eks_managed_node_group]
}

# CPU metrics for the web ScaledObject
resource "aws_eks_addon" "metrics_server" {
  cluster_name = module.eks.cluster_name
  addon_name   = "metrics-server"

  depends_on = [module.eks_managed_node_group]
}
