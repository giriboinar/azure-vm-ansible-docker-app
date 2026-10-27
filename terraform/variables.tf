variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "centralindia"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-service-health-api"
}

variable "admin_username" {
  description = "Admin username for the VM"
  type        = string
  default     = "azureuser"
}

variable "ssh_public_key" {
  description = "SSH public key for VM login (no default: pass your own key, never a private key)"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "Your public IP in CIDR form (for example 203.0.113.10/32) allowed to SSH in"
  type        = string
}

variable "vm_size" {
  description = "VM size (Standard_B1s is eligible for the Azure free tier allowance)"
  type        = string
  default     = "Standard_B1s"
}
