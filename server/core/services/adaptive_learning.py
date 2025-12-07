"""Service for adaptive learning - generates personalized study sessions."""

import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from core.logger import get_logger
from core.services.practice import PracticeService
from db.models import (
    Flashcard,
    FlashcardGroup,
    PracticeRecord,
    Quiz,
    QuizQuestion,
    StudySession,
)
from uuid import uuid4
from db.session import SessionLocal

logger = get_logger(__name__)


class AdaptiveLearningService:
    """Service for generating adaptive learning sessions."""

    def __init__(self, practice_service: PracticeService):
        """Initialize adaptive learning service.

        Args:
            practice_service: Service for accessing practice records
        """
        self.practice_service = practice_service

    async def generate_study_session(
        self,
        user_id: str,
        project_id: str,
        session_length_minutes: int = 30,
        focus_topics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate an adaptive study session.

        Prioritizes:
        1. Flashcards due for review (spaced repetition)
        2. Weak topics (low accuracy)
        3. Optimal difficulty progression
        4. User's historical performance patterns

        Args:
            user_id: User ID
            project_id: Project ID
            session_length_minutes: Desired session length
            focus_topics: Optional list of topics to focus on

        Returns:
            Dictionary with session details
        """
        with self._get_db_session() as db:
            # Get practice records for analysis
            practice_records = self.practice_service.get_user_practice_records(
                user_id=user_id, project_id=project_id
            )

            # Analyze performance
            topic_analysis = self._analyze_topics(practice_records)

            # Get available resources
            flashcard_groups = (
                db.query(FlashcardGroup)
                .filter(FlashcardGroup.project_id == project_id)
                .all()
            )

            quizzes = db.query(Quiz).filter(Quiz.project_id == project_id).all()

            # Prioritize flashcards
            prioritized_flashcards = []

            # 1. Weak topics
            weak_topics = [
                topic
                for topic, stats in topic_analysis.items()
                if stats["accuracy"] < 70
            ]

            if weak_topics:
                for group in flashcard_groups:
                    flashcards = (
                        db.query(Flashcard).filter(Flashcard.group_id == group.id).all()
                    )

                    for flashcard in flashcards:
                        # Simple topic matching (could be improved with NLP)
                        if any(
                            topic.lower() in flashcard.question.lower()
                            for topic in weak_topics
                        ):
                            if not any(
                                f["flashcard_id"] == flashcard.id
                                for f in prioritized_flashcards
                            ):
                                prioritized_flashcards.append(
                                    {
                                        "flashcard_id": flashcard.id,
                                        "group_id": group.id,
                                        "priority": "medium",
                                        "reason": "weak_topic",
                                    }
                                )

            # 2. Fill remaining slots with new/unpracticed items
            practiced_flashcard_ids = {
                pr.item_id for pr in practice_records if pr.item_type == "flashcard"
            }

            for group in flashcard_groups:
                if len(prioritized_flashcards) >= 30:  # Limit session size
                    break

                flashcards = (
                    db.query(Flashcard).filter(Flashcard.group_id == group.id).all()
                )

                for flashcard in flashcards:
                    if flashcard.id not in practiced_flashcard_ids:
                        if not any(
                            f["flashcard_id"] == flashcard.id
                            for f in prioritized_flashcards
                        ):
                            prioritized_flashcards.append(
                                {
                                    "flashcard_id": flashcard.id,
                                    "group_id": group.id,
                                    "priority": "low",
                                    "reason": "new_item",
                                }
                            )

            # Estimate time (assume 1 minute per flashcard)
            estimated_minutes = len(prioritized_flashcards)
            final_flashcards = prioritized_flashcards[
                :session_length_minutes
            ]  # Limit to session length
            focus_topics_list = weak_topics[:5] if weak_topics else []
            learning_objectives = self._generate_learning_objectives(topic_analysis)

            # Create and save study session
            session = StudySession(
                user_id=user_id,
                project_id=project_id,
                session_data={
                    "flashcards": final_flashcards,
                    "learning_objectives": learning_objectives,
                },
                estimated_time_minutes=min(estimated_minutes, session_length_minutes),
                session_length_minutes=session_length_minutes,
                focus_topics=focus_topics_list if focus_topics_list else None,
            )
            db.add(session)
            db.flush()  # Flush to get session.id

            # Create a flashcard group for this study session with only the selected flashcards
            session_group = FlashcardGroup(
                id=str(uuid4()),
                project_id=project_id,
                name=f"Study Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                description="Personalized study session based on your performance",
                study_session_id=session.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(session_group)
            db.flush()

            # Copy selected flashcards to the new group
            flashcard_ids_to_copy = [f["flashcard_id"] for f in final_flashcards]
            original_flashcards = (
                db.query(Flashcard)
                .filter(Flashcard.id.in_(flashcard_ids_to_copy))
                .all()
            )

            for original_flashcard in original_flashcards:
                # Create a copy of the flashcard in the session group
                new_flashcard = Flashcard(
                    id=str(uuid4()),
                    group_id=session_group.id,
                    project_id=project_id,
                    question=original_flashcard.question,
                    answer=original_flashcard.answer,
                    difficulty_level=original_flashcard.difficulty_level,
                    created_at=datetime.now(),
                )
                db.add(new_flashcard)

            db.commit()
            db.refresh(session)
            db.refresh(session_group)

            return {
                "session_id": session.id,
                "flashcard_group_id": session_group.id,
                "flashcards": final_flashcards,
                "estimated_time_minutes": min(
                    estimated_minutes, session_length_minutes
                ),
                "focus_topics": focus_topics_list,
                "learning_objectives": learning_objectives,
                "generated_at": session.generated_at.isoformat(),
            }

    def _analyze_topics(
        self, practice_records: List[PracticeRecord]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze practice records by topic.

        Returns:
            Dictionary mapping topics to statistics
        """
        topic_stats = {}

        for record in practice_records:
            topic = record.topic
            if topic not in topic_stats:
                topic_stats[topic] = {"total": 0, "correct": 0, "accuracy": 0.0}

            topic_stats[topic]["total"] += 1
            if record.was_correct:
                topic_stats[topic]["correct"] += 1

        # Calculate accuracy
        for topic, stats in topic_stats.items():
            if stats["total"] > 0:
                stats["accuracy"] = (stats["correct"] / stats["total"]) * 100

        return topic_stats

    def _generate_learning_objectives(
        self, topic_analysis: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate learning objectives based on topic analysis."""
        weak_topics = [
            topic
            for topic, stats in topic_analysis.items()
            if stats["accuracy"] < 70 and stats["total"] >= 3
        ]

        objectives = []
        if weak_topics:
            objectives.append(f"Improve understanding of: {', '.join(weak_topics[:3])}")

        strong_topics = [
            topic
            for topic, stats in topic_analysis.items()
            if stats["accuracy"] >= 90 and stats["total"] >= 5
        ]

        if strong_topics:
            objectives.append(f"Maintain mastery of: {', '.join(strong_topics[:2])}")

        return objectives

    def get_study_session(
        self, session_id: str, user_id: str
    ) -> Optional[StudySession]:
        """Get a study session by ID.

        Args:
            session_id: Study session ID
            user_id: User ID (for authorization)

        Returns:
            StudySession model or None if not found
        """
        with self._get_db_session() as db:
            session = (
                db.query(StudySession)
                .filter(StudySession.id == session_id, StudySession.user_id == user_id)
                .first()
            )
            return session

    def get_study_session_with_group(
        self, session_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a study session with its associated flashcard group ID.

        Args:
            session_id: Study session ID
            user_id: User ID (for authorization)

        Returns:
            Dictionary with session and flashcard_group_id, or None if not found
        """
        with self._get_db_session() as db:
            session = (
                db.query(StudySession)
                .filter(StudySession.id == session_id, StudySession.user_id == user_id)
                .first()
            )
            if not session:
                return None

            # Find the associated flashcard group
            group = (
                db.query(FlashcardGroup)
                .filter(FlashcardGroup.study_session_id == session_id)
                .first()
            )

            return {
                "session": session,
                "flashcard_group_id": group.id if group else None,
            }

    def list_study_sessions(
        self, user_id: str, project_id: str, limit: int = 50
    ) -> List[StudySession]:
        """List study sessions for a project.

        Args:
            user_id: User ID (for authorization)
            project_id: Project ID
            limit: Maximum number of sessions to return

        Returns:
            List of StudySession models, ordered by most recent first
        """
        with self._get_db_session() as db:
            sessions = (
                db.query(StudySession)
                .filter(
                    StudySession.user_id == user_id,
                    StudySession.project_id == project_id,
                )
                .order_by(StudySession.generated_at.desc())
                .limit(limit)
                .all()
            )
            return sessions

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
