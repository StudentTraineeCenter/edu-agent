"""RAG search tools for agent."""

from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime

from core.agents.context import CustomAgentContext
from db.models import ChatMessageSource


@tool(
    "search_project_documents",
    description="""Search through project documents and materials to find relevant information.

Use this tool when the user asks questions about:
- project content, concepts, or topics
- Specific subject matter from their uploaded materials
- Technical explanations from their documents
- Details that require referencing project materials

Do NOT use for:
- Greetings or casual conversation
- Requests to create study resources (flashcards, quizzes, notes, mind maps)
- General questions that don't require document context""",
)
async def search_project_documents(
    query: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> dict:
    """Search project documents and return relevant content."""
    ctx = runtime.context
    
    # Perform RAG search
    search_results = await ctx.search.search_documents(
        query=query, 
        project_id=ctx.project_id, 
        top_k=5
    )
    
    if not search_results:
        return {
            "content": "No relevant documents found.",
            "sources": []
        }
    
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
    
    # Format content for agent
    context_blocks = [
        f"[{source.citation_index}] {source.title}\n{(source.content or '')[:1000]}\n"
        for source in sources
    ]
    
    formatted_content = "\n\n".join(context_blocks)
    
    return {
        "content": formatted_content,
        "sources": sources,  # This will be captured by middleware
    }


# Export tools
tools = [search_project_documents]
