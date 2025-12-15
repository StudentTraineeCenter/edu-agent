"""Processors for handling queue tasks."""

from processors.base import BaseProcessor
from processors.chat_title import ChatTitleProcessor
from processors.document import DocumentProcessor
from processors.flashcard import FlashcardProcessor
from processors.mind_map import MindMapProcessor
from processors.note import NoteProcessor
from processors.quiz import QuizProcessor

__all__ = [
    "BaseProcessor",
    "ChatTitleProcessor",
    "DocumentProcessor",
    "FlashcardProcessor",
    "MindMapProcessor",
    "NoteProcessor",
    "QuizProcessor",
]
