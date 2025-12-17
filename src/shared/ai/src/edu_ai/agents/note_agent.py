from datetime import datetime
from typing import Any

from edu_core.exceptions import NotFoundError
from edu_db.models import Note, Project
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field

from edu_ai.agents.topic_graph_agent import TopicGraphAgent
from edu_ai.agents.utils import generate, get_db_session


class NoteGenerationResult(BaseModel):
    """Model for note generation result."""

    title: str = Field(..., description="The title of the note")
    description: str = Field(..., description="The description of the note")
    content: str = Field(..., description="The content of the note")


class NoteAgent:
    output_model = NoteGenerationResult
    prompt_template = "note_prompt"

    def __init__(
        self,
        search_service: Any,
        llm: AzureChatOpenAI,
        topic_graph_agent: TopicGraphAgent | None = None,
    ):
        self.search_service = search_service
        self.llm = llm
        self.topic_graph_agent = topic_graph_agent

    async def generate_and_save(
        self,
        project_id: str,
        topic: str | None = None,
        custom_instructions: str | None = None,
        note_id: str | None = None,
        **kwargs: Any,
    ) -> Note:
        """Generate note content and save to the database.

        Args:
            project_id: The project ID
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            note_id: The note ID to populate (required)

        Returns:
            Updated Note model

        Raises:
            NotFoundError: If note or project not found
            ValueError: If note_id is not provided
        """
        if not note_id:
            raise ValueError("note_id is required for note generation")

        with get_db_session() as db:
            # Find existing note
            note = (
                db.query(Note)
                .filter(
                    Note.id == note_id,
                    Note.project_id == project_id,
                )
                .first()
            )
            if not note:
                raise NotFoundError(f"Note {note_id} not found")

            # Get project language code
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise NotFoundError(f"Project {project_id} not found")
            language_code = project.language_code

            generation_topic = topic
            if self.topic_graph_agent:
                topic_graph = await self.topic_graph_agent.generate_topic_graph(
                    project_id=project_id,
                    topic=topic,
                    custom_instructions=custom_instructions,
                )
                if topic_graph.root_topics:
                    topics = []
                    for root_topic in topic_graph.root_topics:
                        topics.append(root_topic.topic)
                        for subtopic in root_topic.subtopics:
                            topics.append(subtopic.topic)
                    generation_topic = ", ".join(topics)

            # Generate note using AI
            result = await generate(
                llm=self.llm,
                search_service=self.search_service,
                output_model=self.output_model,
                prompt_template=self.prompt_template,
                project_id=project_id,
                topic=generation_topic or "",
                language_code=language_code,
                custom_instructions=custom_instructions,
            )

            # Update note with generated content
            note.title = result.title
            note.description = result.description
            note.content = result.content
            note.updated_at = datetime.now()

            db.flush()
            return note
