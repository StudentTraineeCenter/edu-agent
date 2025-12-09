from __future__ import annotations

import asyncio
import json

from langchain.tools import tool
from langgraph.prebuilt import ToolRuntime

from core.agents.context import CustomAgentContext
from core.agents.utils import build_enhanced_prompt, increment_usage
from core.services.quizzes import QuizService
from schemas.quizzes import QuizDto, QuizQuestionDto


@tool(
    "quiz_create",
    description="Create quiz from project documents. Use count 10-30. custom_instructions should include topic, format preferences (length, difficulty), and any context.",
)
async def create_quiz(
    count: int,
    custom_instructions: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "quiz_generation")

    svc = QuizService(search_interface=ctx.search)
    quiz_id = await svc.create_quiz_with_questions(
        project_id=ctx.project_id,
        count=count,
        custom_instructions=custom_instructions,
    )

    quiz = svc.get_quiz(quiz_id)
    questions = svc.get_quiz_questions(quiz_id)

    quiz_dto = QuizDto.model_validate(quiz)
    questions_dto = [QuizQuestionDto.model_validate(q) for q in questions]

    result = {
        **quiz_dto.model_dump(),
        "questions": [q.model_dump() for q in questions_dto],
    }

    return json.dumps(result, ensure_ascii=False, default=str)


@tool(
    "quiz_create_scoped",
    description="Create quiz from specific documents. Use when user references specific docs or IDs.",
)
async def create_quiz_scoped(
    count: int,
    custom_instructions: str,
    document_ids: list[str],
    query: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "quiz_generation")

    svc = QuizService(search_interface=ctx.search)
    enhanced_prompt = build_enhanced_prompt(custom_instructions, query, document_ids)

    quiz_id = await svc.create_quiz_with_questions(
        project_id=ctx.project_id,
        count=count,
        custom_instructions=enhanced_prompt,
    )

    quiz = svc.get_quiz(quiz_id)
    questions = svc.get_quiz_questions(quiz_id)

    quiz_dto = QuizDto.model_validate(quiz)
    questions_dto = [QuizQuestionDto.model_validate(q) for q in questions]

    result = {
        **quiz_dto.model_dump(),
        "questions": [q.model_dump() for q in questions_dto],
    }

    return json.dumps(result, ensure_ascii=False, default=str)


@tool("quiz_list", description="List quizzes for a project")
async def list_quizzes(runtime: ToolRuntime[CustomAgentContext]) -> str:
    ctx = runtime.context
    svc = QuizService(search_interface=ctx.search)
    quizzes = await asyncio.to_thread(svc.get_quizzes, ctx.project_id)

    quizzes_dto = [QuizDto.model_validate(q) for q in quizzes]
    result = {
        "data": [q.model_dump() for q in quizzes_dto],
        "count": len(quizzes_dto),
    }
    return json.dumps(result, ensure_ascii=False, default=str)


@tool("quiz_get_questions", description="Get all questions in a quiz")
async def get_questions(
    quiz_id: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    svc = QuizService(search_interface=ctx.search)
    qs = await asyncio.to_thread(svc.get_quiz_questions, quiz_id)

    questions_dto = [QuizQuestionDto.model_validate(q) for q in qs]
    result = {
        "data": [q.model_dump() for q in questions_dto],
        "count": len(questions_dto),
    }
    return json.dumps(result, ensure_ascii=False, default=str)


@tool("quiz_delete", description="Delete a quiz")
async def delete_quiz(
    quiz_id: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    ctx = runtime.context
    svc = QuizService(search_interface=ctx.search)
    ok = await asyncio.to_thread(svc.delete_quiz, quiz_id)

    result = {
        "success": ok,
        "quiz_id": quiz_id,
        "message": "Kvíz byl úspěšně smazán." if ok else "Kvíz se nepodařilo smazat.",
    }
    return json.dumps(result, ensure_ascii=False)


tools = [
    create_quiz,
    # create_quiz_scoped,
    list_quizzes,
    get_questions,
    delete_quiz,
]
