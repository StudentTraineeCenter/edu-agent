"""Queue message schemas for shared use across services."""

from enum import Enum
from typing import NotRequired, TypedDict, Union


class TaskType(str, Enum):
    """Task type enum for queue messages."""

    FLASHCARD_GENERATION = "flashcard_generation"
    QUIZ_GENERATION = "quiz_generation"
    NOTE_GENERATION = "note_generation"
    MIND_MAP_GENERATION = "mind_map_generation"
    DOCUMENT_PROCESSING = "document_processing"


class FlashcardGenerationData(TypedDict):
    """Data schema for flashcard generation tasks."""

    project_id: str
    group_id: str  # Required: existing flashcard group to populate
    topic: NotRequired[str]
    custom_instructions: NotRequired[str]
    user_id: NotRequired[str]
    count: NotRequired[int]
    difficulty: NotRequired[str]


class QuizGenerationData(TypedDict):
    """Data schema for quiz generation tasks."""

    project_id: str
    quiz_id: str  # Required: existing quiz to populate
    topic: NotRequired[str]
    custom_instructions: NotRequired[str]
    user_id: NotRequired[str]
    count: NotRequired[int]


class NoteGenerationData(TypedDict):
    """Data schema for note generation tasks."""

    project_id: str
    note_id: str  # Required: existing note to populate
    topic: NotRequired[str]
    custom_instructions: NotRequired[str]
    user_id: NotRequired[str]


class MindMapGenerationData(TypedDict):
    """Data schema for mind map generation tasks."""

    project_id: str
    user_id: str
    mind_map_id: NotRequired[str]  # Optional: existing mind map to populate (if not provided, creates new)
    topic: NotRequired[str]
    custom_instructions: NotRequired[str]


class DocumentProcessingData(TypedDict):
    """Data schema for document processing tasks."""

    document_id: str
    project_id: str
    user_id: str


TaskData = Union[
    FlashcardGenerationData,
    QuizGenerationData,
    NoteGenerationData,
    MindMapGenerationData,
    DocumentProcessingData,
]


class QueueTaskMessage(TypedDict):
    """Schema for queue task messages."""

    type: TaskType
    data: TaskData

