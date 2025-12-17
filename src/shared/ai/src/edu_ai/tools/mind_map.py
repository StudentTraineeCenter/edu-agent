"""Mind map tools for agent."""

import asyncio
import json
from contextlib import suppress

from edu_ai.chatbot.context import ChatbotContext
from edu_core.schemas.mind_maps import MindMapDto
from edu_core.services.mind_maps import MindMapService
from edu_queue.schemas import MindMapGenerationData, QueueTaskMessage, TaskType
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
    "mindmap_create",
    description="Create a mind map (visual diagram) from project documents. Provide a short topic plus optional custom instructions (structure, depth, focus, etc.).",
)
async def create_mind_map(
    topic: str,
    runtime: ToolRuntime[ChatbotContext],
    custom_instructions: str | None = None,
) -> str:
    """Create a mind map from project documents."""
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "mindmap_generation")

    # Send message to queue
    queue_service = runtime.context.queue
    message = QueueTaskMessage(
        type=TaskType.MIND_MAP_GENERATION,
        data=MindMapGenerationData(
            project_id=ctx.project_id,
            topic=topic,
            custom_instructions=custom_instructions,
            user_id=ctx.user_id,
        ),
    )
    queue_service.send_message(message)

    return json.dumps(
        {
            "status": "queued",
            "message": "Your request to generate a mind map has been queued.",
        },
        ensure_ascii=False,
    )


@tool(
    "mindmap_create_scoped",
    description="Create a mind map from specific documents. Use when user references specific docs or IDs.",
)
async def create_mind_map_scoped(
    custom_instructions: str,
    document_ids: list[str],
    query: str,
    runtime: ToolRuntime[ChatbotContext],
) -> str:
    """Create a mind map from specific documents."""
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "mindmap_generation")

    enhanced_prompt = build_enhanced_prompt(custom_instructions, query, document_ids)

    # Send message to queue
    queue_service = runtime.context.queue
    message = QueueTaskMessage(
        type=TaskType.MIND_MAP_GENERATION,
        data=MindMapGenerationData(
            project_id=ctx.project_id,
            topic=query,
            custom_instructions=enhanced_prompt,
            user_id=ctx.user_id,
        ),
    )
    queue_service.send_message(message)

    return json.dumps(
        {
            "status": "queued",
            "message": "Your request to generate a mind map from specific documents has been queued.",
        },
        ensure_ascii=False,
    )


@tool("mindmap_list", description="List mind maps for a project")
async def list_mind_maps(runtime: ToolRuntime[ChatbotContext]) -> str:
    """List mind maps for a project."""
    ctx = runtime.context
    svc = MindMapService()
    mind_maps = await asyncio.to_thread(svc.list_mind_maps, ctx.project_id, ctx.user_id)

    mind_maps_dto = [MindMapDto.model_validate(m) for m in mind_maps]
    result = {
        "data": [m.model_dump() for m in mind_maps_dto],
        "count": len(mind_maps_dto),
    }
    return json.dumps(result, ensure_ascii=False, default=str)


@tool("mindmap_get", description="Get a specific mind map by ID")
async def get_mind_map(
    mind_map_id: str,
    runtime: ToolRuntime[ChatbotContext],
) -> str:
    """Get a specific mind map by ID."""
    ctx = runtime.context
    svc = MindMapService()
    mind_map = await asyncio.to_thread(
        svc.get_mind_map, mind_map_id, ctx.project_id, ctx.user_id
    )

    if not mind_map:
        return json.dumps({"error": "Mind map not found"}, ensure_ascii=False)

    mind_map_dto = MindMapDto.model_validate(mind_map)
    result = mind_map_dto.model_dump()
    return json.dumps(result, ensure_ascii=False, default=str)


tools = [
    create_mind_map,
    # create_mind_map_scoped,
    list_mind_maps,
    get_mind_map,
]
