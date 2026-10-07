variable "region" { default = "ap-south-1" }
variable "project" { default = "urlshort" }
variable "instance_type" { default = "m7i-flex.large" }
variable "admin_cidr" {
  description = "Your IP in CIDR form, allowed for SSH and the Kubernetes API"
  type        = string
}
variable "public_key_path" { default = "~/.ssh/urlshort.pub" }
