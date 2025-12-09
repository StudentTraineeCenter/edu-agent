from __future__ import annotations

import asyncio
import json

from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime

from core.agents.context import CustomAgentContext
from core.agents.utils import build_enhanced_prompt, increment_usage
from core.services.notes import NoteService
from schemas.notes import NoteDto


@tool(
    "note_create",
    description="Create a study note (markdown document) from project documents. custom_instructions should include topic, format preferences (length), and any context.",
)
async def create_note(
    custom_instructions: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "note_generation")

    svc = NoteService(search_interface=ctx.search)
    note_id = await svc.create_note_with_content(
        project_id=ctx.project_id,
        custom_instructions=custom_instructions,
    )

    note = svc.get_note(note_id)

    if not note:
        return json.dumps(
            {"error": "Failed to retrieve created note"}, ensure_ascii=False
        )

    note_dto = NoteDto.model_validate(note)

    result = note_dto.model_dump()

    return json.dumps(result, ensure_ascii=False, default=str)


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
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "note_generation")

    svc = NoteService(search_interface=ctx.search)
    enhanced_prompt = build_enhanced_prompt(custom_instructions, query, document_ids)

    note_id = await svc.create_note_with_content(
        project_id=ctx.project_id,
        custom_instructions=enhanced_prompt,
    )

    note = svc.get_note(note_id)

    if not note:
        return json.dumps(
            {"error": "Failed to retrieve created note"}, ensure_ascii=False
        )

    note_dto = NoteDto.model_validate(note)

    result = note_dto.model_dump()

    return json.dumps(result, ensure_ascii=False, default=str)


@tool("note_list", description="List notes for a project")
async def list_notes(runtime: ToolRuntime[CustomAgentContext]) -> str:
    ctx = runtime.context
    svc = NoteService(search_interface=ctx.search)
    notes = await asyncio.to_thread(svc.get_notes, ctx.project_id)

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
    ctx = runtime.context
    svc = NoteService(search_interface=ctx.search)
    note = await asyncio.to_thread(svc.get_note, note_id)

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
    ctx = runtime.context
    svc = NoteService(search_interface=ctx.search)
    ok = await asyncio.to_thread(svc.delete_note, note_id)

    result = {
        "success": ok,
        "note_id": note_id,
        "message": "Note successfully deleted." if ok else "Failed to delete note.",
    }
    return json.dumps(result, ensure_ascii=False)


tools = [
    create_note,
    # create_note_scoped,
    list_notes,
    get_note,
    delete_note,
]
