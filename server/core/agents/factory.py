from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import (
    before_model,
    after_model,
    dynamic_prompt,
    ModelRequest,
)
from langchain_core.messages import BaseMessage
from langgraph.runtime import Runtime

from core.agents.context import CustomAgentContext, CustomAgentState
from core.agents.flashcard import tools as flashcard_tools
from core.agents.llm import make_llm_streaming
from core.agents.quiz import tools as quiz_tools
from db.models import ChatMessageSource


@before_model(state_schema=CustomAgentState)
async def fetch_and_set_sources(
    state: CustomAgentState, runtime: Runtime[CustomAgentContext]
) -> dict[str, Any] | None:
    """Fetch documents via RAG and set sources in agent state (once per user message)."""
    if state.get("sources"):
        return None

    msgs: list[BaseMessage] = state.get("messages", [])
    if not msgs:
        return None

    # Find last user message
    user_query = next(
        (msg.content for msg in reversed(msgs) if msg.type == "human"), None
    )

    if not user_query:
        return None

    # Perform RAG search
    search_results = await runtime.context.search.search_documents(
        query=user_query, project_id=runtime.context.project_id, top_k=5
    )

    # Build sources
    sources = [
        ChatMessageSource(
            id=result.id,
            citation_index=i,
            content=result.content or "",
            title=result.title or f"Document {i}",
            document_id=result.document_id,
            preview_url=result.preview_url,
            score=result.score,
        )
        for i, result in enumerate(search_results, 1)
    ]

    return {"sources": sources} if sources else None


@dynamic_prompt
async def dynamic_system_prompt(request: ModelRequest) -> str:
    """Generate dynamic system prompt with document context."""
    sources = request.state.get("sources", [])

    # Build context blocks from sources
    context_blocks = [
        f"[{source.citation_index}] {source.title}\n{(source.content or '')[:1000]}\n"
        for source in sources
    ]

    documents_context = (
        "\n\n".join(context_blocks)
        if context_blocks
        else "No relevant documents found."
    )
    language = request.runtime.context.language or "English"

    return f"""<role>
You are an educational AI tutor helping students learn course material.
Always respond in {language}.
</role>

<rules>
- For content questions: Base your answers ONLY on the retrieved documents provided in context below
- Cite sources with inline [n] citations after each fact
- Never use general knowledge when documents exist
- Guide learning through explanation, not just answers
- Break down complex concepts, use examples when helpful
- Do not execute tools unless explicitly requested by the user (e.g. "create flashcards", "create a quiz")
- For explanation requests, answer directly using the context - do not call tools
</rules>

<context>
Use the following retrieved documents to answer the question:

{documents_context}
</context>"""


@after_model(state_schema=CustomAgentState)
def ensure_sources_in_stream(
    state: CustomAgentState, runtime: Runtime[CustomAgentContext]
) -> dict[str, Any] | None:
    """Ensure sources are included in the model node update for streaming."""
    sources = state.get("sources", [])
    return {"sources": sources} if sources else None


def make_agent():
    llm = make_llm_streaming()
    tools = [*flashcard_tools, *quiz_tools]

    return create_agent(
        model=llm,
        tools=tools,
        middleware=[
            fetch_and_set_sources,
            dynamic_system_prompt,
            ensure_sources_in_stream,
        ],
        state_schema=CustomAgentState,
        context_schema=CustomAgentContext,
    )
