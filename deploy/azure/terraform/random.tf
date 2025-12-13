# ============================================================================
# Random Suffix for Unique Resource Naming
# ============================================================================
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

