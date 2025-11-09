variable "service_plan_name" {
  description = "Name of the App Service Plan"
  type        = string
}

variable "location" {
  description = "Azure region for resources"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "os_type" {
  description = "OS type for the App Service Plan"
  type        = string
  default     = "Linux"
}

variable "sku_name" {
  description = "SKU name for the App Service Plan"
  type        = string
  default     = "B1"
}

variable "api_app_name" {
  description = "Name of the API web app"
  type        = string
}

variable "web_app_name" {
  description = "Name of the web app"
  type        = string
}

variable "acr_login_server" {
  description = "ACR login server URL"
  type        = string
}

variable "acr_repository_api" {
  description = "ACR repository name for API"
  type        = string
}

variable "acr_tag_api" {
  description = "ACR tag for API"
  type        = string
  default     = "latest"
}

variable "acr_repository_web" {
  description = "ACR repository name for web"
  type        = string
}

variable "acr_tag_web" {
  description = "ACR tag for web"
  type        = string
  default     = "latest"
}

variable "api_health_check_path" {
  description = "Health check path for API app"
  type        = string
  default     = "/health"
}

variable "web_health_check_path" {
  description = "Health check path for web app"
  type        = string
  default     = "/"
}

variable "health_check_eviction_time_in_min" {
  description = "Health check eviction time in minutes"
  type        = number
  default     = 10
}

variable "api_app_settings" {
  description = "App settings for API web app"
  type        = map(string)
  default     = {}
}

variable "web_app_settings" {
  description = "App settings for web app"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

