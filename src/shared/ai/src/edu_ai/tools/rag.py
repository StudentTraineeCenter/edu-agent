"""RAG search tools for agent."""

from edu_ai.chatbot.context import ChatbotContext
from edu_db.models import ChatMessageSource
from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime


@tool(
    "search_project_documents",
    description="Search project documents for relevant course content. ALWAYS use this for questions about course concepts, definitions, examples, exercises, or any academic topic. Only skip for greetings or purely personal questions.",
)
async def search_project_documents(
    query: str,
    runtime: ToolRuntime[ChatbotContext],
) -> dict:
    """Search project documents and return relevant content."""
    ctx = runtime.context

    # Perform RAG search using SearchService directly
    search_results = await ctx.search.search_documents(
        query=query, project_id=ctx.project_id, top_k=5
    )

    if not search_results:
        return {"content": "No relevant documents found.", "sources": []}

    # Build sources from SearchResultItem
    sources = [
        ChatMessageSource(
            id=result.id,
            citation_index=i,
            content=result.content or "",
            title=result.title or f"Document {i}",
            document_id=result.document_id,
            score=getattr(result, "score", None) or 1.0,
        )
        for i, result in enumerate(search_results, 1)
    ]

    # Format content for agent - give clean context without citation markers
    # The agent should use this information naturally, not copy-paste it
    context_blocks = [
        f"From {source.title}:\n{source.content[:1500]}" for source in sources
    ]

    formatted_content = "\n\n---\n\n".join(context_blocks)

    return {
        "content": f"Here is relevant information from the course documents:\n\n{formatted_content}\n\nPlease use this information to answer the student's question in a clear, educational way.",
        "sources": sources,  # This will be captured by middleware
    }


# Export tools
tools = [search_project_documents]
