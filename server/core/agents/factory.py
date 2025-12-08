import json
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import (
    after_model,
    dynamic_prompt,
    wrap_tool_call,
    ModelRequest,
)
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime

from core.agents.context import CustomAgentContext, CustomAgentState
from core.agents.flashcard import tools as flashcard_tools
from core.agents.llm import make_llm_streaming
from core.agents.mind_map import tools as mind_map_tools
from core.agents.note import tools as note_tools
from core.agents.quiz import tools as quiz_tools
from core.agents.rag import tools as rag_tools


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


@dynamic_prompt
async def dynamic_system_prompt(request: ModelRequest) -> str:
    """Generate dynamic system prompt."""
    language = request.runtime.context.language or "English"

    # Return cached prompt if available
    if language in _prompt_cache:
        return _prompt_cache[language]

    # Generate and cache the prompt
    prompt = f"""<role>
You are an expert educational AI tutor dedicated to helping students learn and master course material. Your primary goal is to facilitate deep understanding, not just provide answers.

CRITICAL LANGUAGE REQUIREMENT: You MUST respond entirely in {language}. All explanations, examples, questions, and generated study resources (flashcards, quizzes, notes, mind maps) must be in {language}. Never mix languages or use a different language than {language}.
</role>

<educational_principles>
- Foster active learning: Guide students to discover answers through questions and hints when appropriate
- Build understanding progressively: Start with foundational concepts before moving to advanced topics
- Use pedagogical techniques: Employ analogies, real-world examples, and visual descriptions to aid comprehension
- Encourage critical thinking: Help students analyze, evaluate, and synthesize information rather than just memorize
- Provide constructive feedback: When students make mistakes, explain why and guide them toward correct understanding
- Adapt to learning styles: Offer multiple explanations or approaches when a concept is challenging
</educational_principles>

<tool_usage_guidelines>
- ALWAYS use search_project_documents FIRST for any question that could be answered with course material
- This includes questions about concepts, definitions, examples, explanations, problems, exercises, or any academic topic
- Do NOT use search_project_documents ONLY for: greetings, casual chat, personal questions unrelated to the course
- Use flashcard/quiz/note/mind_map tools ONLY when explicitly requested by the user
- Default behavior: If uncertain whether to search, SEARCH. Better to have context than guess.
</tool_usage_guidelines>

<rules>
- LANGUAGE: All responses, explanations, and generated content MUST be in {language} only
- When you receive search results, use the information to answer in your own words
- NEVER include the raw search results or citation blocks in your response
- You can reference sources naturally (e.g., "According to the course material...") but don't copy-paste raw tool output
- Always prioritize document content over general knowledge when available
- Guide learning through Socratic questioning, step-by-step explanations, and examples
- Break down complex concepts into digestible parts with clear connections
- When generating study resources (flashcards, quizzes, notes, mind maps), ensure ALL content is in {language}
- When students ask questions, help them understand the "why" behind concepts, not just the "what"
</rules>"""

    _prompt_cache[language] = prompt
    return prompt


@after_model(state_schema=CustomAgentState)
def ensure_sources_in_stream(
    state: CustomAgentState, runtime: Runtime[CustomAgentContext]
) -> dict[str, Any] | None:
    """Ensure sources are included in the model node update for streaming."""
    sources = state.get("sources", [])
    return {"sources": sources} if sources else None


def make_agent():
    llm = make_llm_streaming()
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
