from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.base import Base
from db.enums import DocumentStatus


class User(Base):
    __tablename__ = "users"
    # Use Supabase user ID as primary key to sync with auth.users
    id: Mapped[str] = mapped_column(
        String, primary_key=True
    )  # Maps to auth.users.id (UUID from Supabase)
    name: Mapped[str] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    projects = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document", back_populates="owner", cascade="all, delete-orphan"
    )
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    usage = relationship(
        "UserUsage", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    language_code: Mapped[str] = mapped_column(String, default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    owner = relationship("User", back_populates="projects")
    documents = relationship(
        "Document", back_populates="project", cascade="all, delete-orphan"
    )
    chats = relationship("Chat", back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE")
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )

    # File information
    file_name: Mapped[str] = mapped_column(String)  # Original file name
    file_type: Mapped[str] = mapped_column(String)  # pdf, docx, txt, etc.
    file_size: Mapped[int] = mapped_column(Integer)  # Size in bytes

    # Azure Blob Storage references
    original_blob_name: Mapped[str] = mapped_column(
        String, unique=True, nullable=True, index=True
    )
    processed_text_blob_name: Mapped[str] = mapped_column(
        String, unique=True, nullable=True, index=True
    )

    # Document metadata
    summary: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # Auto-generated summary of the document

    # Document processing metadata
    status: Mapped[DocumentStatus] = mapped_column(
        String, default=DocumentStatus.UPLOADED
    )

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    owner = relationship("User", back_populates="documents")
    project = relationship("Project", back_populates="documents")
    segments = relationship(
        "DocumentSegment", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentSegment(Base):
    __tablename__ = "document_segments"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String, ForeignKey("documents.id", ondelete="CASCADE")
    )

    # Content
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String, default="text")

    # Metadata for RAG
    embedding_vector: Mapped[list] = mapped_column(Vector(3072), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    document = relationship("Document", back_populates="segments")


class ChatMessageSource(BaseModel):
    id: str
    citation_index: int
    content: str
    title: str
    document_id: str
    preview_url: str | None = None
    score: float | None = None


class ChatMessageToolCall(BaseModel):
    id: str
    type: str
    name: str
    state: Literal[
        "input-streaming", "input-available", "output-available", "output-error"
    ]
    input: dict | None = None
    output: dict | str | None = None
    error_text: str | None = None


class ChatMessage(BaseModel):
    id: str
    role: Literal["user", "assistant", "internal"]
    content: str
    sources: list[ChatMessageSource] | None = None
    tools: list[ChatMessageToolCall] | None = None
    created_at: datetime


class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE")
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE")
    )

    # Chat metadata
    title: Mapped[str] = mapped_column(
        String, nullable=True
    )  # Auto-generated or user-set title

    # Messages stored as JSON array
    messages: Mapped[list[ChatMessage]] = mapped_column(JSON, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project = relationship("Project", back_populates="chats")
    user = relationship("User", back_populates="chats")


class FlashcardGroup(Base):
    __tablename__ = "flashcard_groups"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    study_session_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("study_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )  # If set, this group belongs to a study session and should be hidden from regular lists

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project = relationship("Project")
    flashcards = relationship(
        "Flashcard", back_populates="group", cascade="all, delete-orphan"
    )


class Flashcard(Base):
    __tablename__ = "flashcards"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    group_id: Mapped[str] = mapped_column(
        String, ForeignKey("flashcard_groups.id", ondelete="CASCADE")
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE")
    )

    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    difficulty_level: Mapped[str] = mapped_column(
        String, default="medium"
    )  # easy, medium, hard
    position: Mapped[int] = mapped_column(
        Integer, default=0, index=True
    )  # Position for ordering within group

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    group = relationship("FlashcardGroup", back_populates="flashcards")
    project = relationship("Project")


class Quiz(Base):
    __tablename__ = "quizzes"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE")
    )

    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project = relationship("Project")
    questions = relationship(
        "QuizQuestion", back_populates="quiz", cascade="all, delete-orphan"
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    quiz_id: Mapped[str] = mapped_column(
        String, ForeignKey("quizzes.id", ondelete="CASCADE")
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE")
    )

    question_text: Mapped[str] = mapped_column(Text)
    option_a: Mapped[str] = mapped_column(Text)
    option_b: Mapped[str] = mapped_column(Text)
    option_c: Mapped[str] = mapped_column(Text)
    option_d: Mapped[str] = mapped_column(Text)
    correct_option: Mapped[str] = mapped_column(String)  # a, b, c, d
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[str] = mapped_column(
        String, default="medium"
    )  # easy, medium, hard
    position: Mapped[int] = mapped_column(
        Integer, default=0, index=True
    )  # Position for ordering within quiz

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    project = relationship("Project")


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text)  # Markdown content

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project = relationship("Project")


class PracticeRecord(Base):
    __tablename__ = "practice_records"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    item_type: Mapped[str] = mapped_column(
        String, index=True
    )  # "flashcard" or "quiz" - type of study resource
    item_id: Mapped[str] = mapped_column(
        String, index=True
    )  # flashcard_id or quiz_question_id - ID of the study resource
    topic: Mapped[str] = mapped_column(Text)  # Extracted from question/flashcard text
    user_answer: Mapped[str] = mapped_column(
        String, nullable=True
    )  # Only for quizzes, what user selected; null for flashcards
    correct_answer: Mapped[str] = mapped_column(
        Text
    )  # The correct answer - for flashcards this is the answer field, for quizzes the correct option
    was_correct: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # Whether the user got it right

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user = relationship("User")
    project = relationship("Project")


class MindMap(Base):
    __tablename__ = "mind_maps"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    # Map content
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    map_data: Mapped[dict] = mapped_column(
        JSON
    )  # Structured mind map data (nodes, edges)

    # Timestamps
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User")
    project = relationship("Project")


class FlashcardProgress(Base):
    __tablename__ = "flashcard_progress"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    flashcard_id: Mapped[str] = mapped_column(
        String, ForeignKey("flashcards.id", ondelete="CASCADE"), index=True
    )
    group_id: Mapped[str] = mapped_column(
        String, ForeignKey("flashcard_groups.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    # Simple mastery tracking
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    incorrect_count: Mapped[int] = mapped_column(Integer, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    mastery_level: Mapped[int] = mapped_column(
        Integer, default=0
    )  # 0=unseen, 1=learning, 2=mastered
    is_mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    last_result: Mapped[bool] = mapped_column(Boolean, nullable=True)
    last_practiced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User")
    flashcard = relationship("Flashcard")
    group = relationship("FlashcardGroup")
    project = relationship("Project")


class StudySession(Base):
    __tablename__ = "study_sessions"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    # Session metadata
    session_data: Mapped[dict] = mapped_column(
        JSON
    )  # Contains flashcards, focus_topics, learning_objectives
    estimated_time_minutes: Mapped[int] = mapped_column(Integer)
    session_length_minutes: Mapped[int] = mapped_column(Integer)  # Requested length
    focus_topics: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )  # Optional focus topics

    # Timestamps
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User")
    project = relationship("Project")


class UserUsage(Base):
    __tablename__ = "user_usage"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), index=True, unique=True
    )

    # Daily usage counters (reset daily)
    chat_messages_today: Mapped[int] = mapped_column(Integer, default=0)
    flashcard_generations_today: Mapped[int] = mapped_column(Integer, default=0)
    quiz_generations_today: Mapped[int] = mapped_column(Integer, default=0)
    document_uploads_today: Mapped[int] = mapped_column(Integer, default=0)

    # Last reset date
    last_reset_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User")
