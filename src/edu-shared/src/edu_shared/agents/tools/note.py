"""Note tools for agent."""

import asyncio
import json

from edu_shared.agents.context import CustomAgentContext
from edu_shared.agents.note_agent import NoteAgent
from edu_shared.schemas.notes import NoteDto
from edu_shared.services.notes import NoteService
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
    try:
        usage.check_and_increment(user_id, feature)
    except Exception:
        # Log but don't fail
        pass


@tool(
    "note_create",
    description="Create a study note (markdown document) from project documents. custom_instructions should include topic, format preferences (length), and any context.",
)
async def create_note(
    custom_instructions: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    """Create a study note from project documents."""
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "note_generation")

    if not ctx.llm:
        return json.dumps(
            {"error": "LLM not available in context"},
            ensure_ascii=False
        )

    svc = NoteService()
    # Create a new note first
    note = svc.create_note(
        project_id=ctx.project_id,
        title="Generated Note",
        description="AI-generated study note",
    )

    # Generate and populate using agent
    note_agent = NoteAgent(
        search_service=ctx.search,
        llm=ctx.llm,
    )
    
    note = await note_agent.generate_and_save(
        project_id=ctx.project_id,
        topic=custom_instructions,
        custom_instructions=custom_instructions,
        note_id=note.id,
    )

    note_dto = NoteDto.model_validate(svc._model_to_dto(note))
    result_dict = note_dto.model_dump()

    return json.dumps(result_dict, ensure_ascii=False, default=str)


@tool(
    "note_create_scoped",
    description="Create a study note from specific documents. Use when user references specific docs or IDs.",
)
async def create_note_scoped(
    custom_instructions: str,
    document_ids: list[str],
    query: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    """Create a study note from specific documents."""
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "note_generation")

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

    svc = NoteService()
    # Create a new note first
    note = svc.create_note(
        project_id=ctx.project_id,
        title="Generated Note",
        description="AI-generated study note",
    )

    # Generate and populate using agent
    note_agent = NoteAgent(
        search_service=ctx.search,
        llm=ctx.llm,
    )
    
    note = await note_agent.generate_and_save(
        project_id=ctx.project_id,
        topic=query,
        custom_instructions=enhanced_prompt,
        note_id=note.id,
    )

    note_dto = NoteDto.model_validate(svc._model_to_dto(note))
    result_dict = note_dto.model_dump()

    return json.dumps(result_dict, ensure_ascii=False, default=str)


@tool("note_list", description="List notes for a project")
async def list_notes(runtime: ToolRuntime[CustomAgentContext]) -> str:
    """List notes for a project."""
    ctx = runtime.context
    svc = NoteService()
    notes = await asyncio.to_thread(svc.list_notes, ctx.project_id)

    notes_dto = [NoteDto.model_validate(n) for n in notes]
    result = {
        "data": [n.model_dump() for n in notes_dto],
        "count": len(notes_dto),
    }
    return json.dumps(result, ensure_ascii=False, default=str)


@tool("note_get", description="Get a specific note by ID")
async def get_note(
    note_id: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    """Get a specific note by ID."""
    ctx = runtime.context
    svc = NoteService()
    note = await asyncio.to_thread(svc.get_note, note_id, ctx.project_id)

    if not note:
        return json.dumps({"error": "Note not found"}, ensure_ascii=False)

    note_dto = NoteDto.model_validate(note)
    result = note_dto.model_dump()
    return json.dumps(result, ensure_ascii=False, default=str)


@tool("note_delete", description="Delete a note")
async def delete_note(
    note_id: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    """Delete a note."""
    ctx = runtime.context
    svc = NoteService()
    await asyncio.to_thread(svc.delete_note, note_id, ctx.project_id)

    result = {
        "success": True,
        "note_id": note_id,
        "message": "Note successfully deleted.",
    }
    return json.dumps(result, ensure_ascii=False)


tools = [
    create_note,
    # create_note_scoped,
    list_notes,
    get_note,
    delete_note,
]
