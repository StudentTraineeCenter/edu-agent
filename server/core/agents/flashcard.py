from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from core.agents.llm import make_llm_streaming
from core.agents.search import SearchInterface
from core.services.flashcards import FlashcardService
from core.services.usage import UsageService
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class CreateFlashcardsInput(BaseModel):
    project_id: str = Field(..., description="Project to ground generation")
    count: int = Field(30, ge=1, le=100, description="Number of flashcards")
    user_prompt: Optional[str] = Field(
        None,
        description="Extra instructions, e.g. 'focus on definitions and examples'",
    )


class CreateFlashcardsScopedInput(CreateFlashcardsInput):
    document_ids: Optional[List[str]] = Field(
        default=None,
        description="Restrict generation to these documents (ids)",
    )
    query: Optional[str] = Field(
        default=None,
        description="Optional focus query to bias selection inside the documents",
    )


class CreateFlashcardsOutput(BaseModel):
    message: str
    name: str
    description: str
    flashcards: List[Dict[str, Any]]


class ListFlashcardGroupsInput(BaseModel):
    project_id: str


class ListFlashcardGroupsOutput(BaseModel):
    groups: List[Dict[str, Any]]


class GetFlashcardsInput(BaseModel):
    group_id: str


class GetFlashcardsOutput(BaseModel):
    flashcards: List[Dict[str, Any]]


class DeleteFlashcardGroupInput(BaseModel):
    group_id: str


class UpdateFlashcardGroupInput(BaseModel):
    group_id: str
    name: Optional[str] = None
    description: Optional[str] = None


