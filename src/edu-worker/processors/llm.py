"""LLM helper utilities for worker processes."""

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_openai import AzureChatOpenAI


def create_llm(
    azure_openai_chat_deployment: str,
    azure_openai_endpoint: str,
    azure_openai_api_version: str,
    streaming: bool = True,
    temperature: float = 0.25,
) -> AzureChatOpenAI:
    """Create an AzureChatOpenAI instance for worker processes.

    Args:
        azure_openai_chat_deployment: Azure OpenAI chat deployment name
        azure_openai_endpoint: Azure OpenAI endpoint URL
        azure_openai_api_version: Azure OpenAI API version
        streaming: Whether to enable streaming
        temperature: Temperature for the LLM

    Returns:
        Configured AzureChatOpenAI instance
    """
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )

    llm_kwargs = {
        "azure_deployment": azure_openai_chat_deployment,
        "azure_endpoint": azure_openai_endpoint,
        "azure_ad_token_provider": token_provider,
        "temperature": temperature,
        "streaming": streaming,
    }

    if azure_openai_api_version:
        llm_kwargs["api_version"] = azure_openai_api_version

    return AzureChatOpenAI(**llm_kwargs)


def create_llm_non_streaming(
    azure_openai_chat_deployment: str,
    azure_openai_endpoint: str,
    azure_openai_api_version: str,
    temperature: float = 0.25,
) -> AzureChatOpenAI:
    """Create a non-streaming AzureChatOpenAI instance for worker processes.

    Args:
        azure_openai_chat_deployment: Azure OpenAI chat deployment name
        azure_openai_endpoint: Azure OpenAI endpoint URL
        azure_openai_api_version: Azure OpenAI API version
        temperature: Temperature for the LLM

    Returns:
        Configured non-streaming AzureChatOpenAI instance
    """
    return create_llm(
        azure_openai_chat_deployment,
        azure_openai_endpoint,
        azure_openai_api_version,
        streaming=False,
        temperature=temperature,
    )
