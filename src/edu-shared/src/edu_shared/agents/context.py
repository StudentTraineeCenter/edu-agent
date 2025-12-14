from typing import TYPE_CHECKING
from langchain.agents import AgentState
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, ConfigDict

from edu_shared.db.models import ChatMessageSource
from edu_shared.services.search import SearchService

if TYPE_CHECKING:
    pass


class CustomAgentContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: str
    language: str
    project_id: str
    search: "SearchService"
    usage: object = None  # Optional usage service (can be None or any usage service type)
    llm: "AzureChatOpenAI | None" = None  # Optional LLM instance for content generation tools


class CustomAgentState(AgentState):
    sources: list[ChatMessageSource]

