# Projects

Projects are the top-level organizational unit for all educational content.

## Features

- **Create Projects**: Set up a new learning project with name, description, and language
- **List Projects**: View all projects owned by the user
- **Get Project**: Retrieve project details
- **Update Project**: Modify project name, description, or language code
- **Delete Project**: Remove a project and all associated content

## Project Properties

- `id`: Unique identifier
- `owner_id`: User who owns the project
- `name`: Project name (must be unique per user)
- `description`: Optional project description
- `language_code`: Language for AI-generated content (default: `"en"`)
- `created_at`: Timestamp when project was created

## Language Support

Projects support different languages through the `language_code` field. When generating quizzes, flashcards, or chat responses, the AI will use the project's language code to ensure content is generated in the appropriate language.