def build_flashcard_tools(
    search_interface: SearchInterface,
    user_id: Optional[str] = None,
    usage_service: Optional[UsageService] = None,
):
    svc = FlashcardService(search_interface=search_interface)

    async def _create_flashcards(
        project_id: str, count: int = 30, user_prompt: Optional[str] = None
    ) -> CreateFlashcardsOutput:
        # Increment usage if user_id and usage_service are provided
        if user_id and usage_service:
            try:
                usage_service.check_and_increment(user_id, "flashcard_generation")
            except Exception as e:
                # Log error but don't fail the operation
                from core.logger import get_logger
                logger = get_logger(__name__)
                logger.warning("failed to increment usage: %s", e)

        group_id = await svc.create_flashcard_group_with_flashcards(
            project_id=project_id,
            count=count,
            user_prompt=user_prompt,
        )
        group = await asyncio.to_thread(lambda: svc.get_flashcard_group(group_id))
        cards = await asyncio.to_thread(lambda: svc.get_flashcards_by_group(group_id))
        return CreateFlashcardsOutput(
            message=f"✅ Flashcards created successfully! I've generated {len(cards)} flashcards for you. You can now start studying them.",
            name=group.name,
            description=group.description or "",
            flashcards=[
                {
                    "question": c.question,
                    "answer": c.answer,
                    "difficulty_level": c.difficulty_level,
                }
                for c in cards
            ],
        )

    async def _create_flashcards_scoped(
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        query: Optional[str] = None,
    ) -> CreateFlashcardsOutput:
        # Increment usage if user_id and usage_service are provided
        if user_id and usage_service:
            try:
                usage_service.check_and_increment(user_id, "flashcard_generation")
            except Exception as e:
                # Log error but don't fail the operation
                from core.logger import get_logger
                logger = get_logger(__name__)
                logger.warning("failed to increment usage: %s", e)

        # For now, the service doesn't support document scoping, so we'll use the general method
        # TODO: Implement document scoping in the service layer
        enhanced_prompt = user_prompt or ""
        if query:
            enhanced_prompt += f" Focus on: {query}"
        if document_ids:
            enhanced_prompt += (
                f" Based on specific documents: {', '.join(document_ids)}"
            )

        group_id = await svc.create_flashcard_group_with_flashcards(
            project_id=project_id,
            count=count,
            user_prompt=enhanced_prompt,
        )
        group = await asyncio.to_thread(lambda: svc.get_flashcard_group(group_id))
        cards = await asyncio.to_thread(lambda: svc.get_flashcards_by_group(group_id))
        return CreateFlashcardsOutput(
            message=f"✅ Flashcards created successfully! I've generated {len(cards)} flashcards for you. You can now start studying them.",
            name=group.name,
            description=group.description or "",
            flashcards=[
                {
                    "question": c.question,
                    "answer": c.answer,
                    "difficulty_level": c.difficulty_level,
                }
                for c in cards
            ],
        )

    async def _list_groups(project_id: str) -> ListFlashcardGroupsOutput:
        groups = await asyncio.to_thread(lambda: svc.get_flashcard_groups(project_id))
        return {
            "groups": [
                {
                    "id": g.id,
                    "name": g.name,
                    "description": g.description,
                    "created_at": g.created_at.isoformat(),
                }
                for g in groups
            ]
        }

    async def _get_flashcards(group_id: str) -> GetFlashcardsOutput:
        cards = await asyncio.to_thread(lambda: svc.get_flashcards_by_group(group_id))
        return {
            "flashcards": [
                {
                    "id": c.id,
                    "question": c.question,
                    "answer": c.answer,
                    "difficulty_level": c.difficulty_level,
                }
                for c in cards
            ]
        }

    async def _delete_group(group_id: str) -> Dict[str, bool]:
        ok = await asyncio.to_thread(lambda: svc.delete_flashcard_group(group_id))
        return {"deleted": bool(ok)}

    async def _update_group(
        group_id: str, name: Optional[str], description: Optional[str]
    ) -> Dict[str, str]:
        grp = await asyncio.to_thread(
            lambda: svc.update_flashcard_group(
                group_id, name=name, description=description
            )
        )
        return {"group_id": grp.id, "name": grp.name, "description": grp.description}

    return [
        StructuredTool.from_function(
            name="flashcards_create",
            description=(
                "Create a new flashcard group grounded in project documents. "
                "Always call this to generate flashcards."
            ),
            coroutine=_create_flashcards,
            args_schema=CreateFlashcardsInput,
            return_direct=False,
        ),
        StructuredTool.from_function(
            name="flashcards_create_scoped",
            description=(
                "Create flashcards but restrict to selected documents and/or a focus query. "
                "Use when the user says 'from this and this' or specifies doc IDs/titles."
            ),
            coroutine=_create_flashcards_scoped,
            args_schema=CreateFlashcardsScopedInput,
            return_direct=False,
        ),
        StructuredTool.from_function(
            name="flashcards_list_groups",
            description="List flashcard groups for a project",
            coroutine=lambda **kw: _list_groups(**kw),
            args_schema=ListFlashcardGroupsInput,
            return_direct=False,
        ),
        StructuredTool.from_function(
            name="flashcards_get",
            description="Get flashcards in a group",
            coroutine=lambda **kw: _get_flashcards(**kw),
            args_schema=GetFlashcardsInput,
            return_direct=False,
        ),
        StructuredTool.from_function(
            name="flashcards_delete_group",
            description="Delete a flashcard group",
            coroutine=lambda **kw: _delete_group(**kw),
            args_schema=DeleteFlashcardGroupInput,
            return_direct=False,
        ),
        StructuredTool.from_function(
            name="flashcards_update_group",
            description="Update a flashcard group's name/description",
            coroutine=lambda **kw: _update_group(**kw),
            args_schema=UpdateFlashcardGroupInput,
            return_direct=False,
        ),
    ]


def build_flashcard_agent(
    project_id: str,
    language_code: str,
    search_interface: SearchInterface,
) -> AgentExecutor:
    tools = build_flashcard_tools(search_interface=search_interface)

    system = (
        f"You are a flashcard authoring assistant. Always respond in {language_code}.\n"
        f"Prefer creating flashcards grounded in the project's documents.\n"
        f"When asked to create flashcards, CALL `flashcards_create` with a sensible count (10-40).\n"
        f"\n"
        f"IMPORTANT: After the tool returns, extract ONLY the 'message' field from the tool output and return it to the user.\n"
        f"DO NOT return the full JSON, the flashcards array, or any other fields.\n"
        f"DO NOT use backticks, code blocks, or any markdown formatting.\n"
        f"Just return the message field value as plain text.\n"
        f"\n"
        f"Example:\n"
        f"Tool returns: {{'message': 'Flashcards created!', 'flashcards': [...]}}\n"
        f"You respond: Flashcards created!\n"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_openai_tools_agent(make_llm_streaming(), tools, prompt)
    return AgentExecutor(
        agent=agent, tools=tools, verbose=False, handle_parsing_errors=True
    )
