import asyncio
import json

from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime

from core.agents.context import CustomAgentContext
from core.agents.utils import build_enhanced_prompt, increment_usage
from core.services.flashcards import FlashcardService
from schemas.flashcards import FlashcardDto, FlashcardGroupDto


@tool(
    "flashcards_create",
    description="Create flashcards from project documents. Use count 15-30, include user_prompt for topic filtering.",
)
async def create_flashcards(
    count: int,
    user_prompt: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> dict:
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "flashcard_generation")

    svc = FlashcardService(search_interface=ctx.search)
    group_id = await svc.create_flashcard_group_with_flashcards(
        project_id=ctx.project_id,
        count=count,
        user_prompt=user_prompt,
    )

    group = svc.get_flashcard_group(group_id)
    cards = svc.get_flashcards_by_group(group_id)

    group_dto = FlashcardGroupDto.model_validate(group)
    flashcards_dto = [FlashcardDto.model_validate(card) for card in cards]

    result = {
        **group_dto.model_dump(),
        "flashcards": [card.model_dump() for card in flashcards_dto],
    }

    return json.dumps(result, ensure_ascii=False, default=str)


@tool(
    "flashcards_create_scoped",
    description="Create flashcards from specific documents. Use when user references specific docs or IDs.",
)
async def create_flashcards_scoped(
    count: int,
    user_prompt: str,
    document_ids: list[str],
    query: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "flashcard_generation")

    svc = FlashcardService(search_interface=ctx.search)
    enhanced_prompt = build_enhanced_prompt(user_prompt, query, document_ids)

    group_id = await svc.create_flashcard_group_with_flashcards(
        project_id=ctx.project_id,
        count=count,
        user_prompt=enhanced_prompt,
    )

    group = svc.get_flashcard_group(group_id)
    cards = svc.get_flashcards_by_group(group_id)

    group_dto = FlashcardGroupDto.model_validate(group)
    flashcards_dto = [FlashcardDto.model_validate(card) for card in cards]

    result = {
        **group_dto.model_dump(),
        "flashcards": [card.model_dump() for card in flashcards_dto],
    }

    return json.dumps(result, ensure_ascii=False, default=str)


@tool("flashcards_list_groups", description="List flashcard groups for a project")
async def list_groups(runtime: ToolRuntime[CustomAgentContext]) -> str:
    ctx = runtime.context
    svc = FlashcardService(search_interface=ctx.search)
    groups = await asyncio.to_thread(svc.get_flashcard_groups, ctx.project_id)

    groups_dto = [FlashcardGroupDto.model_validate(g) for g in groups]
    result = {
        "data": [g.model_dump() for g in groups_dto],
        "count": len(groups_dto),
    }
    return json.dumps(result, ensure_ascii=False, default=str)


@tool("flashcards_get", description="Get flashcards in a group")
async def get_flashcards(
    group_id: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    svc = FlashcardService(search_interface=ctx.search)
    cards = await asyncio.to_thread(svc.get_flashcards_by_group, group_id)

    cards_dto = [FlashcardDto.model_validate(card) for card in cards]
    result = {
        "data": [card.model_dump() for card in cards_dto],
        "count": len(cards_dto),
    }
    return json.dumps(result, ensure_ascii=False, default=str)


@tool("flashcards_delete_group", description="Delete a flashcard group")
async def delete_group(
    group_id: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    svc = FlashcardService(search_interface=ctx.search)
    ok = await asyncio.to_thread(svc.delete_flashcard_group, group_id)

    result = {
        "success": ok,
        "group_id": group_id,
        "message": "Flashcard group successfully deleted."
        if ok
        else "Failed to delete flashcard group.",
    }
    return json.dumps(result, ensure_ascii=False)


@tool(
    "flashcards_update_group", description="Update a flashcard group's name/description"
)
async def update_group(
    group_id: str,
    name: str,
    description: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    svc = FlashcardService(search_interface=ctx.search)
    grp = await asyncio.to_thread(
        svc.update_flashcard_group, group_id, name=name, description=description
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
