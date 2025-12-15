# Quizzes

Quizzes are AI-generated multiple-choice questions created from project documents.

## Quiz Generation

### Process

1. User requests quiz creation (via API or chat).
2. System searches project documents for relevant content.
3. AI analyzes document content.
4. AI generates quiz name, description, and questions.
5. Questions are saved to the database.

### Generation Parameters

- `topic`: Topic to focus quiz generation on (e.g., `"photosynthesis"`, `"Chapter 3"`).
- `custom_instructions`: Free-form instructions for style/format/difficulty (e.g., `"explain answers in detail"`, `"mix easy and hard questions"`).
- `count`: Number of questions to generate (typically 10–30).
- `difficulty`: Target difficulty (`easy`, `medium`, `hard`) – used as a hint, not a hard constraint.
- `project_id`: Project containing source documents.

## Quiz Structure

Each quiz contains:

- **Name**: Auto-generated concise title (2–6 words).
- **Description**: Brief explanation of quiz content (1–2 sentences).
- **Questions**: Multiple-choice questions with:
  - Question text.
  - Four options (A, B, C, D).
  - Correct answer (`a`, `b`, `c`, or `d`).
  - Explanation for the correct answer.
  - Difficulty level (`easy`, `medium`, `hard`).

## Quiz Features

- **Create Quiz**: Generate a new quiz from documents.
- **List Quizzes**: View all quizzes in a project.
- **Get Quiz**: Retrieve quiz details.
- **Get Questions**: List all questions in a quiz.
- **Submit Answers**: Submit quiz answers and get results.
- **Delete Quiz**: Remove a quiz and all its questions.

## Quiz Submission

When submitting quiz answers:

1. User provides answers as a mapping of question IDs to selected options.
2. System evaluates each answer.
3. Results include:
   - Total questions.
   - Number correct.
   - Score percentage.
   - Letter grade (A–F).
   - Per-question results with explanations.

### Grading Scale

- A: 90–100%
- B: 80–89%
- C: 70–79%
- D: 60–69%
- F: Below 60%

## Topic Filtering

Quizzes are generated from specific topics by providing a `topic` (and optionally `custom_instructions`):

- The topic is used to search for relevant documents.
- Only matching document content is used for generation.
- Custom instructions refine style, difficulty, and focus within that topic.

## Question Quality

Generated questions follow these guidelines:

- Test understanding, not just memorization.
- Mix of difficulty levels.
- Cover key concepts, definitions, and applications.
- Clear and concise wording.
- Plausible but clearly wrong distractors.
- Detailed explanations for correct answers.


