# Azure Deployment Guide

This guide covers how to deploy EduAgent to Azure using Terraform.

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
  - Azure App Client ID (for Entra ID authentication)

## Deployment Steps

### Step 1: Configure Terraform Variables

Create a `terraform.tfvars` file in the `infra/` directory:

```hcl
# Azure Authentication
azure_subscription_id = "your-subscription-id"
azure_tenant_id      = "your-tenant-id"
azure_app_client_id  = "your-app-client-id"

# Infrastructure Configuration
location     = "Sweden Central"
region_code  = "swc"
project_name = "edu-agent"
environment  = "dev"
workload     = ""

# Container Registry Configuration
acr_repository_api = "edu-agent-api"
acr_tag_api       = "latest"
acr_repository_web = "edu-agent-web"
acr_tag_web       = "latest"
```

### Step 2: Initialize Terraform

```bash
cd infra
terraform init
```

This downloads the required Terraform providers (Azure RM, Random).

### Step 3: Review Deployment Plan

```bash
terraform plan
```

Review the plan to see what resources will be created:

- Resource Group
- Storage Account (for document storage)
- Azure Container Registry (ACR)
- Key Vault (for secrets)
- AI Foundry Hub and Project (for Azure OpenAI)
- AI Services (for Content Understanding)
- App Service Plan
- App Services (API and Web)
- RBAC assignments

### Step 4: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. This will create all Azure resources. The deployment typically takes 10-15 minutes.

**Note:** The database module is currently disabled. If you need Azure-managed PostgreSQL, uncomment the database module in `main.tf` and provide database credentials.

### Step 5: Build and Push Docker Images

After infrastructure is deployed, build and push the Docker images:

#### Build and Push API Image

```bash
cd infra
./build-push-server.sh [TAG]
```

Example:

```bash
./build-push-server.sh latest
```

#### Build and Push Web Image

```bash
cd infra
./build-push-web.sh [TAG]
```

Example:

```bash
./build-push-web.sh latest
```

The build scripts will:

1. Login to Azure
2. Login to Azure Container Registry
3. Build the Docker image (for linux/amd64 platform)
4. Push the image to ACR

### Step 6: Restart App Services

After pushing new images, restart the App Services to pull the latest images:

```bash
# Get app names from Terraform outputs
API_APP=$(terraform output -raw api_app_name)
WEB_APP=$(terraform output -raw web_app_name)
RESOURCE_GROUP=$(terraform output -raw resource_group_name)

# Restart API
az webapp restart --name "$API_APP" --resource-group "$RESOURCE_GROUP"

# Restart Web
az webapp restart --name "$WEB_APP" --resource-group "$RESOURCE_GROUP"
```

### Step 7: Get Application URLs

```bash
cd infra
terraform output
```

This will show:

- `app_api_url` - API application URL
- `app_web_url` - Web application URL
- `acr_name` - Container registry name
- `resource_group_name` - Resource group name

## Updating Deployment

To update the deployment:

1. Make code changes
2. Build and push new Docker images with updated tags
3. Update `acr_tag_api` and/or `acr_tag_web` in `terraform.tfvars`
4. Run `terraform apply` to update App Service configurations
5. Restart App Services

## Destroying Infrastructure

To remove all resources:

```bash
cd infra
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
cd infra
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
| `MAX_CHAT_MESSAGES_PER_DAY`         | Daily chat message limit    | No       | 100     |
| `MAX_FLASHCARD_GENERATIONS_PER_DAY` | Daily flashcard limit       | No       | 100     |
| `MAX_QUIZ_GENERATIONS_PER_DAY`      | Daily quiz limit            | No       | 100     |
| `MAX_DOCUMENT_UPLOADS_PER_DAY`      | Daily document upload limit | No       | 100     |

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
| `azure-entra-tenant-id`                | Azure AD tenant ID              |
| `azure-entra-client-id`                | Azure AD client ID              |

### Web Frontend Environment Variables

The following environment variables are automatically configured by Terraform in App Service:

| Variable                     | Description        | Required |
| ---------------------------- | ------------------ | -------- |
| `VITE_SERVER_URL`            | API server URL     | Yes      |
| `VITE_AZURE_ENTRA_TENANT_ID` | Azure AD tenant ID | Yes      |
| `VITE_AZURE_ENTRA_CLIENT_ID` | Azure AD client ID | Yes      |

## Infrastructure Overview

The Terraform configuration creates the following resources:

- **Resource Group**: Container for all resources
- **Storage Account**: For document blob storage
- **Azure Container Registry**: For Docker images
- **Key Vault**: For storing secrets
- **AI Foundry Hub**: For Azure OpenAI services
- **AI Services**: For Content Understanding
- **App Service Plan**: Hosting plan for App Services
- **App Service (API)**: Python FastAPI backend
- **App Service (Web)**: React frontend

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
