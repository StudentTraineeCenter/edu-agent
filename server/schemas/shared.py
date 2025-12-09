"""Shared schemas - enums and constants used across multiple features."""

from enum import Enum

# ============================================================================
# String Enums
# ============================================================================


class DifficultyLevel(str, Enum):
    """Difficulty level enum."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class LengthPreference(str, Enum):
    """Length preference enum."""

    LESS = "less"
    NORMAL = "normal"
    MORE = "more"


class GenerationStatus(str, Enum):
    """Generation progress status enum."""

    SEARCHING = "searching"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    STRUCTURING = "structuring"
    WRITING = "writing"
    MAPPING = "mapping"
    BUILDING = "building"
    THINKING = "thinking"
    DONE = "done"


class UsageType(str, Enum):
    """Usage type enum."""

    CHAT_MESSAGE = "chat_message"
    FLASHCARD_GENERATION = "flashcard_generation"
    QUIZ_GENERATION = "quiz_generation"
    DOCUMENT_UPLOAD = "document_upload"


class StudyResourceType(str, Enum):
    """Study resource type enum."""

    FLASHCARD = "flashcard"
    QUIZ = "quiz"


class CorrectOption(str, Enum):
    """Correct option enum for quiz questions."""

    A = "a"
    B = "b"
    C = "c"
    D = "d"


# ============================================================================
# Constants
# ============================================================================

# Default API version for Azure Content Understanding
DEFAULT_API_VERSION = "2025-05-01-preview"

# Default timeout in seconds
DEFAULT_TIMEOUT_SECONDS = 30
