from langchain.agents import AgentState
from pydantic import BaseModel, ConfigDict

from core.agents.search import SearchInterface
from core.services.usage import UsageService
from db.models import ChatMessageSource


class CustomAgentContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: str
    language: str
    project_id: str
    search: SearchInterface
    usage: UsageService


class CustomAgentState(AgentState):
    sources: list[ChatMessageSource]
