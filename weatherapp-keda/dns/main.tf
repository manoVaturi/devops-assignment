# lb is created by the k8s service, so the hostname is passed as a variable
data "aws_route53_zone" "this" {
  name = var.hosted_zone
}

resource "aws_route53_record" "weatherapp" {
  zone_id = data.aws_route53_zone.this.zone_id
  name    = var.app_domain
  type    = "CNAME"
  ttl     = 60
  records = [var.lb_hostname]
}
