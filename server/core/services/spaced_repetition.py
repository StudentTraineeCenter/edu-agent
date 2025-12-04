"""Service for managing spaced repetition using SM-2 algorithm."""

import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from core.logger import get_logger
from db.models import Flashcard, FlashcardGroup, FlashcardSpacedRepetition
from db.session import SessionLocal

logger = get_logger(__name__)


class SpacedRepetitionService:
    """Service for managing spaced repetition using SM-2 algorithm."""

    def __init__(self):
        """Initialize the spaced repetition service."""
        pass

    def calculate_next_review(
        self,
        sr_state: FlashcardSpacedRepetition,
        quality: int  # 0-5 rating from user
    ) -> FlashcardSpacedRepetition:
        """Calculate next review date using SM-2 algorithm.

        SM-2 Algorithm:
        - Quality < 3: Reset (interval = 1 day, repetition = 0)
        - Quality >= 3: Update interval and ease factor

        Args:
            sr_state: Current spaced repetition state
            quality: User's quality rating (0-5)

        Returns:
            Updated FlashcardSpacedRepetition
        """
        if quality < 3:  # Incorrect or difficult
            sr_state.repetition_count = 0
            sr_state.interval_days = 1
        else:
            if sr_state.repetition_count == 0:
                sr_state.interval_days = 1
            elif sr_state.repetition_count == 1:
                sr_state.interval_days = 6
            else:
                sr_state.interval_days = int(sr_state.interval_days * sr_state.ease_factor)

            # Update ease factor
            # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
            sr_state.ease_factor = max(
                1.3,
                sr_state.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            )
            sr_state.repetition_count += 1

        # Update timestamps
        sr_state.last_reviewed_at = datetime.now()
        sr_state.next_review_at = datetime.now() + timedelta(days=sr_state.interval_days)

        return sr_state

    def get_or_create_sr_state(
        self,
        db: Session,
        user_id: str,
        flashcard_id: str,
        group_id: str,
        project_id: str
    ) -> FlashcardSpacedRepetition:
        """Get or create spaced repetition state for a flashcard.

        Args:
            db: Database session
            user_id: User ID
            flashcard_id: Flashcard ID
            group_id: Flashcard group ID
            project_id: Project ID

        Returns:
            FlashcardSpacedRepetition instance
        """
        sr_state = (
            db.query(FlashcardSpacedRepetition)
            .filter(
                FlashcardSpacedRepetition.user_id == user_id,
                FlashcardSpacedRepetition.flashcard_id == flashcard_id
            )
            .first()
        )

        if not sr_state:
            sr_state = FlashcardSpacedRepetition(
                id=str(uuid.uuid4()),
                user_id=user_id,
                flashcard_id=flashcard_id,
                group_id=group_id,
                project_id=project_id,
                ease_factor=2.5,
                interval_days=1,
                repetition_count=0
            )
            db.add(sr_state)
            db.commit()
            db.refresh(sr_state)

        return sr_state

    def get_due_flashcards(
        self,
        db: Session,
        user_id: str,
        group_id: str,
        limit: Optional[int] = None
    ) -> List[Flashcard]:
        """Get flashcards that are due for review.

        Args:
            db: Database session
            user_id: User ID
            group_id: Flashcard group ID
            limit: Optional limit on number of flashcards

        Returns:
            List of Flashcard instances due for review
        """
        # Check if group has spaced repetition enabled
        group = db.query(FlashcardGroup).filter(FlashcardGroup.id == group_id).first()
        if not group or not group.spaced_repetition_enabled:
            return []

        now = datetime.now()
        query = (
            db.query(Flashcard)
            .join(FlashcardSpacedRepetition, Flashcard.id == FlashcardSpacedRepetition.flashcard_id)
            .filter(
                FlashcardSpacedRepetition.user_id == user_id,
                FlashcardSpacedRepetition.group_id == group_id,
                FlashcardSpacedRepetition.next_review_at <= now
            )
            .order_by(FlashcardSpacedRepetition.next_review_at.asc())
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def update_after_practice(
        self,
        db: Session,
        user_id: str,
        flashcard_id: str,
        quality: int,
        was_correct: bool
    ) -> FlashcardSpacedRepetition:
        """Update spaced repetition state after user practices a flashcard.

        Args:
            db: Database session
            user_id: User ID
            flashcard_id: Flashcard ID
            quality: User's quality rating (0-5)
            was_correct: Whether the answer was correct

        Returns:
            Updated FlashcardSpacedRepetition
        """
        # Get flashcard to find group_id and project_id
        flashcard = db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()
        if not flashcard:
            raise ValueError(f"Flashcard {flashcard_id} not found")

        # Get or create SR state
        sr_state = self.get_or_create_sr_state(
            db=db,
            user_id=user_id,
            flashcard_id=flashcard_id,
            group_id=flashcard.group_id,
            project_id=flashcard.project_id
        )

        # Calculate next review
        sr_state = self.calculate_next_review(sr_state, quality)
        sr_state.updated_at = datetime.now()

        db.commit()
        db.refresh(sr_state)

        return sr_state

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

