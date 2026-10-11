output "url" {
  value = "https://${var.hostname}/"
}

output "webhook_url" {
  value = "https://${var.hostname}/github-webhook/"
}

output "ssm_session" {
  value = "aws ssm start-session --region ${var.region} --target ${aws_instance.jenkins.id}"
}

output "app_url" {
  value = "https://${var.app_hostname}/"
}
