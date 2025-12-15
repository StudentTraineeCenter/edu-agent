# Practice Records

Practice records track user progress when studying flashcards or taking quizzes.

## Practice Recording

Each record stores:

- `user_id`: User who made the attempt.
- `project_id`: Project context.
- `item_type`: `"flashcard"` or `"quiz"`.
- `item_id`: ID of the flashcard or quiz question.
- `topic`: Extracted topic from the question/flashcard.
- `user_answer`: User's answer (for quizzes; `null` for flashcards).
- `correct_answer`: The correct answer.
- `was_correct`: Whether the user got it right.
- `created_at`: Timestamp.

## Practice Features

- **Create Practice Record**: Record a single practice event.
- **Create Batch**: Record multiple practice events in one operation.
- **List Practice Records**: View all practice records for a user (optionally filtered by project).

## Use Cases

Practice records enable:

- **Progress Tracking**: Monitor learning progress over time.
- **Performance Analytics**: Analyze correct/incorrect patterns.
- **Topic Analysis**: Identify which topics need more practice.


