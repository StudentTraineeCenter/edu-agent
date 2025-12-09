from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# ============================================================================
# Internal Service Layer Types
# ============================================================================


class QuizQuestionData(BaseModel):
    """Pydantic model for quiz question data structure."""

    question_text: str = Field(description="The quiz question text")
    option_a: str = Field(description="Option A")
    option_b: str = Field(description="Option B")
    option_c: str = Field(description="Option C")
    option_d: str = Field(description="Option D")
    correct_option: str = Field(description="Correct option: a, b, c, or d")
    explanation: str = Field(description="Explanation for the correct answer")
    difficulty_level: str = Field(description="Difficulty level: easy, medium, or hard")


class QuizGenerationRequest(BaseModel):
    """Pydantic model for quiz generation request."""

    name: str = Field(description="Generated name for the quiz")
    description: str = Field(description="Generated description for the quiz")
    questions: List[QuizQuestionData] = Field(
        description="List of generated quiz questions"
    )


class QuizGenerationResult(BaseModel):
    """Model for quiz generation result."""

    name: str
    description: str
    questions: List[QuizQuestionData]


class QuizAnswers(BaseModel):
    """Model for quiz answers submission."""

    answers: dict[str, str] = Field(
        description="Mapping of question IDs to user answers"
    )


class QuizQuestionResult(BaseModel):
    """Model for individual question result."""

    question_id: str
    question_text: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str
    difficulty_level: str


class QuizSubmissionResult(BaseModel):
    """Model for quiz submission result."""

    quiz_id: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    grade: str
    results: List[QuizQuestionResult]
    submitted_at: str


# ============================================================================
# API Request/Response Types
# ============================================================================


class QuizDto(BaseModel):
    """Quiz data transfer object."""

    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuizQuestionDto(BaseModel):
    """Quiz question data transfer object."""

    id: str
    quiz_id: str
    project_id: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: Optional[str] = None
    difficulty_level: str
    position: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateQuizRequest(BaseModel):
    """Request model for creating a quiz."""

    question_count: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Number of quiz questions to generate",
    )
    custom_instructions: Optional[str] = Field(
        None,
        max_length=2000,
        description="Custom instructions including topic, format preferences, length, and any additional context.",
    )
    length: Optional[str] = Field(
        None,
        pattern="^(less|normal|more)$",
        description="Length preference: less, normal, or more",
    )
    difficulty: Optional[str] = Field(
        None,
        pattern="^(easy|medium|hard)$",
        description="Overall difficulty level: easy, medium, or hard",
    )


class UpdateQuizRequest(BaseModel):
    """Request model for updating a quiz."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Name of the quiz"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Description of the quiz"
    )


class QuizResponse(BaseModel):
    """Response model for quiz operations."""

    quiz: QuizDto
    message: str


class QuizListResponse(BaseModel):
    """Response model for listing quizzes."""

    data: List[QuizDto] = Field(description="List of quizzes")


class QuizQuestionListResponse(BaseModel):
    """Response model for listing quiz questions."""

    data: List[QuizQuestionDto] = Field(description="List of quiz questions")


class CreateQuizQuestionRequest(BaseModel):
    """Request model for creating a quiz question."""

    question_text: str = Field(min_length=1, description="Question text")
    option_a: str = Field(min_length=1, description="Option A")
    option_b: str = Field(min_length=1, description="Option B")
    option_c: str = Field(min_length=1, description="Option C")
    option_d: str = Field(min_length=1, description="Option D")
    correct_option: str = Field(
        pattern="^(a|b|c|d)$", description="Correct option (a, b, c, or d)"
    )
    explanation: Optional[str] = Field(None, description="Explanation for the answer")
    difficulty_level: str = Field(
        default="medium",
        pattern="^(easy|medium|hard)$",
        description="Difficulty level",
    )
    position: Optional[int] = Field(
        None, ge=0, description="Position for ordering within quiz"
    )


class UpdateQuizQuestionRequest(BaseModel):
    """Request model for updating a quiz question."""

    question_text: Optional[str] = Field(
        None, min_length=1, description="Question text"
    )
    option_a: Optional[str] = Field(None, min_length=1, description="Option A")
    option_b: Optional[str] = Field(None, min_length=1, description="Option B")
    option_c: Optional[str] = Field(None, min_length=1, description="Option C")
    option_d: Optional[str] = Field(None, min_length=1, description="Option D")
    correct_option: Optional[str] = Field(
        None, pattern="^(a|b|c|d)$", description="Correct option (a, b, c, or d)"
    )
    explanation: Optional[str] = Field(None, description="Explanation for the answer")
    difficulty_level: Optional[str] = Field(
        None, pattern="^(easy|medium|hard)$", description="Difficulty level"
    )


class ReorderQuizQuestionsRequest(BaseModel):
    """Request model for reordering quiz questions."""

    question_ids: List[str] = Field(
        description="List of question IDs in the desired order"
    )


class QuizQuestionResponse(BaseModel):
    """Response model for quiz question operations."""

    question: QuizQuestionDto
    message: str


class QuizProgressUpdate(BaseModel):
    """Progress update for quiz generation streaming."""

    status: str = Field(
        description="Progress status: searching, analyzing, generating, done"
    )
    message: str = Field(description="Human-readable progress message")
    quiz_id: Optional[str] = Field(None, description="Quiz ID when done")
    error: Optional[str] = Field(None, description="Error message if failed")
