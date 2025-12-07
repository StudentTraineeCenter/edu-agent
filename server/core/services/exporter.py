"""Service for exporting flashcards and quizzes to CSV."""

import csv
import io
from contextlib import contextmanager
from typing import List

from core.logger import get_logger
from db.models import Flashcard, FlashcardGroup, Quiz, QuizQuestion
from db.session import SessionLocal

logger = get_logger(__name__)


class ExporterService:
    """Service for exporting study materials to CSV."""

    def export_flashcard_group_to_csv(self, group_id: str) -> str:
        """Export a flashcard group to CSV.

        CSV Format:
        question,answer,difficulty_level

        Args:
            group_id: Flashcard group ID

        Returns:
            CSV content as string
        """
        with self._get_db_session() as db:
            group = (
                db.query(FlashcardGroup).filter(FlashcardGroup.id == group_id).first()
            )

            if not group:
                raise ValueError(f"Flashcard group {group_id} not found")

            flashcards = (
                db.query(Flashcard)
                .filter(Flashcard.group_id == group_id)
                .order_by(Flashcard.created_at.asc())
                .all()
            )

            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(["question", "answer", "difficulty_level"])

            # Write flashcards
            for flashcard in flashcards:
                writer.writerow(
                    [flashcard.question, flashcard.answer, flashcard.difficulty_level]
                )

            return output.getvalue()

    def export_quiz_to_csv(self, quiz_id: str) -> str:
        """Export a quiz to CSV.

        CSV Format:
        question_text,option_a,option_b,option_c,option_d,correct_option,explanation,difficulty_level

        Args:
            quiz_id: Quiz ID

        Returns:
            CSV content as string
        """
        with self._get_db_session() as db:
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()

            if not quiz:
                raise ValueError(f"Quiz {quiz_id} not found")

            questions = (
                db.query(QuizQuestion)
                .filter(QuizQuestion.quiz_id == quiz_id)
                .order_by(QuizQuestion.created_at.asc())
                .all()
            )

            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(
                [
                    "question_text",
                    "option_a",
                    "option_b",
                    "option_c",
                    "option_d",
                    "correct_option",
                    "explanation",
                    "difficulty_level",
                ]
            )

            # Write questions
            for question in questions:
                writer.writerow(
                    [
                        question.question_text,
                        question.option_a,
                        question.option_b,
                        question.option_c,
                        question.option_d,
                        question.correct_option,
                        question.explanation or "",
                        question.difficulty_level,
                    ]
                )

            return output.getvalue()

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
