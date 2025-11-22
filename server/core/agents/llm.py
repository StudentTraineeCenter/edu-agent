from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from core.config import app_config

COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"
API_VERSION = "2024-12-01-preview"


def _get_token_provider():
    cred = DefaultAzureCredential()
    return get_bearer_token_provider(cred, COGNITIVE_SERVICES_SCOPE)


def make_llm_streaming(temperature: float = 0.25):
    return AzureChatOpenAI(
        azure_deployment=app_config.AZURE_OPENAI_CHAT_DEPLOYMENT,
        azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
        api_version=API_VERSION,
        azure_ad_token_provider=_get_token_provider(),
        temperature=temperature,
        streaming=True,
    )


def make_embeddings():
    return AzureOpenAIEmbeddings(
        azure_deployment=app_config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
        api_version=API_VERSION,
        azure_ad_token_provider=_get_token_provider(),
    )
