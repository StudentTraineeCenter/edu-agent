from typing import List
from pydantic import BaseModel, Field
from edu_shared.agents.base import BaseContentAgent


class QuizQuestionGenerationResult(BaseModel):
    """Pydantic model for quiz question data structure."""

    question_text: str = Field(..., description="The quiz question text")
    option_a: str = Field(..., description="Option A")
    option_b: str = Field(..., description="Option B")
    option_c: str = Field(..., description="Option C")
    option_d: str = Field(..., description="Option D")
    correct_option: str = Field(..., description="Correct option: a, b, c, or d")
    explanation: str = Field(..., description="Explanation for the correct answer")
    difficulty_level: str = Field(..., description="Difficulty level: easy, medium, or hard")


class QuizGenerationResult(BaseModel):
    """Model for quiz generation result."""

    name: str = Field(..., description="The name of the quiz")
    description: str = Field(..., description="The description of the quiz")
    questions: List[QuizQuestionGenerationResult] = Field(..., description="The questions of the quiz")


class QuizAgent(BaseContentAgent[QuizGenerationResult]):
    @property
    def output_model(self):
        return QuizGenerationResult

    @property
    def prompt_template(self):
        return "quiz_prompt"

