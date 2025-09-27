#!/usr/bin/env python3
"""
Seed script to insert default user and project data into the database.
Run this script to populate the database with initial data for development/testing.
"""

import sys
import os
from uuid import uuid4

# Add the server directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from db.session import SessionLocal, engine
from db.model import User, Project
from db.base import Base


def create_default_user(db: Session) -> User:
    """Create a default user if it doesn't exist."""
    # Check if default user already exists
    existing_user = db.query(User).filter(User.username == "admin").first()
    if existing_user:
        print("Default user 'admin' already exists")
        return existing_user

    # Create default user
    default_user = User(id=str(uuid4()), username="admin")

    db.add(default_user)
    db.commit()
    db.refresh(default_user)

    print(f"Created default user: {default_user.username} (ID: {default_user.id})")
    return default_user


def create_default_project(db: Session, user: User) -> Project:
    """Create a default project if it doesn't exist."""
    # Check if default project already exists
    existing_project = (
        db.query(Project)
        .filter(Project.name == "Default Project", Project.owner_id == user.id)
        .first()
    )

    if existing_project:
        print("Default project 'Default Project' already exists for this user")
        return existing_project

    # Create default project
    default_project = Project(
        id=str(uuid4()),
        owner_id=user.id,
        name="Default Project",
        description="A default project for testing and development purposes.",
    )

    db.add(default_project)
    db.commit()
    db.refresh(default_project)

    print(f"Created default project: {default_project.name} (ID: {default_project.id})")
    return default_project


def seed_database():
    """Main function to seed the database with default data."""
    print("Starting database seeding...")

    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    print("Database tables created/verified")

    # Create database session
    db = SessionLocal()

    try:
        # Create default user
        user = create_default_user(db)

        # Create default project for the user
        project = create_default_project(db, user)

        print("Database seeding completed successfully!")
        print(f"Default user: {user.username}")
        print(f"Default project: {project.name}")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
