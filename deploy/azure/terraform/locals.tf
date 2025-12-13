# ============================================================================
# Common Locals for Consistent Naming (CAF Naming Convention)
# ============================================================================
locals {
  common_tags = {
    environment = var.environment
    project     = var.project_name
    ManagedBy   = "terraform"
  }

  # CAF naming components
  org_short     = replace(var.project_name, "-", "")
  env_short     = var.environment == "prod" ? "prd" : (var.environment == "staging" ? "stg" : "dev")
  region_short  = var.region_code
  instance      = random_string.suffix.result

  # CAF naming patterns following Azure naming conventions
  # Resource Group: rg-{org}-{env}-{region}
  resource_group_name = "rg-${local.org_short}-${local.env_short}-${local.region_short}"

  # Storage Account: st{org}{env}{region}{instance} (no hyphens, lowercase, max 24 chars)
  storage_account_name = lower(substr("st${local.org_short}${local.env_short}${local.region_short}${local.instance}", 0, 24))

  # Container Registry: cr{org}{env}{region}{instance} (no hyphens, lowercase, max 50 chars)
  acr_name = lower(substr("cr${local.org_short}${local.env_short}${local.region_short}${local.instance}", 0, 50))

  # Key Vault: kv-{org}-{env}-{region}-{instance} (max 24 chars, ensure no trailing hyphen)
  key_vault_name = replace(substr("kv-${local.org_short}-${local.env_short}-${local.region_short}-${local.instance}", 0, 24), "/-$/", "")

  # App Service Plan: asp-{org}-{env}-{region}-{instance} (max 40 chars)
  app_service_plan_name = substr("asp-${local.org_short}-${local.env_short}-${local.region_short}-${local.instance}", 0, 40)

  # Container App: ca{org}{env}{region}{instance} (max 32 chars, lowercase alphanumeric and hyphens only)
  api_container_app_name = lower(substr("ca${local.org_short}${local.env_short}${local.region_short}api${local.instance}", 0, 32))
  worker_container_app_name = lower(substr("ca${local.org_short}${local.env_short}${local.region_short}wrk${local.instance}", 0, 32))
  container_app_environment_name = lower(substr("cae${local.org_short}${local.env_short}${local.region_short}${local.instance}", 0, 32))

  # App Services: app-{org}-{env}-{region}-web-{instance} (max 60 chars)
  web_app_name    = substr("app-${local.org_short}-${local.env_short}-${local.region_short}-web-${local.instance}", 0, 60)

  # Database: sql-{org}-{env}-{region}-{instance} (max 63 chars)
  database_server_name = substr("sql-${local.org_short}-${local.env_short}-${local.region_short}-${local.instance}", 0, 63)
  database_name        = substr("sqldb-${local.org_short}-${local.env_short}-${local.region_short}-${local.instance}", 0, 63)

  # AI Foundry Hub: aif-{org}-{env}-{region}-{instance} (max 64 chars)
  ai_foundry_hub_name = substr("aif-${local.org_short}-${local.env_short}-${local.region_short}-${local.instance}", 0, 64)

  # Application Insights: appi-{org}-{env}-{region}-{instance} (max 260 chars)
  app_insights_name = substr("appi-${local.org_short}-${local.env_short}-${local.region_short}-${local.instance}", 0, 260)

  # Log Analytics Workspace: law-{org}-{env}-{region}-{instance} (max 63 chars)
  log_analytics_workspace_name = substr("law-${local.org_short}-${local.env_short}-${local.region_short}-${local.instance}", 0, 63)

  # AI Secrets configuration
  ai_secrets = {
    "azure-openai-api-key" = {
      value = data.azurerm_cognitive_account.ai_foundry_keys.primary_access_key
      depends_on_ai = true
    }
    "azure-openai-endpoint" = {
      value = azapi_resource.ai_foundry_account.output.properties.endpoint
      depends_on_ai = true
    }
    "azure-openai-default-model" = {
      value = azapi_resource.model_deployments["gpt4o"].name
      depends_on_ai = true
    }
    "azure-openai-embedding-deployment" = {
      value = azapi_resource.model_deployments["text-embedding-3-large"].name
      depends_on_ai = true
    }
    "azure-openai-chat-deployment" = {
      value = azapi_resource.model_deployments["gpt4o"].name
      depends_on_ai = true
    }
    "azure-openai-api-version" = {
      value = "2024-06-01"
      depends_on_ai = false
    }
    "azure-cu-endpoint" = {
      value = azapi_resource.ai_foundry_account.output.properties.endpoint
      depends_on_ai = true
    }
    "azure-cu-key" = {
      value = data.azurerm_cognitive_account.ai_foundry_keys.primary_access_key
      depends_on_ai = true
    }
    "azure-cu-analyzer-id" = {
      value = "prebuilt-documentAnalyzer"
      depends_on_ai = false
    }
  }

  # Supabase Secrets configuration
  supabase_secrets = {
    "supabase-url" = {
      value = "https://${supabase_project.main.id}.supabase.co"
    }
    "supabase-service-role-key" = {
      value = var.supabase_service_role_key != null ? var.supabase_service_role_key : "MANUAL_UPDATE_REQUIRED"
    }
    "supabase-jwt-secret" = {
      value = var.supabase_jwt_secret != null ? var.supabase_jwt_secret : "MANUAL_UPDATE_REQUIRED"
    }
    "supabase-anon-key" = {
      value = var.supabase_anon_key != null ? var.supabase_anon_key : "MANUAL_UPDATE_REQUIRED"
    }
  }

  # ACR Webhook configurations
  acr_webhook_configs = {
    web = {
      service_uri = "https://${azurerm_linux_web_app.web.name}.scm.azurewebsites.net/api/registry/webhook"
      actions     = ["push"]
      scope       = "${var.acr_repository_web}:${var.acr_tag_web}"
    }
  }

  # Model deployments configuration
  model_deployments = {
    gpt4o = {
      name    = var.gpt4o_deployment_name
      model   = {
        format  = "OpenAI"
        name    = var.gpt4o_model_name
        version = var.gpt4o_model_version
      }
      sku = {
        name     = var.gpt4o_sku_name
        capacity = var.gpt4o_sku_capacity
      }
    }
    text-embedding-3-large = {
      name    = var.text_embedding_deployment_name
      model   = {
        format  = "OpenAI"
        name    = var.text_embedding_model_name
        version = var.text_embedding_model_version
      }
      sku = {
        name     = var.text_embedding_sku_name
        capacity = var.text_embedding_sku_capacity
      }
    }
  }
}

