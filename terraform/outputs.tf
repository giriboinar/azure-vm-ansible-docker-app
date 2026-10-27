output "public_ip" {
  description = "Public IP of the VM"
  value       = azurerm_public_ip.main.ip_address
}

output "api_url" {
  description = "Service Health API base URL"
  value       = "http://${azurerm_public_ip.main.ip_address}:8000"
}

output "resource_group_name" {
  value = azurerm_resource_group.main.name
}
