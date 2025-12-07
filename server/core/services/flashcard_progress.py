"""Service for managing flashcard progress and mastery tracking."""

from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.logger import get_logger
from db.models import Flashcard, FlashcardProgress
from db.session import SessionLocal

logger = get_logger(__name__)


class FlashcardProgressService:
    """Service for managing flashcard progress and mastery tracking."""

    def __init__(self):
        """Initialize the flashcard progress service."""
        pass

    def get_or_create_progress(
        self,
        db: Session,
        user_id: str,
        flashcard_id: str,
        group_id: str,
        project_id: str,
    ) -> FlashcardProgress:
        """Get or create progress record for a flashcard.

        Args:
            db: Database session
            user_id: User ID
            flashcard_id: Flashcard ID
            group_id: Group ID
            project_id: Project ID

        Returns:
            FlashcardProgress instance
        """
        progress = (
            db.query(FlashcardProgress)
            .filter(
                and_(
                    FlashcardProgress.user_id == user_id,
                    FlashcardProgress.flashcard_id == flashcard_id,
                )
            )
            .first()
        )

        if not progress:
            progress = FlashcardProgress(
                user_id=user_id,
                flashcard_id=flashcard_id,
                group_id=group_id,
                project_id=project_id,
                correct_count=0,
                incorrect_count=0,
                current_streak=0,
                mastery_level=0,
                is_mastered=False,
            )
            db.add(progress)
            db.flush()

        return progress

    def record_answer(
        self,
        db: Session,
        user_id: str,
        flashcard_id: str,
        group_id: str,
        project_id: str,
        is_correct: bool,
    ) -> FlashcardProgress:
        """Record an answer and update progress.

        Args:
            db: Database session
            user_id: User ID
            flashcard_id: Flashcard ID
            group_id: Group ID
            project_id: Project ID
            is_correct: Whether the answer was correct

        Returns:
            Updated FlashcardProgress
        """
        progress = self.get_or_create_progress(
            db=db,
            user_id=user_id,
            flashcard_id=flashcard_id,
            group_id=group_id,
            project_id=project_id,
        )

        if is_correct:
            progress.correct_count += 1
            progress.current_streak += 1
            progress.last_result = True
        else:
            progress.incorrect_count += 1
            progress.current_streak = 0
            progress.last_result = False

        progress.last_practiced_at = datetime.now()
        self._update_mastery(progress)

        db.commit()
        db.refresh(progress)

        logger.info(
            f"updated progress for flashcard_id={flashcard_id}, user_id={user_id}, "
            f"is_correct={is_correct}, mastery_level={progress.mastery_level}, "
            f"is_mastered={progress.is_mastered}"
        )

        return progress

    def _update_mastery(self, progress: FlashcardProgress) -> None:
        """Update mastery level and is_mastered flag based on progress.

        Mastery rule:
        - is_mastered = True if current_streak >= 2 OR (correct_count >= 3 and accuracy >= 70%)
        - mastery_level: 0=unseen, 1=learning, 2=mastered

        Args:
            progress: FlashcardProgress instance to update
        """
        total = progress.correct_count + progress.incorrect_count
        accuracy = progress.correct_count / total if total > 0 else 0

        # Mastery conditions
        if progress.current_streak >= 2 or (
            progress.correct_count >= 3 and accuracy >= 0.7
        ):
            progress.mastery_level = 2
            progress.is_mastered = True
        elif total > 0:
            progress.mastery_level = 1
            progress.is_mastered = False
        else:
            progress.mastery_level = 0
            progress.is_mastered = False

    def get_unmastered_flashcards(
        self, db: Session, user_id: str, group_id: str, include_mastered: bool = False
    ) -> List[Flashcard]:
        """Get flashcards for study queue (un-mastered by default).

        Args:
            db: Database session
            user_id: User ID
            group_id: Group ID
            include_mastered: Whether to include mastered cards

        Returns:
            List of Flashcard instances
        """
        # Get all flashcards in the group
        all_flashcards = (
            db.query(Flashcard).filter(Flashcard.group_id == group_id).all()
        )

        if include_mastered:
            return all_flashcards

        # Get progress for all flashcards
        flashcard_ids = [f.id for f in all_flashcards]
        if not flashcard_ids:
            return []

        progress_records = (
            db.query(FlashcardProgress)
            .filter(
                and_(
                    FlashcardProgress.user_id == user_id,
                    FlashcardProgress.flashcard_id.in_(flashcard_ids),
                )
            )
            .all()
        )

        # Create a set of mastered flashcard IDs
        mastered_ids = {p.flashcard_id for p in progress_records if p.is_mastered}

        # Return un-mastered flashcards (those without progress or not mastered)
        unmastered = [f for f in all_flashcards if f.id not in mastered_ids]

        logger.info(
            f"found {len(unmastered)} unmastered flashcards out of {len(all_flashcards)} "
            f"for user_id={user_id}, group_id={group_id}"
        )

        return unmastered

    def get_progress_summary(self, db: Session, user_id: str, group_id: str) -> dict:
        """Get progress summary for a flashcard group.

        Args:
            db: Database session
            user_id: User ID
            group_id: Group ID

        Returns:
            Dictionary with summary stats
        """
        all_flashcards = (
            db.query(Flashcard).filter(Flashcard.group_id == group_id).all()
        )

        flashcard_ids = [f.id for f in all_flashcards]
        if not flashcard_ids:
            return {"total": 0, "mastered": 0, "unmastered": 0}

        progress_records = (
            db.query(FlashcardProgress)
            .filter(
                and_(
                    FlashcardProgress.user_id == user_id,
                    FlashcardProgress.flashcard_id.in_(flashcard_ids),
                )
            )
            .all()
        )

        mastered_count = sum(1 for p in progress_records if p.is_mastered)
        unmastered_count = len(all_flashcards) - mastered_count

        return {
            "total": len(all_flashcards),
            "mastered": mastered_count,
            "unmastered": unmastered_count,
        }

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
