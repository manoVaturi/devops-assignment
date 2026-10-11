output "app_url" {
  value       = "http://${aws_route53_record.weatherapp.fqdn}"
  description = "App URL"
}
