"""Service for importing flashcards and quizzes from CSV."""

import csv
import io
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict
from uuid import uuid4

from core.logger import get_logger
from db.models import Flashcard, FlashcardGroup, Quiz, QuizQuestion
from db.session import SessionLocal

logger = get_logger(__name__)


class ImporterService:
    """Service for importing study materials from CSV."""

    def import_flashcards_from_csv(
        self,
        project_id: str,
        csv_content: str,
        group_name: str,
        group_description: str | None = None
    ) -> str:
        """Import flashcards from CSV.

        CSV Format:
        question,answer,difficulty_level

        Args:
            project_id: Project ID
            csv_content: CSV content as string
            group_name: Name for the flashcard group
            group_description: Optional description

        Returns:
            ID of created flashcard group
        """
        with self._get_db_session() as db:
            # Parse CSV
            reader = csv.DictReader(io.StringIO(csv_content))

            flashcards_data = []
            for row in reader:
                flashcards_data.append({
                    "question": row.get("question", "").strip(),
                    "answer": row.get("answer", "").strip(),
                    "difficulty_level": row.get("difficulty_level", "medium").strip().lower()
                })

            if not flashcards_data:
                raise ValueError("No flashcards found in CSV")

            # Validate difficulty levels
            valid_difficulties = {"easy", "medium", "hard"}
            for data in flashcards_data:
                if data["difficulty_level"] not in valid_difficulties:
                    data["difficulty_level"] = "medium"

            # Create flashcard group
            group = FlashcardGroup(
                id=str(uuid4()),
                project_id=project_id,
                name=group_name,
                description=group_description,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(group)
            db.flush()

            # Create flashcards
            for data in flashcards_data:
                flashcard = Flashcard(
                    id=str(uuid4()),
                    group_id=group.id,
                    project_id=project_id,
                    question=data["question"],
                    answer=data["answer"],
                    difficulty_level=data["difficulty_level"],
                    created_at=datetime.now()
                )
                db.add(flashcard)

            db.commit()
            db.refresh(group)

            logger.info(f"imported {len(flashcards_data)} flashcards to group {group.id}")
            return str(group.id)

    def import_quiz_from_csv(
        self,
        project_id: str,
        csv_content: str,
        quiz_name: str,
        quiz_description: str | None = None
    ) -> str:
        """Import quiz from CSV.

        CSV Format:
        question_text,option_a,option_b,option_c,option_d,correct_option,explanation,difficulty_level

        Args:
            project_id: Project ID
            csv_content: CSV content as string
            quiz_name: Name for the quiz
            quiz_description: Optional description

        Returns:
            ID of created quiz
        """
        with self._get_db_session() as db:
            # Parse CSV
            reader = csv.DictReader(io.StringIO(csv_content))

            questions_data = []
            for row in reader:
                questions_data.append({
                    "question_text": row.get("question_text", "").strip(),
                    "option_a": row.get("option_a", "").strip(),
                    "option_b": row.get("option_b", "").strip(),
                    "option_c": row.get("option_c", "").strip(),
                    "option_d": row.get("option_d", "").strip(),
                    "correct_option": row.get("correct_option", "").strip().lower(),
                    "explanation": row.get("explanation", "").strip(),
                    "difficulty_level": row.get("difficulty_level", "medium").strip().lower()
                })

            if not questions_data:
                raise ValueError("No questions found in CSV")

            # Validate correct_option
            valid_options = {"a", "b", "c", "d"}
            for data in questions_data:
                if data["correct_option"] not in valid_options:
                    raise ValueError(f"Invalid correct_option: {data['correct_option']}")

            # Validate difficulty levels
            valid_difficulties = {"easy", "medium", "hard"}
            for data in questions_data:
                if data["difficulty_level"] not in valid_difficulties:
                    data["difficulty_level"] = "medium"

            # Create quiz
            quiz = Quiz(
                id=str(uuid4()),
                project_id=project_id,
                name=quiz_name,
                description=quiz_description,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(quiz)
            db.flush()

            # Create questions
            for data in questions_data:
                question = QuizQuestion(
                    id=str(uuid4()),
                    quiz_id=quiz.id,
                    project_id=project_id,
                    question_text=data["question_text"],
                    option_a=data["option_a"],
                    option_b=data["option_b"],
                    option_c=data["option_c"],
                    option_d=data["option_d"],
                    correct_option=data["correct_option"],
                    explanation=data["explanation"] or None,
                    difficulty_level=data["difficulty_level"],
                    created_at=datetime.now()
                )
                db.add(question)

            db.commit()
            db.refresh(quiz)

            logger.info(f"imported {len(questions_data)} questions to quiz {quiz.id}")
            return str(quiz.id)

    @contextmanager
    def _get_db_session(self):
        """Context manager for database sessions."""
        db = SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

