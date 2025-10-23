from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from core.config import app_config
from langchain_openai import AzureChatOpenAI


def make_llm_streaming(temperature=0.0):
    cred = DefaultAzureCredential()
    tok = get_bearer_token_provider(
        cred, "https://cognitiveservices.azure.com/.default"
    )
    return AzureChatOpenAI(
        azure_deployment=app_config.AZURE_OPENAI_CHAT_DEPLOYMENT,
        azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
        api_version="2024-12-01-preview",
        azure_ad_token_provider=tok,
        temperature=temperature,
        streaming=True,
    )
