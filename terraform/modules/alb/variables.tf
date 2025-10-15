variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs"
  type        = list(string)
}

variable "health_check_path" {
  description = "Health check path"
  type        = string
}

variable "health_check_matcher" {
  description = "HTTP status codes for successful health checks"
  type        = string
}
