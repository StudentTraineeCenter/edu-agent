# Random string for unique naming
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Common locals for consistent naming
locals {
  common_tags = {
    environment = var.environment
    project     = var.project_name
  }
  
  name_prefix = "${var.project_name}-${var.environment}-${random_string.suffix.result}"
}
