resource "azurerm_service_plan" "web" {
  name                = "${local.name_prefix}-asp"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "B1" # dev-friendly; change to P1v3 for prod

  tags = local.common_tags
}

resource "azurerm_linux_web_app" "api" {
  name                = "${local.name_prefix}-api"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.web.id
  https_only          = true

  site_config {
    application_stack {
      docker_image_name   = "${var.acr_repository_api}:${var.acr_tag_api}"
      docker_registry_url = "https://${azurerm_container_registry.acr.login_server}"
    }

    container_registry_use_managed_identity = true # correct argument name
    always_on                               = true
    health_check_path                       = "/health"
    health_check_eviction_time_in_min       = 10
    ftps_state                              = "Disabled"
    minimum_tls_version                     = "1.2"
    http2_enabled                           = true
  }

  identity {
    type = "SystemAssigned"
  }

  # Environment Variables (App Settings)
  app_settings = {
    # PostgreSQL
    "POSTGRES_DB"       = "postgres"
    "POSTGRES_USER"     = "postgres"
    "POSTGRES_PASSWORD" = "postgres"
    "POSTGRES_HOST"     = "127.0.0.1"
    "POSTGRES_PORT"     = "5432"
    "DATABASE_URL"      = "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/postgres"

    # Azure OpenAI
    "AZURE_OPENAI_ENDPOINT"             = azurerm_cognitive_account.openai.endpoint
    "AZURE_OPENAI_API_KEY"              = azurerm_cognitive_account.openai.primary_access_key
    "AZURE_OPENAI_DEFAULT_MODEL"        = azurerm_cognitive_deployment.gpt4o.name
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT" = azurerm_cognitive_deployment.text_embedding_3_large.name
    "AZURE_OPENAI_CHAT_DEPLOYMENT"      = azurerm_cognitive_deployment.gpt4o.name
    "AZURE_OPENAI_API_VERSION"          = "2024-06-01"

    # Azure Storage
    "AZURE_STORAGE_CONNECTION_STRING" = azurerm_storage_account.main.primary_connection_string
    "AZURE_STORAGE_CONTAINER_NAME"    = azurerm_storage_container.documents.name
    "AZURE_STORAGE_ACCOUNT_KEY"       = azurerm_storage_account.main.primary_access_key

    # Azure Content Understanding (AI Services)
    "AZURE_CU_KEY"         = azurerm_ai_services.service.primary_access_key
    "AZURE_CU_ENDPOINT"    = azurerm_ai_services.service.endpoint
    "AZURE_CU_ANALYZER_ID" = "prebuilt-documentAnalyzer"

    # Azure Entra ID
    "AZURE_ENTRA_TENANT_ID" = var.azure_tenant_id
    "AZURE_ENTRA_CLIENT_ID" = data.azurerm_client_config.current.client_id

    # Required for Python web apps
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "WEBSITES_PORT"                  = "8000"
    "STARTUP_COMMAND"                = "gunicorn -k uvicorn.workers.UvicornWorker -w 2 app.main:app --bind 0.0.0.0:8000"
  }

  tags = local.common_tags
}

resource "azurerm_role_assignment" "api_to_storage_reader" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_linux_web_app.api.identity[0].principal_id
}
