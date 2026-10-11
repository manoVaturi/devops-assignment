variable "lb_hostname" {
  type        = string
  description = "Load balancer hostname of the weatherapp service"
}

variable "hosted_zone" {
  type        = string
  default     = "manovaturi.com"
  description = "Route 53 hosted zone"
}

variable "app_domain" {
  type        = string
  default     = "weatherapp.manovaturi.com"
  description = "Domain for the app"
}
