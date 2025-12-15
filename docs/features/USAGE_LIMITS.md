# Usage Limits

The system enforces daily usage limits to manage resource consumption.

## Usage Types

Four types of usage are tracked:

1. **Chat Messages**: Number of chat messages sent per day.
2. **Flashcard Generations**: Number of flashcard groups created per day.
3. **Quiz Generations**: Number of quizzes created per day.
4. **Document Uploads**: Number of documents uploaded per day.

## Daily Limits

Each usage type has a configurable daily limit. Limits reset at midnight UTC.

## Usage Tracking

- **Check Before Action**: Limits are checked before allowing an action.
- **Automatic Increment**: Counters increment when actions succeed.
- **Daily Reset**: Counters reset automatically each day.
- **Per-User Tracking**: Each user has independent usage counters.

## Usage Features

- **Get Usage**: View current usage statistics and limits.
- **Automatic Enforcement**: System prevents actions when limits are exceeded.
- **Error Handling**: Clear error messages when limits are reached.

## Usage Statistics

Usage statistics include:

- `used`: Current count for the day.
- `limit`: Maximum allowed per day.
- Available for all four usage types.


