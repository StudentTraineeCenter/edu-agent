from abc import ABC, abstractmethod
from typing import List

from core.services.document_types import SearchResultItem
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Unified search result structure with validation."""

    id: str = Field(..., description="Unique identifier for the result")
    title: str = Field(..., description="Title of the document")
    content: str = Field(..., description="Content excerpt")
    document_id: str = Field(..., description="Document ID")
    score: float = Field(default=1.0, ge=0.0, le=1.0, description="Relevance score")
    preview_url: str = Field(default="", description="URL to preview document")

    @classmethod
    def from_search_result_item(
        cls, item: SearchResultItem, segment_id: str = ""
    ) -> "SearchResult":
        """Convert SearchResultItem to SearchResult for backwards compatibility."""
        return cls(
            id=segment_id or item.document_id,
            title=item.title,
            content=item.content,
            document_id=item.document_id,
            score=item.score,
            preview_url=f"/v1/documents/{item.document_id}/preview",
        )


class SearchInterface(ABC):
    """Abstract interface for document search functionality"""

    @abstractmethod
    async def search_documents(
        self, query: str, project_id: str, top_k: int = 5
    ) -> List[SearchResult]:
        """Search for documents in a project"""
        pass


class DocumentSearchAdapter(SearchInterface):
    """Adapter that wraps DocumentService to implement SearchInterface with validated types."""

    def __init__(self, document_service):
        self.document_service = document_service

    async def search_documents(
        self, query: str, project_id: str, top_k: int = 5
    ) -> List[SearchResult]:
        """Search documents using the document service with validated types."""
        results = await self.document_service.search_documents(query, project_id, top_k)

        # Convert SearchResultItems to SearchResults
        search_results = []
        for result in results:
            search_result = SearchResult.from_search_result_item(result)
            search_results.append(search_result)

        return search_results
