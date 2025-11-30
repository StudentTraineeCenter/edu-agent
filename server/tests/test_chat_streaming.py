#!/usr/bin/env python3
"""Test script for ChatService streaming response.

This script loads all configs and tests the chat service streaming functionality
without starting the full server. It logs all chunks to the console.
"""

import argparse
import asyncio
import sys
from uuid import uuid4

# Import config first to load environment variables
from core.config import app_config
from core.logger import get_logger
from core.agents.search import DocumentSearchAdapter
from core.services.chat import ChatService
from core.services.documents import DocumentService
from core.services.projects import ProjectService
from core.services.usage import UsageService
from db.models import User, Project
from db.session import SessionLocal

logger = get_logger(__name__)


def print_config_summary():
    """Print a summary of loaded configuration."""
    logger.info("=" * 60)
    logger.info("Configuration Summary")
    logger.info("=" * 60)
    logger.info(f"Database URL: {app_config.DATABASE_URL[:50]}...")
    logger.info(f"Azure OpenAI Endpoint: {app_config.AZURE_OPENAI_ENDPOINT}")
    logger.info(
        f"Azure OpenAI Chat Deployment: {app_config.AZURE_OPENAI_CHAT_DEPLOYMENT}"
    )
    logger.info(f"Azure Storage Input Container: {app_config.AZURE_STORAGE_INPUT_CONTAINER_NAME}")
    logger.info(f"Azure Storage Output Container: {app_config.AZURE_STORAGE_OUTPUT_CONTAINER_NAME}")
    logger.info("=" * 60)


