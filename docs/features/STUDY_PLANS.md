# Study Plans

Study Plans are AI-generated personalized learning paths created based on a student's performance in practice quizzes and flashcards.

## Overview

The Study Plan feature analyzes a user's practice history to identify weak topics (where success rate is < 70%) and generates a targeted plan using available quizzes and flashcards to help improve mastery.

## Study Plan Generation

### Process

1. **Performance Analysis**: System fetches the user's `PracticeRecords` for the project.
2. **Weakness Identification**: Calculates success rates per topic. Topics with < 70% success rate are flagged as "weak".
3. **Resource Gathering**: System identifies available Quizzes and Flashcards in the project.
4. **AI Generation**:
   - A prompt containing the performance summary, weak topics, and available resources is sent to Azure OpenAI.
   - The AI generates a structured plan with specific recommendations and a study schedule.
5. **Storage**: The plan is saved to the database as a JSON object linked to the user and project.

### Generation Triggers

- **Manual Request**: Users can request a new study plan at any time (e.g., "Generate a new plan for me").
- **Performance Updates**: (Future) Could be triggered automatically after significant practice activity.

## Study Plan Structure

Each Study Plan (`StudyPlanDto`) contains:

- `id`: Unique identifier.
- `user_id`: ID of the user.
- `project_id`: ID of the project.
- `weak_topics`: List of topics identified as weak areas.
- `content`: Structured content containing:
  - **Goal**: Overall objective of the plan.
  - **Schedule**: Recommended daily/weekly tasks.
  - **Resources**: specific links to Quizzes or Flashcard groups to practice.
  - **Tips**: Study advice based on performance patterns.
- `created_at`: Timestamp when the plan was generated.

## Study Plan Features

- **Generate Study Plan**: Create a new personalized plan based on current statistics.
- **Get Latest Plan**: Retrieve the most recently generated plan for the project.
- **List Plans**: View history of all generated study plans.

## Usage

Study Plans serve as a dynamic syllabus that adapts to the student's learning curve, ensuring time is spent on areas that need the most improvement.
