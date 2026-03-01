################################################################################
# terraform/modules/lightsail/variables.tf
################################################################################

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "lightsail_power" {
  description = "Lightsail container service power level. Controls vCPU + RAM per node."
  type        = string
  default     = "nano"   # nano=$7/mo (0.25 vCPU, 512 MB) | micro=$10 | small=$25 | medium=$50

  validation {
    condition     = contains(["nano", "micro", "small", "medium", "large", "xlarge"], var.lightsail_power)
    error_message = "Must be one of: nano, micro, small, medium, large, xlarge."
  }
}

variable "lightsail_scale" {
  description = "Number of compute nodes (containers) to run. 1 for dev/staging, 2+ for production HA."
  type        = number
  default     = 1
}
