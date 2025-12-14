"""Quiz tools for agent."""

import asyncio
import json

from edu_shared.agents.context import CustomAgentContext
from edu_shared.schemas.quizzes import QuizDto, QuizQuestionDto
from edu_shared.services.quizzes import QuizService
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
    "quiz_create",
    description="Create quiz from project documents. Use count 10-30. custom_instructions should include topic, format preferences (length, difficulty), and any context.",
)
async def create_quiz(
    count: int,
    custom_instructions: str,
    runtime: ToolRuntime[CustomAgentContext],
) -> str:
    """Create quiz from project documents."""
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "quiz_generation")

    if not ctx.llm:
        return json.dumps(
            {"error": "LLM not available in context"},
            ensure_ascii=False
        )

    svc = QuizService()
    # Create a new quiz first
    quiz = svc.create_quiz(
        project_id=ctx.project_id,
        name="Generated Quiz",
        description="AI-generated quiz",
    )

    # Then generate and populate it
    result = await svc.generate_and_populate(
        quiz_id=quiz.id,
        project_id=ctx.project_id,
        search_service=ctx.search,
        llm=ctx.llm,
        topic=custom_instructions,
        custom_instructions=custom_instructions,
        count=count,
    )

    # Get questions
    questions = await asyncio.to_thread(svc.list_quiz_questions, quiz.id, ctx.project_id)

    quiz_dto = QuizDto.model_validate(result)
    questions_dto = [QuizQuestionDto.model_validate(q) for q in questions]

    result_dict = {
        **quiz_dto.model_dump(),
        "questions": [q.model_dump() for q in questions_dto],
    }

    return json.dumps(result_dict, ensure_ascii=False, default=str)


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
    """Create quiz from specific documents."""
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "quiz_generation")

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

    svc = QuizService()
    # Create a new quiz first
    quiz = svc.create_quiz(
        project_id=ctx.project_id,
        name="Generated Quiz",
        description="AI-generated quiz",
    )

    # Then generate and populate it
    result = await svc.generate_and_populate(
        quiz_id=quiz.id,
        project_id=ctx.project_id,
        search_service=ctx.search,
        llm=ctx.llm,
        topic=query,
        custom_instructions=enhanced_prompt,
        count=count,
    )

    # Get questions
    questions = await asyncio.to_thread(svc.list_quiz_questions, quiz.id, ctx.project_id)

    quiz_dto = QuizDto.model_validate(result)
    questions_dto = [QuizQuestionDto.model_validate(q) for q in questions]

    result_dict = {
        **quiz_dto.model_dump(),
        "questions": [q.model_dump() for q in questions_dto],
    }

    return json.dumps(result_dict, ensure_ascii=False, default=str)


@tool("quiz_list", description="List quizzes for a project")
async def list_quizzes(runtime: ToolRuntime[CustomAgentContext]) -> str:
    """List quizzes for a project."""
    ctx = runtime.context
    svc = QuizService()
    quizzes = await asyncio.to_thread(svc.list_quizzes, ctx.project_id)

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
    """Get all questions in a quiz."""
    ctx = runtime.context
    svc = QuizService()
    qs = await asyncio.to_thread(svc.list_quiz_questions, quiz_id, ctx.project_id)

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
    """Delete a quiz."""
    ctx = runtime.context
    svc = QuizService()
    await asyncio.to_thread(svc.delete_quiz, quiz_id, ctx.project_id)

    result = {
        "success": True,
        "quiz_id": quiz_id,
        "message": "Quiz successfully deleted.",
    }
    return json.dumps(result, ensure_ascii=False)


tools = [
    create_quiz,
    # create_quiz_scoped,
    list_quizzes,
    get_questions,
    delete_quiz,
]
