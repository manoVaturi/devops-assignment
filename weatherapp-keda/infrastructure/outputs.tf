output "configure_kubectl" {
  value       = "aws eks update-kubeconfig --region ${data.aws_region.current.region} --name ${module.eks.cluster_name}"
  description = "Command to connect kubectl to the cluster"
}

output "cluster_endpoint" {
  value       = module.eks.cluster_endpoint
  description = "Kubernetes API endpoint"
}
