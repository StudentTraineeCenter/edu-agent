from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from db.base import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    projects = relationship("Project", back_populates="owner")
    documents = relationship("Document", back_populates="owner")
    chats = relationship("Chat", back_populates="user")


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    language_code: Mapped[str] = mapped_column(String, default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner = relationship("User", back_populates="projects")
    documents = relationship("Document", back_populates="project")
    chats = relationship("Chat", back_populates="project")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id"), nullable=True
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

    # Document processing metadata
    status: Mapped[str] = mapped_column(
        String, default="uploaded"
    )  # uploaded, processing, processed, failed, indexed

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
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"))

    # Segment ordering and structure
    segment_order: Mapped[int] = mapped_column(Integer)

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


class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))

    # Chat metadata
    title: Mapped[str] = mapped_column(
        String, nullable=True
    )  # Auto-generated or user-set title

    # Messages stored as JSON array
    messages: Mapped[list[dict]] = mapped_column(JSON, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project = relationship("Project", back_populates="chats")
    user = relationship("User", back_populates="chats")


class FlashcardGroup(Base):
    __tablename__ = "flashcard_groups"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
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
    flashcards = relationship(
        "Flashcard", back_populates="group", cascade="all, delete-orphan"
    )


class Flashcard(Base):
    __tablename__ = "flashcards"
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    group_id: Mapped[str] = mapped_column(String, ForeignKey("flashcard_groups.id"))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))

    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    difficulty_level: Mapped[str] = mapped_column(
        String, default="medium"
    )  # easy, medium, hard

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
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))

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
    quiz_id: Mapped[str] = mapped_column(String, ForeignKey("quizzes.id"))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))

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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    project = relationship("Project")
