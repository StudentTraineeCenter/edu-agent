#!/usr/bin/env python3
"""Convert terraform output JSON to .env format."""

import json
import sys
from pathlib import Path


def terraform_to_env(terraform_output: dict) -> str:
    """Convert terraform output to .env format."""
    lines = []

    # Database (not in terraform output, keep default)
    lines.append("# Database")
    lines.append("DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/postgres")
    lines.append("")

    # Azure Storage
    lines.append("# Azure Storage")
    lines.append(f"AZURE_STORAGE_CONNECTION_STRING={terraform_output['storage_connection_string']['value']}")
    lines.append(f"AZURE_STORAGE_INPUT_CONTAINER_NAME={terraform_output['input_container_name']['value']}")
    lines.append(f"AZURE_STORAGE_OUTPUT_CONTAINER_NAME={terraform_output['output_container_name']['value']}")
    lines.append("")

    # Azure AI Foundry
    lines.append("# Azure AI Foundry")
    lines.append(f"AZURE_OPENAI_API_KEY={terraform_output['ai_foundry_api_key']['value']}")
    lines.append(f"AZURE_OPENAI_ENDPOINT={terraform_output['ai_foundry_endpoint']['value']}")
    lines.append(f"AZURE_OPENAI_CHAT_DEPLOYMENT={terraform_output['gpt4o_deployment_name']['value']}")
    lines.append(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT={terraform_output['text_embedding_3_large_deployment_name']['value']}")
    lines.append(f"AZURE_OPENAI_DEFAULT_MODEL={terraform_output['gpt4o_deployment_name']['value']}")
    lines.append("AZURE_OPENAI_API_VERSION=2024-06-01")
    lines.append("")

    # Azure Document Intelligence
    lines.append("# Azure Document Intelligence")
    lines.append(f"AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT={terraform_output['ai_service_endpoint']['value']}")
    lines.append(f"AZURE_DOCUMENT_INTELLIGENCE_KEY={terraform_output['ai_service_key']['value']}")
    lines.append("")

    # Azure Entra ID
    lines.append("# Azure Entra ID")
    lines.append(f"AZURE_ENTRA_TENANT_ID={terraform_output['azure_tenant_id']['value']}")
    lines.append(f"AZURE_ENTRA_CLIENT_ID={terraform_output['azure_app_client_id']['value']}")
    lines.append("")

    # Azure Key Vault
    lines.append("# Azure Key Vault")
    lines.append(f"AZURE_KEY_VAULT_URI={terraform_output['azure_key_vault_uri']['value']}")
    lines.append("")

    # Azure Content Understanding
    lines.append("# Azure Content Understanding")
    lines.append(f"AZURE_CU_ENDPOINT={terraform_output['ai_service_endpoint']['value']}")
    lines.append(f"AZURE_CU_KEY={terraform_output['ai_service_key']['value']}")
    lines.append("AZURE_CU_ANALYZER_ID=prebuilt-documentAnalyzer")
    lines.append("")

    # Terraform (for terraform variables)
    lines.append("# Terraform")
    lines.append(f"TF_VAR_azure_app_client_id={terraform_output['azure_app_client_id']['value']}")
    # Note: azure_subscription_id not in terraform output, user needs to add manually
    lines.append("# TF_VAR_azure_subscription_id=<add-manually>")
    lines.append(f"TF_VAR_azure_tenant_id={terraform_output['azure_tenant_id']['value']}")
    lines.append("")

    # Vite (for frontend)
    lines.append("# Vite")
    lines.append("VITE_SERVER_URL=http://localhost:8000")
    lines.append(f"VITE_AZURE_ENTRA_TENANT_ID={terraform_output['azure_tenant_id']['value']}")
    lines.append(f"VITE_AZURE_ENTRA_CLIENT_ID={terraform_output['azure_app_client_id']['value']}")
    lines.append("")

    # Usage Limits
    lines.append("MAX_DOCUMENT_UPLOADS_PER_DAY=1")
    lines.append("MAX_QUIZ_GENERATIONS_PER_DAY=1")
    lines.append("MAX_FLASHCARD_GENERATIONS_PER_DAY=1")
    lines.append("MAX_CHAT_MESSAGES_PER_DAY=1")

    return "\n".join(lines)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Read from file
        input_file = Path(sys.argv[1])
        with open(input_file) as f:
            terraform_output = json.load(f)
    else:
        # Read from stdin
        terraform_output = json.load(sys.stdin)

    env_content = terraform_to_env(terraform_output)

    if len(sys.argv) > 2:
        # Write to file
        output_file = Path(sys.argv[2])
        output_file.write_text(env_content)
        print(f"Generated .env file: {output_file}")
    else:
        # Print to stdout
        print(env_content)


if __name__ == "__main__":
    main()

