from datetime import datetime
from typing import Any
from uuid import uuid4

from edu_core.exceptions import NotFoundError
from edu_db.models import Project, Quiz, QuizQuestion
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field

from edu_ai.agents.topic_graph_agent import TopicGraphAgent
from edu_ai.agents.utils import generate, get_db_session


class QuizQuestionGenerationResult(BaseModel):
    """Pydantic model for quiz question data structure."""

    question_text: str = Field(..., description="The quiz question text")
    option_a: str = Field(..., description="Option A")
    option_b: str = Field(..., description="Option B")
    option_c: str = Field(..., description="Option C")
    option_d: str = Field(..., description="Option D")
    correct_option: str = Field(..., description="Correct option: a, b, c, or d")
    explanation: str = Field(..., description="Explanation for the correct answer")
    difficulty_level: str = Field(
        ..., description="Difficulty level: easy, medium, or hard"
    )


class QuizGenerationResult(BaseModel):
    """Model for quiz generation result."""

    name: str = Field(..., description="The name of the quiz")
    description: str = Field(..., description="The description of the quiz")
    questions: list[QuizQuestionGenerationResult] = Field(
        ..., description="The questions of the quiz"
    )


class QuizAgent:
    output_model = QuizGenerationResult
    prompt_template = "quiz_prompt"

    def __init__(
        self,
        search_service: Any,
        llm: AzureChatOpenAI,
        topic_graph_agent: TopicGraphAgent | None = None,
    ):
        self.search_service = search_service
        self.llm = llm
        self.topic_graph_agent = topic_graph_agent

    async def generate_and_save(
        self,
        project_id: str,
        topic: str | None = None,
        custom_instructions: str | None = None,
        quiz_id: str | None = None,
        count: int | None = None,
        **kwargs: Any,
    ) -> Quiz:
        """Generate quiz questions and save to the database.

        Args:
            project_id: The project ID
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            quiz_id: The quiz ID to populate (required)
            count: Optional count of questions to generate

        Returns:
            Updated Quiz model

        Raises:
            NotFoundError: If quiz or project not found
            ValueError: If quiz_id is not provided
        """
        if not quiz_id:
            raise ValueError("quiz_id is required for quiz generation")

        with get_db_session() as db:
            # Find existing quiz
            quiz = (
                db.query(Quiz)
                .filter(
                    Quiz.id == quiz_id,
                    Quiz.project_id == project_id,
                )
                .first()
            )
            if not quiz:
                raise NotFoundError(f"Quiz {quiz_id} not found")

            # Get project language code
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise NotFoundError(f"Project {project_id} not found")
            language_code = project.language_code

            generation_topic = topic
            if self.topic_graph_agent:
                topic_graph = await self.topic_graph_agent.generate_topic_graph(
                    project_id=project_id,
                    topic=topic,
                    custom_instructions=custom_instructions,
                )
                if topic_graph.root_topics:
                    topics = []
                    for root_topic in topic_graph.root_topics:
                        topics.append(root_topic.topic)
                        for subtopic in root_topic.subtopics:
                            topics.append(subtopic.topic)
                    generation_topic = ", ".join(topics)

            # Generate quiz using AI
            kwargs = {}
            if count is not None:
                kwargs["count"] = count

            result = await generate(
                llm=self.llm,
                search_service=self.search_service,
                output_model=self.output_model,
                prompt_template=self.prompt_template,
                project_id=project_id,
                topic=generation_topic or "",
                language_code=language_code,
                custom_instructions=custom_instructions,
                **kwargs,
            )

            # Update quiz with generated name and description
            quiz.name = result.name
            quiz.description = result.description
            quiz.updated_at = datetime.now()
            db.flush()

            # Delete existing questions and create new ones
            db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).delete()

            # Save quiz questions
            for position, question_item in enumerate(result.questions):
                quiz_question = QuizQuestion(
                    id=str(uuid4()),
                    quiz_id=quiz_id,
                    project_id=project_id,
                    question_text=question_item.question_text,
                    option_a=question_item.option_a,
                    option_b=question_item.option_b,
                    option_c=question_item.option_c,
                    option_d=question_item.option_d,
                    correct_option=question_item.correct_option,
                    explanation=question_item.explanation,
                    difficulty_level=question_item.difficulty_level,
                    position=position,
                    created_at=datetime.now(),
                )
                db.add(quiz_question)

            db.flush()
            return quiz
