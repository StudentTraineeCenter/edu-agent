from __future__ import annotations

import asyncio
import json

from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime

from core.agents.context import CustomAgentContext
from core.agents.utils import build_enhanced_prompt, increment_usage
from core.services.mind_maps import MindMapService
from schemas.mind_maps import MindMapDto


@tool(
    "mindmap_create",
    description="Create a mind map (visual diagram) from project documents. custom_instructions should include topic, format preferences, and any context.",
)
async def create_mind_map(
    custom_instructions: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    # TODO: Add mindmap_generation to usage tracking
    # increment_usage(ctx.usage, ctx.user_id, "mindmap_generation")

    svc = MindMapService(search_interface=ctx.search)
    mind_map = await svc.generate_mind_map(
        user_id=ctx.user_id,
        project_id=ctx.project_id,
        custom_instructions=custom_instructions,
    )

    mind_map_dto = MindMapDto.model_validate(mind_map)

    result = mind_map_dto.model_dump()

    return json.dumps(result, ensure_ascii=False, default=str)


@tool(
    "mindmap_create_scoped",
    description="Create a mind map from specific documents. Use when user references specific docs or IDs.",
)
async def create_mind_map_scoped(
    custom_instructions: str,
    document_ids: list[str],
    query: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    # TODO: Add mindmap_generation to usage tracking
    # increment_usage(ctx.usage, ctx.user_id, "mindmap_generation")

    svc = MindMapService(search_interface=ctx.search)
    enhanced_prompt = build_enhanced_prompt(custom_instructions, query, document_ids)

    mind_map = await svc.generate_mind_map(
        user_id=ctx.user_id,
        project_id=ctx.project_id,
        custom_instructions=enhanced_prompt,
    )

    mind_map_dto = MindMapDto.model_validate(mind_map)

    result = mind_map_dto.model_dump()

    return json.dumps(result, ensure_ascii=False, default=str)


@tool("mindmap_list", description="List mind maps for a project")
async def list_mind_maps(runtime: ToolRuntime[CustomAgentContext]) -> str:
    ctx = runtime.context
    svc = MindMapService(search_interface=ctx.search)
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
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    svc = MindMapService(search_interface=ctx.search)
    mind_map = await asyncio.to_thread(svc.get_mind_map, mind_map_id, ctx.user_id)

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