def get_user_by_id(user_id: str) -> User:
    """Get a user by ID."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        logger.info(f"Using existing user: {user.id} ({user.email or 'no email'})")
        return user
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise
    finally:
        db.close()


def get_or_create_test_user() -> User:
    """Get or create a test user for testing."""
    db = SessionLocal()
    try:
        # Try to find an existing test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if test_user:
            logger.info(f"Using existing test user: {test_user.id}")
            return test_user

        # Create a new test user
        test_user = User(
            id=str(uuid4()),
            email="test@example.com",
            name="Test User",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        logger.info(f"Created new test user: {test_user.id}")
        return test_user
    except Exception as e:
        logger.error(f"Error getting/creating test user: {e}")
        raise
    finally:
        db.close()


def get_project_by_id(project_id: str, user_id: str) -> str:
    """Get a project by ID and verify ownership."""
    db = SessionLocal()
    try:
        project = (
            db.query(Project)
            .filter(
                Project.id == project_id,
                Project.owner_id == user_id,
            )
            .first()
        )
        if not project:
            raise ValueError(
                f"Project {project_id} not found or not owned by user {user_id}"
            )
        logger.info(f"Using existing project: {project.id} ({project.name})")
        return project.id
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise
    finally:
        db.close()


def get_or_create_test_project(project_service: ProjectService, user_id: str) -> str:
    """Get or create a test project for testing."""
    db = SessionLocal()
    try:
        # Try to find an existing test project
        test_project = (
            db.query(Project)
            .filter(
                Project.owner_id == user_id,
                Project.name == "Test Project",
            )
            .first()
        )

        if test_project:
            logger.info(f"Using existing test project: {test_project.id}")
            return test_project.id

        # Create a new test project
        test_project = project_service.create_project(
            owner_id=user_id,
            name="Test Project",
            description="Test project for streaming chat",
            language_code="en",
        )
        logger.info(f"Created new test project: {test_project.id}")
        return test_project.id
    except Exception as e:
        logger.error(f"Error getting/creating test project: {e}")
        raise
    finally:
        db.close()


async def test_streaming_response(
    chat_service: ChatService, chat_id: str, user_id: str, message: str
):
    """Test the streaming response from chat service."""
    logger.info("=" * 60)
    logger.info("Starting Streaming Test")
    logger.info("=" * 60)
    logger.info(f"Chat ID: {chat_id}")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Message: {message}")
    logger.info("=" * 60)
    logger.info("")

    chunk_count = 0
    total_chars = 0
    sources_count = 0
    tools_count = 0

    try:
        async for chunk in chat_service.send_streaming_message(
            chat_id, user_id, message
        ):
            chunk_count += 1

            # Log chunk details
            if chunk.chunk:
                total_chars += len(chunk.chunk)
                logger.info(f"[CHUNK {chunk_count}] Content: {repr(chunk.chunk[:100])}")

            if chunk.sources:
                sources_count = len(chunk.sources)
                logger.info(
                    f"[CHUNK {chunk_count}] Sources: {sources_count} sources found"
                )
                for i, source in enumerate(chunk.sources):
                    logger.info(f"  Source {i + 1}: {source.title} (id: {source.id})")

            if chunk.tools:
                tools_count = len(chunk.tools)
                logger.info(f"[CHUNK {chunk_count}] Tools: {tools_count} tool calls")
                for i, tool in enumerate(chunk.tools):
                    logger.info(f"  Tool {i + 1}: {tool.name} (state: {tool.state})")

            if chunk.done:
                logger.info("")
                logger.info("=" * 60)
                logger.info("Streaming Complete")
                logger.info("=" * 60)
                logger.info(f"Total chunks received: {chunk_count}")
                logger.info(f"Total characters: {total_chars}")
                logger.info(f"Total sources: {sources_count}")
                logger.info(f"Total tool calls: {tools_count}")
                if chunk.response:
                    logger.info(
                        f"Final response length: {len(chunk.response)} characters"
                    )
                    logger.info(f"Final response preview: {chunk.response[:200]}...")
                logger.info("=" * 60)
                break

            # Small delay to make output readable
            await asyncio.sleep(0.01)

    except Exception as e:
        logger.error(f"Error during streaming: {e}", exc_info=True)
        raise


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test ChatService streaming response",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default test user and project
  python test_chat_streaming.py

  # Use existing user and project IDs
  python test_chat_streaming.py --user-id abc123 --project-id xyz789

  # Use existing IDs with custom message
  python test_chat_streaming.py --user-id abc123 --project-id xyz789 --message "What is machine learning?"
        """,
    )
    parser.add_argument(
        "--user-id",
        type=str,
        help="Use existing user ID (if not provided, creates/uses test user)",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        help="Use existing project ID (if not provided, creates/uses test project)",
    )
    parser.add_argument(
        "--message",
        type=str,
        default="Hello! Can you tell me about the documents in this project?",
        help="Test message to send (default: 'Hello! Can you tell me about the documents in this project?')",
    )

    args = parser.parse_args()

    logger.info("Initializing Chat Service Streaming Test")
    logger.info("")

    # Print config summary
    print_config_summary()
    logger.info("")

    # Initialize services (same as dependencies.py)
    logger.info("Initializing services...")
    document_service = DocumentService()
    search_interface = DocumentSearchAdapter(document_service)
    usage_service = UsageService()
    chat_service = ChatService(
        search_interface=search_interface, usage_service=usage_service
    )
    project_service = ProjectService()
    logger.info("Services initialized successfully")
    logger.info("")

    # Get or create test user
    logger.info("Setting up test user and project...")
    if args.user_id:
        test_user = get_user_by_id(args.user_id)
    else:
        test_user = get_or_create_test_user()

    if args.project_id:
        project_id = get_project_by_id(args.project_id, test_user.id)
    else:
        project_id = get_or_create_test_project(project_service, test_user.id)
    logger.info("")

    # Create a test chat
    logger.info("Creating test chat...")
    test_chat = chat_service.create_chat(
        project_id=project_id, user_id=test_user.id, title=None
    )
    logger.info(f"Created chat: {test_chat.id}")
    logger.info("")

    # Test message
    test_message = args.message

    # Run the streaming test
    await test_streaming_response(
        chat_service=chat_service,
        chat_id=test_chat.id,
        user_id=test_user.id,
        message=test_message,
    )

    logger.info("")
    logger.info("Test completed successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
