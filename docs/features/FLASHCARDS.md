# Flashcards

Flashcards are AI-generated study cards created from project documents.

## Flashcard Generation

### Process

1. User requests flashcard creation (via API or chat).
2. System searches project documents for relevant content.
3. AI analyzes document content.
4. AI generates flashcard group name, description, and flashcards.
5. Flashcards are saved to the database.

### Generation Parameters

- `topic`: Topic to focus flashcard generation on (e.g., `"key formulas for exam"`, `"nitrogen cycle"`).
- `custom_instructions`: Free-form instructions for card style/format/difficulty (e.g., `"short Q/A"`, `"focus on definitions"`, `"hard recall questions only"`).
- `count`: Number of flashcards to generate (typically 15–30).
- `difficulty`: Target difficulty (`easy`, `medium`, `hard`) – used as a hint, not a hard constraint.
- `project_id`: Project containing source documents.

## Flashcard Structure

Flashcards are organized into groups. Each group contains:

- **Name**: Auto-generated concise title (2–6 words).
- **Description**: Brief explanation of flashcard content (1–2 sentences).
- **Flashcards**: Individual cards with:
  - Question.
  - Answer.
  - Difficulty level (`easy`, `medium`, `hard`).

## Flashcard Features

- **Create Flashcard Group**: Generate a new group with flashcards.
- **List Groups**: View all flashcard groups in a project.
- **Get Group**: Retrieve group details.
- **Get Flashcards**: List all flashcards in a group.
- **Update Group**: Modify group name or description.
- **Delete Group**: Remove a group and all its flashcards.
- **Spaced Repetition**: Track simple mastery/progress per user/flashcard.
- **Practice Tracking**: Track practice events and performance metrics.
- **Due Cards**: View flashcards due for review based on progress.

## Topic Filtering

Flashcards are generated from specific topics by providing a `topic` (and optionally `custom_instructions`):

- The topic is used to search for relevant documents.
- Only matching document content is used for generation.
- Custom instructions refine style, difficulty, and focus within that topic.

## Spaced Repetition / Progress

The system tracks flashcard progress and simple mastery:

- Correct and incorrect counts.
- Current streak and mastery level.
- Whether a card is considered mastered.
- Last practiced timestamp and last result.

This data feeds into practice analytics.
