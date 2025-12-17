"""Flashcard tools for agent."""

import asyncio
import json
from contextlib import suppress

from edu_ai.chatbot.context import ChatbotContext
from edu_core.schemas.flashcards import FlashcardDto, FlashcardGroupDto
from edu_core.services.flashcard_groups import FlashcardGroupService
from edu_queue.schemas import FlashcardGenerationData, QueueTaskMessage, TaskType
from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime


def build_enhanced_prompt(
    custom_instructions: str | None,
    query: str | None = None,
    document_ids: list[str] | None = None,
) -> str:
    """Build enhanced prompt with optional query and document filtering."""
    prompt = custom_instructions or ""
    if query:
        prompt += f" Focus on: {query}"
    if document_ids:
        prompt += f" Based on specific documents: {', '.join(document_ids)}"
    return prompt


def increment_usage(usage, user_id: str, feature: str) -> None:
    """Increment usage tracking, log errors but don't fail."""
    if not usage:
        return
    with suppress(Exception):
        usage.check_and_increment(user_id, feature)


@tool(
    "flashcards_create",
    description="Create flashcards from project documents. Use count 15-30. Provide a short topic plus optional custom instructions (format, difficulty, focus, etc.).",
)
async def create_flashcards(
    count: int,
    topic: str,
    runtime: ToolRuntime[ChatbotContext],
    custom_instructions: str | None = None,
) -> str:
    """Create flashcards from project documents."""
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "flashcard_generation")

    svc = FlashcardGroupService()
    # Create a new flashcard group first
    group = svc.create_flashcard_group(
        project_id=ctx.project_id,
        name="Generated Flashcards",
        description="AI-generated flashcards",
    )

    # Send message to queue
    queue_service = runtime.context.queue
    message = QueueTaskMessage(
        type=TaskType.FLASHCARD_GENERATION,
        data=FlashcardGenerationData(
            project_id=ctx.project_id,
            group_id=group.id,
            topic=topic,
            custom_instructions=custom_instructions,
            count=count,
            user_id=ctx.user_id,
        ),
    )
    queue_service.send_message(message)

    return json.dumps(
        {
            "status": "queued",
            "message": "Your request to generate flashcards has been queued.",
            "group_id": group.id,
        },
        ensure_ascii=False,
    )


@tool(
    "flashcards_create_scoped",
    description="Create flashcards from specific documents. Use when user references specific docs or IDs.",
)
async def create_flashcards_scoped(
    count: int,
    custom_instructions: str,
    document_ids: list[str],
    query: str,
    runtime: ToolRuntime[ChatbotContext],
) -> str:
    """Create flashcards from specific documents."""
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "flashcard_generation")

    enhanced_prompt = build_enhanced_prompt(custom_instructions, query, document_ids)

    svc = FlashcardGroupService()
    # Create a new flashcard group first
    group = svc.create_flashcard_group(
        project_id=ctx.project_id,
        name="Generated Flashcards",
        description="AI-generated flashcards",
    )

    # Send message to queue
    queue_service = runtime.context.queue
    message = QueueTaskMessage(
        type=TaskType.FLASHCARD_GENERATION,
        data=FlashcardGenerationData(
            project_id=ctx.project_id,
            group_id=group.id,
            topic=query,
            custom_instructions=enhanced_prompt,
            count=count,
            user_id=ctx.user_id,
        ),
    )
    queue_service.send_message(message)

    return json.dumps(
        {
            "status": "queued",
            "message": "Your request to generate flashcards from specific documents has been queued.",
            "group_id": group.id,
        },
        ensure_ascii=False,
    )


@tool("flashcards_list_groups", description="List flashcard groups for a project")
async def list_groups(runtime: ToolRuntime[ChatbotContext]) -> str:
    """List flashcard groups for a project."""
    ctx = runtime.context
    svc = FlashcardGroupService()
    groups = await asyncio.to_thread(svc.list_flashcard_groups, ctx.project_id)

    groups_dto = [FlashcardGroupDto.model_validate(g) for g in groups]
    result = {
        "data": [g.model_dump() for g in groups_dto],
        "count": len(groups_dto),
    }
    return json.dumps(result, ensure_ascii=False, default=str)


@tool("flashcards_get", description="Get flashcards in a group")
async def get_flashcards(
    group_id: str,
    runtime: ToolRuntime[ChatbotContext],
) -> str:
    """Get flashcards in a group."""
    ctx = runtime.context
    svc = FlashcardGroupService()
    cards = await asyncio.to_thread(svc.list_flashcards, group_id, ctx.project_id)

    cards_dto = [FlashcardDto.model_validate(card) for card in cards]
    result = {
        "data": [card.model_dump() for card in cards_dto],
        "count": len(cards_dto),
    }
    return json.dumps(result, ensure_ascii=False, default=str)


@tool("flashcards_delete_group", description="Delete a flashcard group")
async def delete_group(
    group_id: str,
    runtime: ToolRuntime[ChatbotContext],
) -> str:
    """Delete a flashcard group."""
    ctx = runtime.context
    svc = FlashcardGroupService()
    await asyncio.to_thread(svc.delete_flashcard_group, group_id, ctx.project_id)

    result = {
        "success": True,
        "group_id": group_id,
        "message": "Flashcard group successfully deleted.",
    }
    return json.dumps(result, ensure_ascii=False)


@tool(
    "flashcards_update_group", description="Update a flashcard group's name/description"
)
async def update_group(
    group_id: str,
    name: str,
    description: str,
    runtime: ToolRuntime[ChatbotContext],
) -> str:
    """Update a flashcard group's name/description."""
    ctx = runtime.context
    svc = FlashcardGroupService()
    grp = await asyncio.to_thread(
        svc.update_flashcard_group,
        group_id,
        ctx.project_id,
        name=name,
        description=description,
    )

    group_dto = FlashcardGroupDto.model_validate(grp)
    return json.dumps(group_dto.model_dump(), ensure_ascii=False, default=str)


tools = [
    create_flashcards,
    # create_flashcards_scoped,
    list_groups,
    get_flashcards,
    delete_group,
    update_group,
]
