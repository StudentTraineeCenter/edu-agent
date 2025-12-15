import json
from typing import Any

from edu_ai.agents.context import CustomAgentContext, CustomAgentState
from edu_ai.agents.prompts_utils import render_prompt
from edu_ai.agents.tools.flashcard import tools as flashcard_tools
from edu_ai.agents.tools.mind_map import tools as mind_map_tools
from edu_ai.agents.tools.note import tools as note_tools
from edu_ai.agents.tools.quiz import tools as quiz_tools
from edu_ai.agents.tools.rag import tools as rag_tools
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelRequest,
    after_model,
    dynamic_prompt,
    wrap_tool_call,
)
from langchain_core.messages import ToolMessage
from langchain_openai import AzureChatOpenAI
from langgraph.runtime import Runtime


@wrap_tool_call
async def capture_sources_from_rag(request, handler):
    """Capture sources when RAG search tool is used."""
    # Execute the tool
    result = await handler(request)

    # Check if this was a search_project_documents call
    if request.tool.name == "search_project_documents" and isinstance(
        result, ToolMessage
    ):
        try:
            # Parse the content to extract sources
            content = (
                json.loads(result.content)
                if isinstance(result.content, str)
                else result.content
            )
            sources = content.get("sources", [])

            # Store sources in state
            if sources:
                request.state["sources"] = sources

            # Return just the content string to the agent
            result.content = content.get("content", result.content)
        except:
            pass

    return result


# Cache system prompts by language for performance
_prompt_cache = {}


def get_instructions(language: str = "English") -> str:
    """Load and render the system prompt template."""
    return render_prompt("system_prompt", language=language)


@dynamic_prompt
async def dynamic_system_prompt(request: ModelRequest) -> str:
    """Generate dynamic system prompt."""
    language = request.runtime.context.language or "English"

    # Return cached prompt if available
    if language in _prompt_cache:
        return _prompt_cache[language]

    # Generate and cache the prompt
    prompt = get_instructions(language)

    _prompt_cache[language] = prompt
    return prompt


@after_model(state_schema=CustomAgentState)
def ensure_sources_in_stream(
    state: CustomAgentState, runtime: Runtime[CustomAgentContext]
) -> dict[str, Any] | None:
    """Ensure sources are included in the model node update for streaming."""
    sources = state.get("sources", [])
    return {"sources": sources} if sources else None


def make_agent(llm: AzureChatOpenAI):
    tools = [
        *rag_tools,
        *flashcard_tools,
        *quiz_tools,
        *note_tools,
        *mind_map_tools,
    ]

    return create_agent(
        model=llm,
        tools=tools,
        middleware=[
            capture_sources_from_rag,
            dynamic_system_prompt,
            ensure_sources_in_stream,
        ],
        state_schema=CustomAgentState,
        context_schema=CustomAgentContext,
    )

