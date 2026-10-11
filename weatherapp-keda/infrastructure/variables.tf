variable "api_allowed_cidrs" {
  type        = list(string)
  default     = ["0.0.0.0/0"]
  description = "CIDRs allowed to reach the Kubernetes API, e.g. [\"1.2.3.4/32\"]"
}
