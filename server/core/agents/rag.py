from typing import Any, Dict, List, Tuple

from core.agents.search import SearchInterface, SearchResult
from db.models import ChatMessageSource
from langchain.tools import tool


def make_project_retrieval_tool(project_id: str, search_interface: SearchInterface):
    @tool(f"retrieve_project_docs_{project_id}")
    async def retrieve_project_docs(query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Retrieve top_k semantically similar passages from this project's documents.
        Returns:
          - context: Markdown text with [n] headers for citations
          - sources: list[ChatMessageSource-like dict] with citation_index, id, document_id, preview_url, score, title, content
        """
        hits = await search_interface.search_documents(
            query=query, project_id=project_id, top_k=top_k
        )

        context, sources = _build_sources_and_context(hits)

        return {"context": context, "sources": sources}

    return retrieve_project_docs


def _build_sources_and_context(
    results: List[SearchResult],
) -> Tuple[str, List[ChatMessageSource]]:
    context_blocks = []
    sources = []
    for i, result in enumerate(results, 1):
        title = result.title or f"Document {i}"
        content = (result.content or "")[:1000]  # trim for tokens
        context_blocks.append(f"[{i}] {title}\n{content}\n")
        sources.append(
            ChatMessageSource(
                id=result.id,
                citation_index=i,
                content=result.content or "",
                title=title,
                document_id=result.document_id,
                preview_url=result.preview_url,
                score=result.score,
            )
        )

    ctx = (
        "\n\n".join(context_blocks)
        if context_blocks
        else "No relevant documents found."
    )

    return ctx, sources
