"""Queue message schemas for shared use across services."""

from enum import Enum
from typing import NotRequired, TypedDict, Union


class TaskType(str, Enum):
    """Task type enum for queue messages."""

    FLASHCARD_GENERATION = "flashcard_generation"
    QUIZ_GENERATION = "quiz_generation"
    NOTE_GENERATION = "note_generation"
    DOCUMENT_PROCESSING = "document_processing"


class FlashcardGenerationData(TypedDict):
    """Data schema for flashcard generation tasks."""

    project_id: str
    topic: NotRequired[str]
    custom_instructions: NotRequired[str]
    group_id: NotRequired[str]
    user_id: NotRequired[str]


class QuizGenerationData(TypedDict):
    """Data schema for quiz generation tasks."""

    project_id: str
    topic: NotRequired[str]
    custom_instructions: NotRequired[str]
    group_id: NotRequired[str]
    user_id: NotRequired[str]


class NoteGenerationData(TypedDict):
    """Data schema for note generation tasks."""

    project_id: str
    topic: NotRequired[str]
    custom_instructions: NotRequired[str]
    user_id: NotRequired[str]


class DocumentProcessingData(TypedDict):
    """Data schema for document processing tasks."""

    document_id: str
    project_id: str
    user_id: str


TaskData = Union[
    FlashcardGenerationData,
    QuizGenerationData,
    NoteGenerationData,
    DocumentProcessingData,
]


class QueueTaskMessage(TypedDict):
    """Schema for queue task messages."""

    type: TaskType
    data: TaskData

