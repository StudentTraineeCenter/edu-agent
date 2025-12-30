# Azure Deployment Guide

This guide covers how to deploy EduAgent to Azure using Terraform and the tooling in `deploy/azure/`.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Steps](#deployment-steps)
3. [Updating Deployment](#updating-deployment)
4. [Destroying Infrastructure](#destroying-infrastructure)
5. [Troubleshooting](#troubleshooting)
6. [Environment Variables Reference](#environment-variables-reference)

## Prerequisites

- Azure subscription with appropriate permissions
- Azure CLI installed and configured (`az login`)
- Terraform installed (version 1.0+)
- Docker installed (for building and pushing images)
- Azure credentials:
  - Subscription ID
  - Tenant ID
- Supabase credentials:
  - Supabase project URL
  - Supabase anon key
  - Supabase service role key
  - Supabase JWT secret

## Deployment Steps

### Step 1: Configure Terraform Variables

Create a `terraform.tfvars` file in the `deploy/azure/terraform/` directory:

```hcl
# Azure Authentication
azure_subscription_id = "your-subscription-id"
azure_tenant_id      = "your-tenant-id"

# Infrastructure Configuration
location     = "Sweden Central"
region_code  = "swc"
project_name = "edu-agent"
environment  = "dev"

# Container Registry Configuration (optional overrides)
acr_repository_api    = "edu-api"
acr_tag_api           = "latest"
acr_repository_worker = "edu-worker"
acr_tag_worker        = "latest"
acr_repository_web    = "edu-agent-web"
acr_tag_web           = "latest"

# Supabase (provisioned by Terraform)
supabase_access_token      = "your-supabase-personal-access-token"
supabase_organization_id   = "your-supabase-org-id"
supabase_database_password = "strong-db-password"
supabase_service_role_key  = "service-role-key-or-null-if-set-manually-later"
supabase_jwt_secret        = "jwt-secret-or-null-if-set-manually-later"
supabase_anon_key          = "anon-key-or-null-if-set-manually-later"
```

### Step 2: Initialize Terraform

```bash
cd deploy/azure/terraform
terraform init
```

This downloads the required Terraform providers (Azure RM, Random).

### Step 3: Review Deployment Plan

```bash
terraform plan
```

Review the plan to see what resources will be created, including:

- **Azure AI Foundry**: Hub, Project, and Model Deployments (GPT-4o, text-embedding-3-large)
- **Azure Storage**: Account with Blob containers and Tasks queue
- **Azure Key Vault**: Secure secret management with RBAC
- **Azure Container Registry**: Private registry for container images
- **Azure Container Apps**: Serverless hosting for API and Worker services
- **Azure App Service**: Linux-based hosting for the Web frontend
- **Azure Monitor**: Log Analytics and Application Insights for observability
- **Supabase**: Managed project with Database and Auth configured
- **RBAC assignments**: Managed identities and access control settings

### Step 4: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. This will create all Azure resources. The deployment typically takes 10–15 minutes.

Terraform will also:

- Seed Key Vault with secrets for Azure AI, Supabase, and storage
- Wire up identities and RBAC so container apps can read from Key Vault

### Step 5: Build and Push Docker Images with ACR Tasks

After infrastructure is deployed, build and push the Docker images using the remote ACR build script (no local Docker daemon required for the build itself):

```bash
cd deploy/azure

# Build all containers (API, worker, web) using ACR Tasks
python build.py

# Or build specific containers
python build.py --container edu-api
python build.py --container edu-worker
python build.py --container edu-web

# Optionally override the ACR name (otherwise read from terraform output)
python build.py --acr-name myacr
```

Build configuration is controlled via `deploy/azure/build-config.yaml`:

- Image names, tags, and Dockerfile paths
- Vite build-time environment variables for the web app:
  - `VITE_SERVER_URL` (from `container_app_api_url` terraform output)
  - `VITE_SUPABASE_URL` (from `supabase_api_url` terraform output)
  - `VITE_SUPABASE_ANON_KEY` (from the `supabase_anon_key` variable)

### Step 6: Get Application URLs

```bash
cd deploy/azure/terraform
terraform output
```

This will show:

- `container_app_api_url` - API container app URL (used by the SPA)
- `app_web_url` - Web application URL
- `acr_name` - Container registry name
- `resource_group_name` - Resource group name

## Updating Deployment

To update the deployment:

1. Make code changes
2. (Optional) Update `acr_tag_*` values in `deploy/azure/terraform/terraform.tfvars`
3. Build and push new Docker images:

   ```bash
   cd deploy/azure
   python build.py                      # all containers
   # or: python build.py --container edu-api --container edu-worker --container edu-web
   ```

4. If you changed image tags or infra settings, run:

   ```bash
   cd deploy/azure/terraform
   terraform apply
   ```

5. The container apps will automatically use the new images on the next revision. The web app can be updated either via ACR webhooks (for the configured scope) or a standard redeploy.

## Destroying Infrastructure

To remove all resources:

```bash
cd deploy/azure/terraform
terraform destroy
```

**Warning:** This will delete all resources including stored documents and data.

## Troubleshooting

### Terraform Issues

**Error: Authentication failed**

```bash
# Login to Azure
az login
az account set --subscription "your-subscription-id"
```

**Error: Provider not found**

```bash
cd deploy/azure/terraform
terraform init -upgrade
```

**Error: Resource already exists**

- Check if resources exist in Azure Portal
- Import existing resources or destroy and recreate

### Docker Build Issues

**Error: Cannot connect to Docker daemon**

- Start Docker Desktop or Docker service
- Verify Docker is running: `docker ps`

**Error: ACR login failed**

- Verify ACR name is correct: `terraform output acr_name`
- Check Azure login: `az account show`
- Try manual login: `az acr login --name <acr-name>`

**Error: Image push failed**

- Verify you have push permissions to ACR
- Check ACR authentication: `az acr login --name <acr-name>`

### App Service Issues

**App Service not starting**

- Check App Service logs: `az webapp log tail --name <app-name> --resource-group <rg-name>`
- Verify environment variables are set correctly
- Check Docker image exists in ACR
- Verify STARTUP_COMMAND is correct

**API returns 500 errors**

- Check application logs in Azure Portal
- Verify all environment variables are set
- Check database connectivity (if using Azure database)
- Verify Azure service endpoints and keys

## Environment Variables Reference

### Server (API) Environment Variables

The application uses Azure Key Vault for secure credential management. In production, only the Key Vault URI and usage limits need to be configured in App Service:

| Variable                            | Description                 | Required | Default |
| ----------------------------------- | --------------------------- | -------- | ------- |
| `AZURE_KEY_VAULT_URI`               | Azure Key Vault URI         | Yes      | -       |
| `MAX_CHAT_MESSAGES_PER_DAY`         | Daily chat message limit    | No       | 50      |
| `MAX_FLASHCARD_GENERATIONS_PER_DAY` | Daily flashcard limit       | No       | 10      |
| `MAX_QUIZ_GENERATIONS_PER_DAY`      | Daily quiz limit            | No       | 10      |
| `MAX_DOCUMENT_UPLOADS_PER_DAY`      | Daily document upload limit | No       | 5       |

All other Azure service credentials are automatically retrieved from Key Vault using the secret names defined in the application configuration. The App Service must have appropriate RBAC permissions to read secrets from the Key Vault.

### Key Vault Secret Names

The following secrets must be stored in the Key Vault:

| Secret Name                            | Description                     |
| -------------------------------------- | ------------------------------- |
| `database-url`                         | PostgreSQL connection string    |
| `azure-openai-api-key`                 | Azure OpenAI API key            |
| `azure-openai-endpoint`                | Azure OpenAI endpoint URL       |
| `azure-openai-default-model`           | Default OpenAI model            |
| `azure-openai-chat-deployment`         | Chat model deployment name      |
| `azure-openai-embedding-deployment`    | Embedding model deployment      |
| `azure-openai-api-version`             | OpenAI API version              |
| `azure-storage-connection-string`      | Azure Storage connection string |
| `azure-storage-input-container-name`   | Input blob container name       |
| `azure-storage-output-container-name`  | Output blob container name      |
| `azure-document-intelligence-endpoint` | Document Intelligence endpoint  |
| `azure-document-intelligence-key`      | Document Intelligence API key   |
| `azure-cu-endpoint`                    | Content Understanding endpoint  |
| `azure-cu-key`                         | Content Understanding API key   |
| `azure-cu-analyzer-id`                 | Content Understanding analyzer  |
| `supabase-url`                         | Supabase project URL            |
| `supabase-service-role-key`            | Supabase service role key       |
| `supabase-jwt-secret`                  | Supabase JWT secret             |

### Web Frontend Environment Variables

The following environment variables are automatically configured by Terraform in App Service:

| Variable                 | Description          | Required |
| ------------------------ | -------------------- | -------- |
| `VITE_SERVER_URL`        | API server URL       | Yes      |
| `VITE_SUPABASE_URL`      | Supabase project URL | Yes      |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key    | Yes      |

## Infrastructure Overview

The Terraform configuration creates the following resources:

- **Azure AI Foundry**: Hub, Project, and Model Deployments (GPT-4o, text-embedding-3-large)
- **Azure Storage**: Account with Blob containers and Tasks queue
- **Azure Key Vault**: Secure secret management with RBAC
- **Azure Container Registry**: Private registry for container images
- **Azure Container Apps**: Serverless hosting for API and Worker services
- **Azure App Service**: Linux-based hosting for the Web frontend
- **Azure Monitor**: Log Analytics and Application Insights for observability
- **Supabase**: Managed project with Database and Auth configured

## Additional Resources

- [Terraform Azure Provider Documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure Container Registry Documentation](https://docs.microsoft.com/azure/container-registry/)

## Support

For issues or questions:

- Check application logs
- Review Terraform state: `terraform show`
- Check Azure Portal for resource status
- Contact: richard.amare@studentstc.cz
