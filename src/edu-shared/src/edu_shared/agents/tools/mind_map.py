"""Mind map tools for agent."""

import asyncio
import json

from edu_shared.agents.context import CustomAgentContext
from edu_shared.agents.mind_map_agent import MindMapAgent
from edu_shared.schemas.mind_maps import MindMapDto
from edu_shared.services.mind_maps import MindMapService
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


@tool(
    "mindmap_create",
    description="Create a mind map (visual diagram) from project documents. custom_instructions should include topic, format preferences, and any context.",
)
async def create_mind_map(
    custom_instructions: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    """Create a mind map from project documents."""
    ctx = runtime.context
    # TODO: Add mindmap_generation to usage tracking
    # increment_usage(ctx.usage, ctx.user_id, "mindmap_generation")

    if not ctx.llm:
        return json.dumps(
            {"error": "LLM not available in context"},
            ensure_ascii=False
        )

    # Generate and create using agent
    mind_map_agent = MindMapAgent(
        search_service=ctx.search,
        llm=ctx.llm,
    )
    
    mind_map = await mind_map_agent.generate_and_save(
        project_id=ctx.project_id,
        topic=custom_instructions,
        custom_instructions=custom_instructions,
        user_id=ctx.user_id,
    )

    svc = MindMapService()
    mind_map_dto = MindMapDto.model_validate(svc._model_to_dto(mind_map))
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
    """Create a mind map from specific documents."""
    ctx = runtime.context
    # TODO: Add mindmap_generation to usage tracking
    # increment_usage(ctx.usage, ctx.user_id, "mindmap_generation")

    if not ctx.agent_config:
        return json.dumps(
            {"error": "Agent config not available in context"},
            ensure_ascii=False
        )

    enhanced_prompt = build_enhanced_prompt(custom_instructions, query, document_ids)

    if not ctx.llm:
        return json.dumps(
            {"error": "LLM not available in context"},
            ensure_ascii=False
        )

    # Generate and create using agent
    mind_map_agent = MindMapAgent(
        search_service=ctx.search,
        llm=ctx.llm,
    )
    
    mind_map = await mind_map_agent.generate_and_save(
        project_id=ctx.project_id,
        topic=query,
        custom_instructions=enhanced_prompt,
        user_id=ctx.user_id,
    )

    svc = MindMapService()
    mind_map_dto = MindMapDto.model_validate(svc._model_to_dto(mind_map))
    result = mind_map_dto.model_dump()

    return json.dumps(result, ensure_ascii=False, default=str)


@tool("mindmap_list", description="List mind maps for a project")
async def list_mind_maps(runtime: ToolRuntime[CustomAgentContext]) -> str:
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
    runtime: ToolRuntime[CustomAgentContext],
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
