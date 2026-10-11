variable "region" {
  type    = string
  default = "eu-west-1"
}

variable "zone_name" {
  type    = string
  default = "manovaturi.com"
}

variable "hostname" {
  type    = string
  default = "jenkins.manovaturi.com"
}

variable "app_hostname" {
  type    = string
  default = "monitor.manovaturi.com"
}

variable "app_port" {
  type    = number
  default = 8091 # nginx of the deployed stack on the Jenkins host
}

variable "instance_type" {
  type    = string
  default = "t3.medium"
}

variable "git_repo_url" {
  type    = string
  default = "https://github.com/manoVaturi/devops-assignment.git"
}
