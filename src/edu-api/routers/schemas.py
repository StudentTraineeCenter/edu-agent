"""Request schemas for CRUD operations."""

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., description="Name of the project")
    description: str | None = Field(None, description="Description of the project")
    language_code: str = Field(
        default="en", description="Language code for the project"
    )


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, description="Name of the project")
    description: str | None = Field(None, description="Description of the project")
    language_code: str | None = Field(None, description="Language code for the project")


class DocumentCreate(BaseModel):
    file_name: str = Field(..., description="Name of the document file")
    file_type: str = Field(..., description="File extension (pdf, docx, txt, etc.)")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    summary: str | None = Field(
        None, description="Auto-generated summary of the document"
    )


class DocumentUpdate(BaseModel):
    file_name: str | None = Field(None, description="Name of the document file")
    summary: str | None = Field(
        None, description="Auto-generated summary of the document"
    )


class ChatCreate(BaseModel):
    title: str | None = Field(None, description="Title of the chat")


class ChatUpdate(BaseModel):
    title: str | None = Field(None, description="Title of the chat")


class NoteCreate(BaseModel):
    title: str = Field(..., description="Title of the note")
    content: str = Field(..., description="Content of the note")
    description: str | None = Field(None, description="Description of the note")


class NoteUpdate(BaseModel):
    title: str | None = Field(None, description="Title of the note")
    content: str | None = Field(None, description="Content of the note")
    description: str | None = Field(None, description="Description of the note")


class QuizCreate(BaseModel):
    name: str = Field(..., description="Name of the quiz")
    description: str | None = Field(None, description="Description of the quiz")


class QuizUpdate(BaseModel):
    name: str | None = Field(None, description="Name of the quiz")
    description: str | None = Field(None, description="Description of the quiz")


class FlashcardGroupCreate(BaseModel):
    name: str = Field(..., description="Name of the flashcard group")
    description: str | None = Field(
        None, description="Description of the flashcard group"
    )
    study_session_id: str | None = Field(
        None, description="ID of the study session if this group belongs to one"
    )


class FlashcardGroupUpdate(BaseModel):
    name: str | None = Field(None, description="Name of the flashcard group")
    description: str | None = Field(
        None, description="Description of the flashcard group"
    )


class ChatCompletionRequest(BaseModel):
    message: str = Field(..., description="User message to process")


class FlashcardCreate(BaseModel):
    question: str = Field(..., description="Question of the flashcard")
    answer: str = Field(..., description="Answer of the flashcard")
    difficulty_level: str = Field(
        default="medium", description="Difficulty level (easy, medium, hard)"
    )
    position: int | None = Field(
        None, description="Position for ordering within the group"
    )


class FlashcardUpdate(BaseModel):
    question: str | None = Field(None, description="Question of the flashcard")
    answer: str | None = Field(None, description="Answer of the flashcard")
    difficulty_level: str | None = Field(
        None, description="Difficulty level (easy, medium, hard)"
    )
    position: int | None = Field(
        None, description="Position for ordering within the group"
    )


class QuizQuestionCreate(BaseModel):
    question_text: str = Field(..., description="The quiz question text")
    option_a: str = Field(..., description="Option A")
    option_b: str = Field(..., description="Option B")
    option_c: str = Field(..., description="Option C")
    option_d: str = Field(..., description="Option D")
    correct_option: str = Field(..., description="Correct option: a, b, c, or d")
    explanation: str | None = Field(
        None, description="Explanation for the correct answer"
    )
    difficulty_level: str = Field(
        default="medium", description="Difficulty level (easy, medium, hard)"
    )
    position: int | None = Field(
        None, description="Position for ordering within the quiz"
    )


class QuizQuestionUpdate(BaseModel):
    question_text: str | None = Field(None, description="The quiz question text")
    option_a: str | None = Field(None, description="Option A")
    option_b: str | None = Field(None, description="Option B")
    option_c: str | None = Field(None, description="Option C")
    option_d: str | None = Field(None, description="Option D")
    correct_option: str | None = Field(
        None, description="Correct option: a, b, c, or d"
    )
    explanation: str | None = Field(
        None, description="Explanation for the correct answer"
    )
    difficulty_level: str | None = Field(
        None, description="Difficulty level (easy, medium, hard)"
    )
    position: int | None = Field(
        None, description="Position for ordering within the quiz"
    )


class QuizQuestionReorder(BaseModel):
    question_ids: list[str] = Field(
        ..., description="List of question IDs in the desired order"
    )


class PracticeRecordCreate(BaseModel):
    item_type: str = Field(
        ...,
        pattern="^(flashcard|quiz)$",
        description="Type of study resource: flashcard or quiz",
    )
    item_id: str = Field(
        ..., description="ID of the study resource (flashcard or quiz question)"
    )
    topic: str = Field(..., max_length=500, description="Topic extracted from question")
    user_answer: str | None = Field(
        None, description="User's answer (only for quizzes, null for flashcards)"
    )
    correct_answer: str = Field(
        ..., description="The correct answer - flashcard answer or quiz correct option"
    )
    was_correct: bool = Field(..., description="Whether the user got it right")


class PracticeRecordBatchCreate(BaseModel):
    practice_records: list[PracticeRecordCreate] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of practice records to create",
    )


class MindMapCreate(BaseModel):
    title: str = Field(..., description="Title of the mind map")
    description: str | None = Field(None, description="Description of the mind map")
    custom_instructions: str | None = Field(
        None, description="Custom instructions for AI generation"
    )


class StudySessionCreate(BaseModel):
    session_length_minutes: int = Field(
        30, ge=10, le=120, description="Length of the study session in minutes"
    )
    focus_topics: list[str] | None = Field(None, description="Optional focus topics")


class GenerateRequest(BaseModel):
    topic: str | None = Field(None, description="Topic for generation")
    custom_instructions: str | None = Field(
        None, description="Custom instructions for generation"
    )
    count: int | None = Field(
        None, description="Number of items to generate (for flashcards/quizzes)"
    )
    difficulty: str | None = Field(
        None, description="Difficulty level (for flashcards/quizzes)"
    )
