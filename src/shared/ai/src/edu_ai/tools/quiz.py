"""Quiz tools for agent."""

import asyncio
import json
from contextlib import suppress

from edu_ai.chatbot.context import ChatbotContext
from edu_core.schemas.quizzes import QuizDto, QuizQuestionDto
from edu_core.services.quizzes import QuizService
from edu_queue.schemas import QueueTaskMessage, QuizGenerationData, TaskType
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
    "quiz_create",
    description="Create a quiz from project documents. Use count 10-30. Provide a short topic plus optional custom instructions (difficulty, focus areas, style, etc.).",
)
async def create_quiz(
    count: int,
    topic: str,
    runtime: ToolRuntime[ChatbotContext],
    custom_instructions: str | None = None,
) -> str:
    """Create quiz from project documents."""
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "quiz_generation")

    svc = QuizService()
    # Create a new quiz first
    quiz = svc.create_quiz(
        project_id=ctx.project_id,
        name="Generated Quiz",
        description="AI-generated quiz",
    )

    # Send message to queue
    queue_service = runtime.context.queue
    message = QueueTaskMessage(
        type=TaskType.QUIZ_GENERATION,
        data=QuizGenerationData(
            project_id=ctx.project_id,
            quiz_id=quiz.id,
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
            "message": "Your request to generate a quiz has been queued.",
            "quiz_id": quiz.id,
        },
        ensure_ascii=False,
    )


@tool(
    "quiz_create_scoped",
    description="Create quiz from specific documents. Use when user references specific docs or IDs.",
)
async def create_quiz_scoped(
    count: int,
    custom_instructions: str,
    document_ids: list[str],
    query: str,
    runtime: ToolRuntime[ChatbotContext],
) -> str:
    """Create quiz from specific documents."""
    ctx = runtime.context
    increment_usage(ctx.usage, ctx.user_id, "quiz_generation")

    enhanced_prompt = build_enhanced_prompt(custom_instructions, query, document_ids)

    svc = QuizService()
    # Create a new quiz first
    quiz = svc.create_quiz(
        project_id=ctx.project_id,
        name="Generated Quiz",
        description="AI-generated quiz",
    )

    # Send message to queue
    queue_service = runtime.context.queue
    message = QueueTaskMessage(
        type=TaskType.QUIZ_GENERATION,
        data=QuizGenerationData(
            project_id=ctx.project_id,
            quiz_id=quiz.id,
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
            "message": "Your request to generate a quiz from specific documents has been queued.",
            "quiz_id": quiz.id,
        },
        ensure_ascii=False,
    )


@tool("quiz_list", description="List quizzes for a project")
async def list_quizzes(runtime: ToolRuntime[ChatbotContext]) -> str:
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
    runtime: ToolRuntime[ChatbotContext],
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
    runtime: ToolRuntime[ChatbotContext],
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
