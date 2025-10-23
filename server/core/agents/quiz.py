from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from core.agents.llm import make_llm_streaming
from core.agents.search import SearchInterface
from core.services.quizzes import QuizService
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class CreateQuizInput(BaseModel):
    project_id: str
    count: int = Field(20, ge=1, le=100)
    user_prompt: Optional[str] = None


class CreateQuizScopedInput(CreateQuizInput):
    document_ids: Optional[List[str]] = Field(default=None)
    query: Optional[str] = None


class CreateQuizOutput(BaseModel):
    message: str
    name: str
    description: str
    questions: List[Dict[str, Any]]


class ListQuizzesInput(BaseModel):
    project_id: str


class ListQuizzesOutput(BaseModel):
    quizzes: List[Dict[str, Any]]


class GetQuizQuestionsInput(BaseModel):
    quiz_id: str


class GetQuizQuestionsOutput(BaseModel):
    questions: List[Dict[str, Any]]


class SubmitQuizAnswersInput(BaseModel):
    quiz_id: str
    answers: Dict[str, str] = Field(
        ..., description="Map question_id -> selected option letter (a/b/c/d)"
    )


class DeleteQuizInput(BaseModel):
    quiz_id: str


def build_quiz_tools(search_interface: SearchInterface):
    svc = QuizService(search_interface=search_interface)

    async def _create_quiz(
        project_id: str, count: int = 20, user_prompt: Optional[str] = None
    ) -> CreateQuizOutput:
        quiz_id = await svc.create_quiz_with_questions(
            project_id=project_id,
            count=count,
            user_prompt=user_prompt,
        )
        quiz = await asyncio.to_thread(lambda: svc.get_quiz(quiz_id))
        qs = await asyncio.to_thread(lambda: svc.get_quiz_questions(quiz_id))
        return CreateQuizOutput(
            message=f"✅ Quiz created successfully! I've generated {len(qs)} questions for you. You can now start taking the quiz.",
            name=quiz.name,
            description=quiz.description or "",
            questions=[
                {
                    "question_text": q.question_text,
                    "option_a": q.option_a,
                    "option_b": q.option_b,
                    "option_c": q.option_c,
                    "option_d": q.option_d,
                    "correct_option": q.correct_option,
                    "difficulty_level": q.difficulty_level,
                    "explanation": q.explanation,
                }
                for q in qs
            ],
        )

    async def _create_quiz_scoped(
        project_id: str,
        count: int = 20,
        user_prompt: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        query: Optional[str] = None,
    ) -> CreateQuizOutput:
        # For now, the service doesn't support document scoping, so we'll use the general method
        # TODO: Implement document scoping in the service layer
        enhanced_prompt = user_prompt or ""
        if query:
            enhanced_prompt += f" Focus on: {query}"
        if document_ids:
            enhanced_prompt += (
                f" Based on specific documents: {', '.join(document_ids)}"
            )

        quiz_id = await svc.create_quiz_with_questions(
            project_id=project_id,
            count=count,
            user_prompt=enhanced_prompt,
        )
        quiz = await asyncio.to_thread(lambda: svc.get_quiz(quiz_id))
        qs = await asyncio.to_thread(lambda: svc.get_quiz_questions(quiz_id))
        return CreateQuizOutput(
            message=f"✅ Quiz created successfully! I've generated {len(qs)} questions for you. You can now start taking the quiz.",
            name=quiz.name,
            description=quiz.description or "",
            questions=[
                {
                    "question_text": q.question_text,
                    "option_a": q.option_a,
                    "option_b": q.option_b,
                    "option_c": q.option_c,
                    "option_d": q.option_d,
                    "correct_option": q.correct_option,
                    "difficulty_level": q.difficulty_level,
                    "explanation": q.explanation,
                }
                for q in qs
            ],
        )

    async def _list_quizzes(project_id: str) -> ListQuizzesOutput:
        quizzes = await asyncio.to_thread(lambda: svc.get_quizzes(project_id))
        return {
            "quizzes": [
                {
                    "id": q.id,
                    "name": q.name,
                    "description": q.description,
                    "created_at": q.created_at.isoformat(),
                }
                for q in quizzes
            ]
        }

    async def _get_questions(quiz_id: str) -> GetQuizQuestionsOutput:
        qs = await asyncio.to_thread(lambda: svc.get_quiz_questions(quiz_id))
        return {
            "questions": [
                {
                    "id": x.id,
                    "question_text": x.question_text,
                    "option_a": x.option_a,
                    "option_b": x.option_b,
                    "option_c": x.option_c,
                    "option_d": x.option_d,
                    "correct_option": x.correct_option,
                    "difficulty_level": x.difficulty_level,
                }
                for x in qs
            ]
        }

    async def _submit_answers(quiz_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
        result = await svc.submit_quiz_answers(quiz_id, answers)
        return result

    async def _delete_quiz(quiz_id: str) -> Dict[str, bool]:
        ok = await asyncio.to_thread(lambda: svc.delete_quiz(quiz_id))
        return {"deleted": bool(ok)}

    return [
        StructuredTool.from_function(
            name="quiz_create",
            description="Create a new quiz grounded in project documents",
            coroutine=_create_quiz,
            args_schema=CreateQuizInput,
            return_direct=False,
        ),
        StructuredTool.from_function(
            name="quiz_create_scoped",
            description=(
                "Create a quiz but restrict to selected documents and/or a focus query. "
                "Use when the user says 'from this and this' or specifies doc IDs/titles."
            ),
            coroutine=_create_quiz_scoped,
            args_schema=CreateQuizScopedInput,
            return_direct=False,
        ),
        StructuredTool.from_function(
            name="quiz_list",
            description="List quizzes for a project",
            coroutine=lambda **kw: _list_quizzes(**kw),
            args_schema=ListQuizzesInput,
            return_direct=False,
        ),
        StructuredTool.from_function(
            name="quiz_get_questions",
            description="Get all questions in a quiz",
            coroutine=lambda **kw: _get_questions(**kw),
            args_schema=GetQuizQuestionsInput,
            return_direct=False,
        ),
        StructuredTool.from_function(
            name="quiz_submit_answers",
            description="Submit answers for a quiz and get results",
            coroutine=lambda **kw: _submit_answers(**kw),
            args_schema=SubmitQuizAnswersInput,
            return_direct=False,
        ),
        StructuredTool.from_function(
            name="quiz_delete",
            description="Delete a quiz",
            coroutine=lambda **kw: _delete_quiz(**kw),
            args_schema=DeleteQuizInput,
            return_direct=False,
        ),
    ]


def build_quiz_agent(
    project_id: str,
    language_code: str,
    search_interface: SearchInterface,
) -> AgentExecutor:
    tools = build_quiz_tools(search_interface)

    system = (
        f"You are a quiz authoring assistant. Always respond in {language_code}.\n"
        f"Prefer creating quizzes grounded in the project's documents.\n"
        f"When asked to create a quiz, CALL `quiz_create` with a sensible count (10-40).\n"
        f"\n"
        f"IMPORTANT: After the tool returns, extract ONLY the 'message' field from the tool output and return it to the user.\n"
        f"DO NOT return the full JSON, the questions array, or any other fields.\n"
        f"DO NOT use backticks, code blocks, or any markdown formatting.\n"
        f"Just return the message field value as plain text.\n"
        f"\n"
        f"Example:\n"
        f"Tool returns: {{'message': 'Quiz created!', 'questions': [...]}}\n"
        f"You respond: Quiz created!\n"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_openai_tools_agent(make_llm_streaming(), tools, prompt)
    return AgentExecutor(
        agent=agent, tools=tools, verbose=False, handle_parsing_errors=True
    )
