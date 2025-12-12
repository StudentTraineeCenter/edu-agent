from langchain.agents import AgentState
from pydantic import BaseModel, ConfigDict

from edu_shared.db.models import ChatMessageSource
from edu_shared.services.search import SearchService


class CustomAgentContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: str
    language: str
    project_id: str
    search: "SearchService"
    usage: object = None  # Optional usage service (can be None or any usage service type)


class CustomAgentState(AgentState):
    sources: list[ChatMessageSource]

