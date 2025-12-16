import * as HttpClientError from '@effect/platform/HttpClientError'
import * as HttpClientRequest from '@effect/platform/HttpClientRequest'
import * as HttpClientResponse from '@effect/platform/HttpClientResponse'
import * as Data from 'effect/Data'
import * as Effect from 'effect/Effect'
import * as S from 'effect/Schema'
import type { ParseError } from 'effect/ParseResult'
import type * as HttpClient from '@effect/platform/HttpClient'

export class HealthCheckHealthGet200 extends S.Struct({}) {}

export class ProjectDto extends S.Class<ProjectDto>('ProjectDto')({
  /**
   * Unique ID of the project
   */
  id: S.String,
  /**
   * ID of the user who owns the project
   */
  owner_id: S.String,
  /**
   * Name of the project
   */
  name: S.String,
  /**
   * Description of the project
   */
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * Language code for the project
   */
  language_code: S.String,
  /**
   * Date and time the project was created
   */
  created_at: S.String,
}) {}

export class ListProjectsApiV1ProjectsGet200 extends S.Array(ProjectDto) {}

export class ProjectCreate extends S.Class<ProjectCreate>('ProjectCreate')({
  /**
   * Name of the project
   */
  name: S.String,
  /**
   * Description of the project
   */
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * Language code for the project
   */
  language_code: S.optionalWith(S.String, {
    nullable: true,
    default: () => 'en' as const,
  }),
}) {}

export class ValidationError extends S.Class<ValidationError>(
  'ValidationError',
)({
  loc: S.Array(S.Union(S.String, S.Int)),
  msg: S.String,
  type: S.String,
}) {}

export class HTTPValidationError extends S.Class<HTTPValidationError>(
  'HTTPValidationError',
)({
  detail: S.optionalWith(S.Array(ValidationError), { nullable: true }),
}) {}

export class ProjectUpdate extends S.Class<ProjectUpdate>('ProjectUpdate')({
  /**
   * Name of the project
   */
  name: S.optionalWith(S.String, { nullable: true }),
  /**
   * Description of the project
   */
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * Language code for the project
   */
  language_code: S.optionalWith(S.String, { nullable: true }),
}) {}

export class BodyUploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost extends S.Class<BodyUploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost>(
  'BodyUploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost',
)({
  files: S.Array(S.instanceOf(globalThis.Blob)),
}) {}

export class UploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost201 extends S.Struct(
  {},
) {}

/**
 * Document processing status enum.
 */
export class DocumentStatus extends S.Literal(
  'uploaded',
  'processing',
  'processed',
  'indexed',
  'failed',
) {}

export class DocumentDto extends S.Class<DocumentDto>('DocumentDto')({
  /**
   * Unique ID of the document
   */
  id: S.String,
  /**
   * ID of the document owner
   */
  owner_id: S.String,
  /**
   * ID of the project the document belongs to
   */
  project_id: S.optionalWith(S.String, { nullable: true }),
  /**
   * Name of the document file
   */
  file_name: S.String,
  /**
   * File extension (pdf, docx, txt, etc.)
   */
  file_type: S.String,
  /**
   * File size in bytes
   */
  file_size: S.Int.pipe(S.greaterThan(0)),
  /**
   * Document processing status: uploaded, processing, processed, failed, indexed
   */
  status: DocumentStatus,
  /**
   * Auto-generated summary of the document
   */
  summary: S.optionalWith(S.String, { nullable: true }),
  /**
   * Date and time the document was uploaded
   */
  uploaded_at: S.String,
  /**
   * Date and time the document was processed
   */
  processed_at: S.optionalWith(S.String, { nullable: true }),
}) {}

export class ListDocumentsApiV1ProjectsProjectIdDocumentsGet200 extends S.Array(
  DocumentDto,
) {}

export class DocumentCreate extends S.Class<DocumentCreate>('DocumentCreate')({
  /**
   * Name of the document file
   */
  file_name: S.String,
  /**
   * File extension (pdf, docx, txt, etc.)
   */
  file_type: S.String,
  /**
   * File size in bytes
   */
  file_size: S.Int.pipe(S.greaterThan(0)),
  /**
   * Auto-generated summary of the document
   */
  summary: S.optionalWith(S.String, { nullable: true }),
}) {}

export class DocumentUpdate extends S.Class<DocumentUpdate>('DocumentUpdate')({
  /**
   * Name of the document file
   */
  file_name: S.optionalWith(S.String, { nullable: true }),
  /**
   * Auto-generated summary of the document
   */
  summary: S.optionalWith(S.String, { nullable: true }),
}) {}

export class SourceDto extends S.Class<SourceDto>('SourceDto')({
  /**
   * Unique ID of the source segment
   */
  id: S.String,
  /**
   * Content of the source segment
   */
  content: S.String,
  /**
   * Title/name of the source document
   */
  title: S.String,
  /**
   * ID of the source document
   */
  document_id: S.String,
}) {}

/**
 * Current state of the tool call
 */
export class ToolCallDtoState extends S.Literal(
  'input-streaming',
  'input-available',
  'output-available',
  'output-error',
) {}

export class ToolCallDto extends S.Class<ToolCallDto>('ToolCallDto')({
  /**
   * Unique ID of the tool call
   */
  id: S.String,
  /**
   * Tool type identifier
   */
  type: S.String,
  /**
   * Name of the tool being called
   */
  name: S.String,
  /**
   * Current state of the tool call
   */
  state: ToolCallDtoState,
  /**
   * Input parameters for the tool
   */
  input: S.optionalWith(S.Record({ key: S.String, value: S.Unknown }), {
    nullable: true,
  }),
  /**
   * Output result from the tool
   */
  output: S.optionalWith(
    S.Union(S.Record({ key: S.String, value: S.Unknown }), S.String),
    { nullable: true },
  ),
  /**
   * Error message if failed
   */
  error_text: S.optionalWith(S.String, { nullable: true }),
}) {}

export class ChatMessageDto extends S.Class<ChatMessageDto>('ChatMessageDto')({
  /**
   * Unique ID of the message
   */
  id: S.String,
  /**
   * Role of the message sender
   */
  role: S.String,
  /**
   * Content of the message
   */
  content: S.String,
  /**
   * Source documents for assistant messages
   */
  sources: S.optionalWith(S.Array(SourceDto), { nullable: true }),
  /**
   * Tool calls made during message generation
   */
  tools: S.optionalWith(S.Array(ToolCallDto), { nullable: true }),
  /**
   * Date and time the message was created
   */
  created_at: S.String,
}) {}

export class ChatDto extends S.Class<ChatDto>('ChatDto')({
  /**
   * Unique ID of the chat
   */
  id: S.String,
  /**
   * ID of the project this chat belongs to
   */
  project_id: S.String,
  /**
   * ID of the user who created the chat
   */
  user_id: S.String,
  /**
   * Title of the chat
   */
  title: S.optionalWith(S.String, { nullable: true }),
  /**
   * List of messages in the chat
   */
  messages: S.optionalWith(S.Array(ChatMessageDto), { nullable: true }),
  /**
   * Date and time the chat was created
   */
  created_at: S.String,
  /**
   * Date and time the chat was updated
   */
  updated_at: S.String,
}) {}

export class ListChatsApiV1ProjectsProjectIdChatsGet200 extends S.Array(
  ChatDto,
) {}

export class ChatCreate extends S.Class<ChatCreate>('ChatCreate')({
  /**
   * Title of the chat
   */
  title: S.optionalWith(S.String, { nullable: true }),
}) {}

export class ChatUpdate extends S.Class<ChatUpdate>('ChatUpdate')({
  /**
   * Title of the chat
   */
  title: S.optionalWith(S.String, { nullable: true }),
}) {}

export class ChatCompletionRequest extends S.Class<ChatCompletionRequest>(
  'ChatCompletionRequest',
)({
  /**
   * User message to process
   */
  message: S.String,
}) {}

export class SendStreamingMessageApiV1ProjectsProjectIdChatsChatIdMessagesStreamPost200 extends S.Struct(
  {},
) {}

export class NoteDto extends S.Class<NoteDto>('NoteDto')({
  /**
   * Unique ID of the note
   */
  id: S.String,
  /**
   * ID of the project the note belongs to
   */
  project_id: S.String,
  /**
   * Title of the note
   */
  title: S.String,
  /**
   * Description of the note
   */
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * Content of the note
   */
  content: S.String,
  /**
   * Date and time the note was created
   */
  created_at: S.String,
  /**
   * Date and time the note was updated
   */
  updated_at: S.String,
}) {}

export class ListNotesApiV1ProjectsProjectIdNotesGet200 extends S.Array(
  NoteDto,
) {}

export class NoteCreate extends S.Class<NoteCreate>('NoteCreate')({
  /**
   * Title of the note
   */
  title: S.String,
  /**
   * Content of the note
   */
  content: S.String,
  /**
   * Description of the note
   */
  description: S.optionalWith(S.String, { nullable: true }),
}) {}

export class NoteUpdate extends S.Class<NoteUpdate>('NoteUpdate')({
  /**
   * Title of the note
   */
  title: S.optionalWith(S.String, { nullable: true }),
  /**
   * Content of the note
   */
  content: S.optionalWith(S.String, { nullable: true }),
  /**
   * Description of the note
   */
  description: S.optionalWith(S.String, { nullable: true }),
}) {}

export class GenerateRequest extends S.Class<GenerateRequest>(
  'GenerateRequest',
)({
  /**
   * Topic for generation
   */
  topic: S.optionalWith(S.String, { nullable: true }),
  /**
   * Custom instructions for generation
   */
  custom_instructions: S.optionalWith(S.String, { nullable: true }),
  /**
   * Number of items to generate (for flashcards/quizzes)
   */
  count: S.optionalWith(S.Int, { nullable: true }),
  /**
   * Difficulty level (for flashcards/quizzes)
   */
  difficulty: S.optionalWith(S.String, { nullable: true }),
}) {}

export class GenerateNoteStreamApiV1ProjectsProjectIdNotesNoteIdGenerateStreamPost200 extends S.Struct(
  {},
) {}

export class QuizDto extends S.Class<QuizDto>('QuizDto')({
  /**
   * Unique ID of the quiz
   */
  id: S.String,
  /**
   * ID of the project the quiz belongs to
   */
  project_id: S.String,
  /**
   * Name of the quiz
   */
  name: S.String,
  /**
   * Description of the quiz
   */
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * Date and time the quiz was created
   */
  created_at: S.String,
  /**
   * Date and time the quiz was updated
   */
  updated_at: S.String,
}) {}

export class ListQuizzesApiV1ProjectsProjectIdQuizzesGet200 extends S.Array(
  QuizDto,
) {}

export class QuizCreate extends S.Class<QuizCreate>('QuizCreate')({
  /**
   * Name of the quiz
   */
  name: S.String,
  /**
   * Description of the quiz
   */
  description: S.optionalWith(S.String, { nullable: true }),
}) {}

export class QuizUpdate extends S.Class<QuizUpdate>('QuizUpdate')({
  /**
   * Name of the quiz
   */
  name: S.optionalWith(S.String, { nullable: true }),
  /**
   * Description of the quiz
   */
  description: S.optionalWith(S.String, { nullable: true }),
}) {}

export class GenerateQuizStreamApiV1ProjectsProjectIdQuizzesQuizIdGenerateStreamPost200 extends S.Struct(
  {},
) {}

/**
 * Quiz question data transfer object.
 */
export class QuizQuestionDto extends S.Class<QuizQuestionDto>(
  'QuizQuestionDto',
)({
  /**
   * Unique ID of the quiz question
   */
  id: S.String,
  /**
   * ID of the quiz this question belongs to
   */
  quiz_id: S.String,
  /**
   * ID of the project
   */
  project_id: S.String,
  /**
   * The quiz question text
   */
  question_text: S.String,
  /**
   * Option A
   */
  option_a: S.String,
  /**
   * Option B
   */
  option_b: S.String,
  /**
   * Option C
   */
  option_c: S.String,
  /**
   * Option D
   */
  option_d: S.String,
  /**
   * Correct option: a, b, c, or d
   */
  correct_option: S.String,
  /**
   * Explanation for the correct answer
   */
  explanation: S.optionalWith(S.String, { nullable: true }),
  /**
   * Difficulty level: easy, medium, or hard
   */
  difficulty_level: S.String,
  /**
   * Position for ordering within quiz
   */
  position: S.Int,
  /**
   * Date and time the question was created
   */
  created_at: S.String,
}) {}

export class ListQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsGet200 extends S.Array(
  QuizQuestionDto,
) {}

export class QuizQuestionCreate extends S.Class<QuizQuestionCreate>(
  'QuizQuestionCreate',
)({
  /**
   * The quiz question text
   */
  question_text: S.String,
  /**
   * Option A
   */
  option_a: S.String,
  /**
   * Option B
   */
  option_b: S.String,
  /**
   * Option C
   */
  option_c: S.String,
  /**
   * Option D
   */
  option_d: S.String,
  /**
   * Correct option: a, b, c, or d
   */
  correct_option: S.String,
  /**
   * Explanation for the correct answer
   */
  explanation: S.optionalWith(S.String, { nullable: true }),
  /**
   * Difficulty level (easy, medium, hard)
   */
  difficulty_level: S.optionalWith(S.String, {
    nullable: true,
    default: () => 'medium' as const,
  }),
  /**
   * Position for ordering within the quiz
   */
  position: S.optionalWith(S.Int, { nullable: true }),
}) {}

export class QuizQuestionUpdate extends S.Class<QuizQuestionUpdate>(
  'QuizQuestionUpdate',
)({
  /**
   * The quiz question text
   */
  question_text: S.optionalWith(S.String, { nullable: true }),
  /**
   * Option A
   */
  option_a: S.optionalWith(S.String, { nullable: true }),
  /**
   * Option B
   */
  option_b: S.optionalWith(S.String, { nullable: true }),
  /**
   * Option C
   */
  option_c: S.optionalWith(S.String, { nullable: true }),
  /**
   * Option D
   */
  option_d: S.optionalWith(S.String, { nullable: true }),
  /**
   * Correct option: a, b, c, or d
   */
  correct_option: S.optionalWith(S.String, { nullable: true }),
  /**
   * Explanation for the correct answer
   */
  explanation: S.optionalWith(S.String, { nullable: true }),
  /**
   * Difficulty level (easy, medium, hard)
   */
  difficulty_level: S.optionalWith(S.String, { nullable: true }),
  /**
   * Position for ordering within the quiz
   */
  position: S.optionalWith(S.Int, { nullable: true }),
}) {}

export class QuizQuestionReorder extends S.Class<QuizQuestionReorder>(
  'QuizQuestionReorder',
)({
  /**
   * List of question IDs in the desired order
   */
  question_ids: S.Array(S.String),
}) {}

export class ReorderQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsReorderPatch200 extends S.Array(
  QuizQuestionDto,
) {}

export class ListFlashcardGroupsApiV1ProjectsProjectIdFlashcardGroupsGetParams extends S.Struct(
  {
    /**
     * Filter by study session ID
     */
    study_session_id: S.optionalWith(S.String, { nullable: true }),
  },
) {}

export class FlashcardGroupDto extends S.Class<FlashcardGroupDto>(
  'FlashcardGroupDto',
)({
  /**
   * Unique ID of the flashcard group
   */
  id: S.String,
  /**
   * ID of the project the flashcard group belongs to
   */
  project_id: S.String,
  /**
   * Name of the flashcard group
   */
  name: S.String,
  /**
   * Description of the flashcard group
   */
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * ID of the study session if this group belongs to one
   */
  study_session_id: S.optionalWith(S.String, { nullable: true }),
  /**
   * Date and time the flashcard group was created
   */
  created_at: S.String,
  /**
   * Date and time the flashcard group was updated
   */
  updated_at: S.String,
}) {}

export class ListFlashcardGroupsApiV1ProjectsProjectIdFlashcardGroupsGet200 extends S.Array(
  FlashcardGroupDto,
) {}

export class FlashcardGroupCreate extends S.Class<FlashcardGroupCreate>(
  'FlashcardGroupCreate',
)({
  /**
   * Name of the flashcard group
   */
  name: S.String,
  /**
   * Description of the flashcard group
   */
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * ID of the study session if this group belongs to one
   */
  study_session_id: S.optionalWith(S.String, { nullable: true }),
}) {}

export class FlashcardGroupUpdate extends S.Class<FlashcardGroupUpdate>(
  'FlashcardGroupUpdate',
)({
  /**
   * Name of the flashcard group
   */
  name: S.optionalWith(S.String, { nullable: true }),
  /**
   * Description of the flashcard group
   */
  description: S.optionalWith(S.String, { nullable: true }),
}) {}

export class GenerateFlashcardsStreamApiV1ProjectsProjectIdFlashcardGroupsGroupIdGenerateStreamPost200 extends S.Struct(
  {},
) {}

export class FlashcardDto extends S.Class<FlashcardDto>('FlashcardDto')({
  /**
   * Unique ID of the flashcard
   */
  id: S.String,
  /**
   * ID of the flashcard group
   */
  group_id: S.String,
  /**
   * ID of the project the flashcard belongs to
   */
  project_id: S.String,
  /**
   * Question of the flashcard
   */
  question: S.String,
  /**
   * Answer of the flashcard
   */
  answer: S.String,
  /**
   * Difficulty level of the flashcard
   */
  difficulty_level: S.String,
  /**
   * Position of the flashcard within the group
   */
  position: S.Int,
  /**
   * Date and time the flashcard was created
   */
  created_at: S.String,
}) {}

export class ListFlashcardsApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsGet200 extends S.Array(
  FlashcardDto,
) {}

export class FlashcardCreate extends S.Class<FlashcardCreate>(
  'FlashcardCreate',
)({
  /**
   * Question of the flashcard
   */
  question: S.String,
  /**
   * Answer of the flashcard
   */
  answer: S.String,
  /**
   * Difficulty level (easy, medium, hard)
   */
  difficulty_level: S.optionalWith(S.String, {
    nullable: true,
    default: () => 'medium' as const,
  }),
  /**
   * Position for ordering within the group
   */
  position: S.optionalWith(S.Int, { nullable: true }),
}) {}

export class FlashcardUpdate extends S.Class<FlashcardUpdate>(
  'FlashcardUpdate',
)({
  /**
   * Question of the flashcard
   */
  question: S.optionalWith(S.String, { nullable: true }),
  /**
   * Answer of the flashcard
   */
  answer: S.optionalWith(S.String, { nullable: true }),
  /**
   * Difficulty level (easy, medium, hard)
   */
  difficulty_level: S.optionalWith(S.String, { nullable: true }),
  /**
   * Position for ordering within the group
   */
  position: S.optionalWith(S.Int, { nullable: true }),
}) {}

/**
 * Practice record data transfer object.
 */
export class PracticeRecordDto extends S.Class<PracticeRecordDto>(
  'PracticeRecordDto',
)({
  /**
   * Unique ID of the practice record
   */
  id: S.String,
  /**
   * ID of the user
   */
  user_id: S.String,
  /**
   * ID of the project
   */
  project_id: S.String,
  /**
   * Type of study resource: flashcard or quiz
   */
  item_type: S.String,
  /**
   * ID of the study resource (flashcard or quiz question)
   */
  item_id: S.String,
  /**
   * Topic extracted from question
   */
  topic: S.String,
  /**
   * User's answer (only for quizzes, null for flashcards)
   */
  user_answer: S.optionalWith(S.String, { nullable: true }),
  /**
   * The correct answer
   */
  correct_answer: S.String,
  /**
   * Whether the user got it right
   */
  was_correct: S.Boolean,
  /**
   * Date and time the practice record was created
   */
  created_at: S.String,
}) {}

export class ListPracticeRecordsApiV1ProjectsProjectIdPracticeRecordsGet200 extends S.Array(
  PracticeRecordDto,
) {}

export class PracticeRecordCreate extends S.Class<PracticeRecordCreate>(
  'PracticeRecordCreate',
)({
  /**
   * Type of study resource: flashcard or quiz
   */
  item_type: S.String.pipe(S.pattern(new RegExp('^(flashcard|quiz)$'))),
  /**
   * ID of the study resource (flashcard or quiz question)
   */
  item_id: S.String,
  /**
   * Topic extracted from question
   */
  topic: S.String.pipe(S.maxLength(500)),
  /**
   * User's answer (only for quizzes, null for flashcards)
   */
  user_answer: S.optionalWith(S.String, { nullable: true }),
  /**
   * The correct answer - flashcard answer or quiz correct option
   */
  correct_answer: S.String,
  /**
   * Whether the user got it right
   */
  was_correct: S.Boolean,
}) {}

export class PracticeRecordBatchCreate extends S.Class<PracticeRecordBatchCreate>(
  'PracticeRecordBatchCreate',
)({
  /**
   * List of practice records to create
   */
  practice_records: S.NonEmptyArray(PracticeRecordCreate).pipe(
    S.minItems(1),
    S.maxItems(100),
  ),
}) {}

export class CreatePracticeRecordsBatchApiV1ProjectsProjectIdPracticeRecordsBatchPost201 extends S.Array(
  PracticeRecordDto,
) {}

/**
 * Mind map data transfer object.
 */
export class MindMapDto extends S.Class<MindMapDto>('MindMapDto')({
  /**
   * Unique ID of the mind map
   */
  id: S.String,
  /**
   * ID of the user
   */
  user_id: S.String,
  /**
   * ID of the project
   */
  project_id: S.String,
  /**
   * Title of the mind map
   */
  title: S.String,
  /**
   * Description of the mind map
   */
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * Structured mind map data (nodes, edges)
   */
  map_data: S.Record({ key: S.String, value: S.Unknown }),
  /**
   * Date and time the mind map was generated
   */
  generated_at: S.String,
  /**
   * Date and time the mind map was updated
   */
  updated_at: S.String,
}) {}

export class ListMindMapsApiV1ProjectsProjectIdMindMapsGet200 extends S.Array(
  MindMapDto,
) {}

export class MindMapCreate extends S.Class<MindMapCreate>('MindMapCreate')({
  /**
   * Title of the mind map
   */
  title: S.String,
  /**
   * Description of the mind map
   */
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * Custom instructions for AI generation
   */
  custom_instructions: S.optionalWith(S.String, { nullable: true }),
}) {}

export class CreateMindMapStreamApiV1ProjectsProjectIdMindMapsStreamPost200 extends S.Struct(
  {},
) {}

export class ListStudySessionsApiV1ProjectsProjectIdStudySessionsGetParams extends S.Struct(
  {
    /**
     * Maximum number of sessions to return
     */
    limit: S.optionalWith(
      S.Int.pipe(S.greaterThanOrEqualTo(1), S.lessThanOrEqualTo(100)),
      { nullable: true, default: () => 50 as const },
    ),
  },
) {}

/**
 * Study session data transfer object.
 */
export class StudySessionDto extends S.Class<StudySessionDto>(
  'StudySessionDto',
)({
  /**
   * Unique ID of the study session
   */
  id: S.String,
  /**
   * ID of the user
   */
  user_id: S.String,
  /**
   * ID of the project
   */
  project_id: S.String,
  /**
   * Session data containing flashcards, focus_topics, learning_objectives
   */
  session_data: S.Record({ key: S.String, value: S.Unknown }),
  /**
   * Estimated time in minutes
   */
  estimated_time_minutes: S.Int,
  /**
   * Requested session length in minutes
   */
  session_length_minutes: S.Int,
  /**
   * Optional focus topics
   */
  focus_topics: S.optionalWith(S.Array(S.String), { nullable: true }),
  /**
   * Date and time the session was generated
   */
  generated_at: S.String,
  /**
   * Date and time the session was started
   */
  started_at: S.optionalWith(S.String, { nullable: true }),
  /**
   * Date and time the session was completed
   */
  completed_at: S.optionalWith(S.String, { nullable: true }),
}) {}

export class ListStudySessionsApiV1ProjectsProjectIdStudySessionsGet200 extends S.Array(
  StudySessionDto,
) {}

export class StudySessionCreate extends S.Class<StudySessionCreate>(
  'StudySessionCreate',
)({
  /**
   * Length of the study session in minutes
   */
  session_length_minutes: S.optionalWith(
    S.Int.pipe(S.greaterThanOrEqualTo(10), S.lessThanOrEqualTo(120)),
    { nullable: true, default: () => 30 as const },
  ),
  /**
   * Optional focus topics
   */
  focus_topics: S.optionalWith(S.Array(S.String), { nullable: true }),
}) {}

/**
 * DTO for usage limit information.
 */
export class UsageLimitDto extends S.Class<UsageLimitDto>('UsageLimitDto')({
  /**
   * Number of operations used today
   */
  used: S.Int,
  /**
   * Maximum number of operations allowed per day
   */
  limit: S.Int,
}) {}

/**
 * DTO for user usage statistics.
 */
export class UsageDto extends S.Class<UsageDto>('UsageDto')({
  /**
   * Chat message usage statistics
   */
  chat_messages: UsageLimitDto,
  /**
   * Flashcard generation usage statistics
   */
  flashcard_generations: UsageLimitDto,
  /**
   * Quiz generation usage statistics
   */
  quiz_generations: UsageLimitDto,
  /**
   * Mind map generation usage statistics
   */
  mindmap_generations: UsageLimitDto,
  /**
   * Document upload usage statistics
   */
  document_uploads: UsageLimitDto,
}) {}

export class UserDto extends S.Class<UserDto>('UserDto')({
  /**
   * Unique ID of the user
   */
  id: S.String,
  /**
   * Name of the user
   */
  name: S.optionalWith(S.String, { nullable: true }),
  /**
   * Email of the user
   */
  email: S.optionalWith(S.String, { nullable: true }),
  /**
   * Date and time the user was created
   */
  created_at: S.String,
  /**
   * Date and time the user was updated
   */
  updated_at: S.String,
}) {}

export class ListUsersApiV1UsersGet200 extends S.Array(UserDto) {}

export const make = (
  httpClient: HttpClient.HttpClient,
  options: {
    readonly transformClient?:
      | ((
          client: HttpClient.HttpClient,
        ) => Effect.Effect<HttpClient.HttpClient>)
      | undefined
  } = {},
): Client => {
  const unexpectedStatus = (response: HttpClientResponse.HttpClientResponse) =>
    Effect.flatMap(
      Effect.orElseSucceed(response.json, () => 'Unexpected status code'),
      (description) =>
        Effect.fail(
          new HttpClientError.ResponseError({
            request: response.request,
            response,
            reason: 'StatusCode',
            description:
              typeof description === 'string'
                ? description
                : JSON.stringify(description),
          }),
        ),
    )
  const withResponse: <A, E>(
    f: (response: HttpClientResponse.HttpClientResponse) => Effect.Effect<A, E>,
  ) => (
    request: HttpClientRequest.HttpClientRequest,
  ) => Effect.Effect<any, any> = options.transformClient
    ? (f) => (request) =>
        Effect.flatMap(
          Effect.flatMap(options.transformClient!(httpClient), (client) =>
            client.execute(request),
          ),
          f,
        )
    : (f) => (request) => Effect.flatMap(httpClient.execute(request), f)
  const decodeSuccess =
    <A, I, R>(schema: S.Schema<A, I, R>) =>
    (response: HttpClientResponse.HttpClientResponse) =>
      HttpClientResponse.schemaBodyJson(schema)(response)
  const decodeError =
    <const Tag extends string, A, I, R>(tag: Tag, schema: S.Schema<A, I, R>) =>
    (response: HttpClientResponse.HttpClientResponse) =>
      Effect.flatMap(
        HttpClientResponse.schemaBodyJson(schema)(response),
        (cause) => Effect.fail(ClientError(tag, cause, response)),
      )
  return {
    httpClient,
    healthCheckHealthGet: () =>
      HttpClientRequest.get(`/health`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(HealthCheckHealthGet200),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listProjectsApiV1ProjectsGet: () =>
      HttpClientRequest.get(`/api/v1/projects`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ListProjectsApiV1ProjectsGet200),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createProjectApiV1ProjectsPost: (options) =>
      HttpClientRequest.post(`/api/v1/projects`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ProjectDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getProjectApiV1ProjectsProjectIdGet: (projectId) =>
      HttpClientRequest.get(`/api/v1/projects/${projectId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ProjectDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteProjectApiV1ProjectsProjectIdDelete: (projectId) =>
      HttpClientRequest.del(`/api/v1/projects/${projectId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    updateProjectApiV1ProjectsProjectIdPatch: (projectId, options) =>
      HttpClientRequest.patch(`/api/v1/projects/${projectId}`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ProjectDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    uploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost: (
      projectId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/documents/upload`,
      ).pipe(
        HttpClientRequest.bodyFormDataRecord(options as any),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              UploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost201,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listDocumentsApiV1ProjectsProjectIdDocumentsGet: (projectId) =>
      HttpClientRequest.get(`/api/v1/projects/${projectId}/documents`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              ListDocumentsApiV1ProjectsProjectIdDocumentsGet200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createDocumentApiV1ProjectsProjectIdDocumentsPost: (projectId, options) =>
      HttpClientRequest.post(`/api/v1/projects/${projectId}/documents`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(DocumentDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getDocumentApiV1ProjectsProjectIdDocumentsDocumentIdGet: (
      projectId,
      documentId,
    ) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/documents/${documentId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(DocumentDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteDocumentApiV1ProjectsProjectIdDocumentsDocumentIdDelete: (
      projectId,
      documentId,
    ) =>
      HttpClientRequest.del(
        `/api/v1/projects/${projectId}/documents/${documentId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    updateDocumentApiV1ProjectsProjectIdDocumentsDocumentIdPatch: (
      projectId,
      documentId,
      options,
    ) =>
      HttpClientRequest.patch(
        `/api/v1/projects/${projectId}/documents/${documentId}`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(DocumentDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listChatsApiV1ProjectsProjectIdChatsGet: (projectId) =>
      HttpClientRequest.get(`/api/v1/projects/${projectId}/chats`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ListChatsApiV1ProjectsProjectIdChatsGet200),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createChatApiV1ProjectsProjectIdChatsPost: (projectId, options) =>
      HttpClientRequest.post(`/api/v1/projects/${projectId}/chats`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ChatDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getChatApiV1ProjectsProjectIdChatsChatIdGet: (projectId, chatId) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/chats/${chatId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ChatDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteChatApiV1ProjectsProjectIdChatsChatIdDelete: (projectId, chatId) =>
      HttpClientRequest.del(
        `/api/v1/projects/${projectId}/chats/${chatId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    updateChatApiV1ProjectsProjectIdChatsChatIdPatch: (
      projectId,
      chatId,
      options,
    ) =>
      HttpClientRequest.patch(
        `/api/v1/projects/${projectId}/chats/${chatId}`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ChatDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    sendStreamingMessageApiV1ProjectsProjectIdChatsChatIdMessagesStreamPost: (
      projectId,
      chatId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/chats/${chatId}/messages/stream`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              SendStreamingMessageApiV1ProjectsProjectIdChatsChatIdMessagesStreamPost200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listNotesApiV1ProjectsProjectIdNotesGet: (projectId) =>
      HttpClientRequest.get(`/api/v1/projects/${projectId}/notes`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ListNotesApiV1ProjectsProjectIdNotesGet200),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createNoteApiV1ProjectsProjectIdNotesPost: (projectId, options) =>
      HttpClientRequest.post(`/api/v1/projects/${projectId}/notes`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(NoteDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getNoteApiV1ProjectsProjectIdNotesNoteIdGet: (projectId, noteId) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/notes/${noteId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(NoteDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteNoteApiV1ProjectsProjectIdNotesNoteIdDelete: (projectId, noteId) =>
      HttpClientRequest.del(
        `/api/v1/projects/${projectId}/notes/${noteId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    updateNoteApiV1ProjectsProjectIdNotesNoteIdPatch: (
      projectId,
      noteId,
      options,
    ) =>
      HttpClientRequest.patch(
        `/api/v1/projects/${projectId}/notes/${noteId}`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(NoteDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    generateNoteApiV1ProjectsProjectIdNotesNoteIdGeneratePost: (
      projectId,
      noteId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/notes/${noteId}/generate`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(NoteDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    generateNoteStreamApiV1ProjectsProjectIdNotesNoteIdGenerateStreamPost: (
      projectId,
      noteId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/notes/${noteId}/generate/stream`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              GenerateNoteStreamApiV1ProjectsProjectIdNotesNoteIdGenerateStreamPost200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listQuizzesApiV1ProjectsProjectIdQuizzesGet: (projectId) =>
      HttpClientRequest.get(`/api/v1/projects/${projectId}/quizzes`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              ListQuizzesApiV1ProjectsProjectIdQuizzesGet200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createQuizApiV1ProjectsProjectIdQuizzesPost: (projectId, options) =>
      HttpClientRequest.post(`/api/v1/projects/${projectId}/quizzes`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(QuizDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getQuizApiV1ProjectsProjectIdQuizzesQuizIdGet: (projectId, quizId) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/quizzes/${quizId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(QuizDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteQuizApiV1ProjectsProjectIdQuizzesQuizIdDelete: (projectId, quizId) =>
      HttpClientRequest.del(
        `/api/v1/projects/${projectId}/quizzes/${quizId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    updateQuizApiV1ProjectsProjectIdQuizzesQuizIdPatch: (
      projectId,
      quizId,
      options,
    ) =>
      HttpClientRequest.patch(
        `/api/v1/projects/${projectId}/quizzes/${quizId}`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(QuizDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    generateQuizApiV1ProjectsProjectIdQuizzesQuizIdGeneratePost: (
      projectId,
      quizId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/quizzes/${quizId}/generate`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(QuizDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    generateQuizStreamApiV1ProjectsProjectIdQuizzesQuizIdGenerateStreamPost: (
      projectId,
      quizId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/quizzes/${quizId}/generate/stream`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              GenerateQuizStreamApiV1ProjectsProjectIdQuizzesQuizIdGenerateStreamPost200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsGet: (
      projectId,
      quizId,
    ) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/quizzes/${quizId}/questions`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              ListQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsGet200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createQuizQuestionApiV1ProjectsProjectIdQuizzesQuizIdQuestionsPost: (
      projectId,
      quizId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/quizzes/${quizId}/questions`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(QuizQuestionDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getQuizQuestionApiV1ProjectsProjectIdQuizzesQuizIdQuestionsQuestionIdGet: (
      projectId,
      quizId,
      questionId,
    ) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/quizzes/${quizId}/questions/${questionId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(QuizQuestionDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteQuizQuestionApiV1ProjectsProjectIdQuizzesQuizIdQuestionsQuestionIdDelete:
      (projectId, quizId, questionId) =>
        HttpClientRequest.del(
          `/api/v1/projects/${projectId}/quizzes/${quizId}/questions/${questionId}`,
        ).pipe(
          withResponse(
            HttpClientResponse.matchStatus({
              '422': decodeError('HTTPValidationError', HTTPValidationError),
              '204': () => Effect.void,
              orElse: unexpectedStatus,
            }),
          ),
        ),
    updateQuizQuestionApiV1ProjectsProjectIdQuizzesQuizIdQuestionsQuestionIdPatch:
      (projectId, quizId, questionId, options) =>
        HttpClientRequest.patch(
          `/api/v1/projects/${projectId}/quizzes/${quizId}/questions/${questionId}`,
        ).pipe(
          HttpClientRequest.bodyUnsafeJson(options),
          withResponse(
            HttpClientResponse.matchStatus({
              '2xx': decodeSuccess(QuizQuestionDto),
              '422': decodeError('HTTPValidationError', HTTPValidationError),
              orElse: unexpectedStatus,
            }),
          ),
        ),
    reorderQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsReorderPatch:
      (projectId, quizId, options) =>
        HttpClientRequest.patch(
          `/api/v1/projects/${projectId}/quizzes/${quizId}/questions/reorder`,
        ).pipe(
          HttpClientRequest.bodyUnsafeJson(options),
          withResponse(
            HttpClientResponse.matchStatus({
              '2xx': decodeSuccess(
                ReorderQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsReorderPatch200,
              ),
              '422': decodeError('HTTPValidationError', HTTPValidationError),
              orElse: unexpectedStatus,
            }),
          ),
        ),
    listFlashcardGroupsApiV1ProjectsProjectIdFlashcardGroupsGet: (
      projectId,
      options,
    ) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/flashcard-groups`,
      ).pipe(
        HttpClientRequest.setUrlParams({
          study_session_id: options?.['study_session_id'] as any,
        }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              ListFlashcardGroupsApiV1ProjectsProjectIdFlashcardGroupsGet200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createFlashcardGroupApiV1ProjectsProjectIdFlashcardGroupsPost: (
      projectId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/flashcard-groups`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(FlashcardGroupDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getFlashcardGroupApiV1ProjectsProjectIdFlashcardGroupsGroupIdGet: (
      projectId,
      groupId,
    ) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/flashcard-groups/${groupId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(FlashcardGroupDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteFlashcardGroupApiV1ProjectsProjectIdFlashcardGroupsGroupIdDelete: (
      projectId,
      groupId,
    ) =>
      HttpClientRequest.del(
        `/api/v1/projects/${projectId}/flashcard-groups/${groupId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    updateFlashcardGroupApiV1ProjectsProjectIdFlashcardGroupsGroupIdPatch: (
      projectId,
      groupId,
      options,
    ) =>
      HttpClientRequest.patch(
        `/api/v1/projects/${projectId}/flashcard-groups/${groupId}`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(FlashcardGroupDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    generateFlashcardsApiV1ProjectsProjectIdFlashcardGroupsGroupIdGeneratePost:
      (projectId, groupId, options) =>
        HttpClientRequest.post(
          `/api/v1/projects/${projectId}/flashcard-groups/${groupId}/generate`,
        ).pipe(
          HttpClientRequest.bodyUnsafeJson(options),
          withResponse(
            HttpClientResponse.matchStatus({
              '2xx': decodeSuccess(FlashcardGroupDto),
              '422': decodeError('HTTPValidationError', HTTPValidationError),
              orElse: unexpectedStatus,
            }),
          ),
        ),
    generateFlashcardsStreamApiV1ProjectsProjectIdFlashcardGroupsGroupIdGenerateStreamPost:
      (projectId, groupId, options) =>
        HttpClientRequest.post(
          `/api/v1/projects/${projectId}/flashcard-groups/${groupId}/generate/stream`,
        ).pipe(
          HttpClientRequest.bodyUnsafeJson(options),
          withResponse(
            HttpClientResponse.matchStatus({
              '2xx': decodeSuccess(
                GenerateFlashcardsStreamApiV1ProjectsProjectIdFlashcardGroupsGroupIdGenerateStreamPost200,
              ),
              '422': decodeError('HTTPValidationError', HTTPValidationError),
              orElse: unexpectedStatus,
            }),
          ),
        ),
    listFlashcardsApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsGet: (
      projectId,
      groupId,
    ) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/flashcard-groups/${groupId}/flashcards`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              ListFlashcardsApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsGet200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createFlashcardApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsPost: (
      projectId,
      groupId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/flashcard-groups/${groupId}/flashcards`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(FlashcardDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getFlashcardApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsFlashcardIdGet:
      (projectId, groupId, flashcardId) =>
        HttpClientRequest.get(
          `/api/v1/projects/${projectId}/flashcard-groups/${groupId}/flashcards/${flashcardId}`,
        ).pipe(
          withResponse(
            HttpClientResponse.matchStatus({
              '2xx': decodeSuccess(FlashcardDto),
              '422': decodeError('HTTPValidationError', HTTPValidationError),
              orElse: unexpectedStatus,
            }),
          ),
        ),
    deleteFlashcardApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsFlashcardIdDelete:
      (projectId, groupId, flashcardId) =>
        HttpClientRequest.del(
          `/api/v1/projects/${projectId}/flashcard-groups/${groupId}/flashcards/${flashcardId}`,
        ).pipe(
          withResponse(
            HttpClientResponse.matchStatus({
              '422': decodeError('HTTPValidationError', HTTPValidationError),
              '204': () => Effect.void,
              orElse: unexpectedStatus,
            }),
          ),
        ),
    updateFlashcardApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsFlashcardIdPatch:
      (projectId, groupId, flashcardId, options) =>
        HttpClientRequest.patch(
          `/api/v1/projects/${projectId}/flashcard-groups/${groupId}/flashcards/${flashcardId}`,
        ).pipe(
          HttpClientRequest.bodyUnsafeJson(options),
          withResponse(
            HttpClientResponse.matchStatus({
              '2xx': decodeSuccess(FlashcardDto),
              '422': decodeError('HTTPValidationError', HTTPValidationError),
              orElse: unexpectedStatus,
            }),
          ),
        ),
    listPracticeRecordsApiV1ProjectsProjectIdPracticeRecordsGet: (projectId) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/practice-records`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              ListPracticeRecordsApiV1ProjectsProjectIdPracticeRecordsGet200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createPracticeRecordApiV1ProjectsProjectIdPracticeRecordsPost: (
      projectId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/practice-records`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(PracticeRecordDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createPracticeRecordsBatchApiV1ProjectsProjectIdPracticeRecordsBatchPost: (
      projectId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/practice-records/batch`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              CreatePracticeRecordsBatchApiV1ProjectsProjectIdPracticeRecordsBatchPost201,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listMindMapsApiV1ProjectsProjectIdMindMapsGet: (projectId) =>
      HttpClientRequest.get(`/api/v1/projects/${projectId}/mind-maps`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              ListMindMapsApiV1ProjectsProjectIdMindMapsGet200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createMindMapApiV1ProjectsProjectIdMindMapsPost: (projectId, options) =>
      HttpClientRequest.post(`/api/v1/projects/${projectId}/mind-maps`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(MindMapDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getMindMapApiV1ProjectsProjectIdMindMapsMindMapIdGet: (
      projectId,
      mindMapId,
    ) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/mind-maps/${mindMapId}`,
      ).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(MindMapDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createMindMapStreamApiV1ProjectsProjectIdMindMapsStreamPost: (
      projectId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/mind-maps/stream`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              CreateMindMapStreamApiV1ProjectsProjectIdMindMapsStreamPost200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listStudySessionsApiV1ProjectsProjectIdStudySessionsGet: (
      projectId,
      options,
    ) =>
      HttpClientRequest.get(
        `/api/v1/projects/${projectId}/study-sessions`,
      ).pipe(
        HttpClientRequest.setUrlParams({ limit: options?.['limit'] as any }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              ListStudySessionsApiV1ProjectsProjectIdStudySessionsGet200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createStudySessionApiV1ProjectsProjectIdStudySessionsPost: (
      projectId,
      options,
    ) =>
      HttpClientRequest.post(
        `/api/v1/projects/${projectId}/study-sessions`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(StudySessionDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getStudySessionApiV1StudySessionsSessionIdGet: (sessionId) =>
      HttpClientRequest.get(`/api/v1/study-sessions/${sessionId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(StudySessionDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getUsageApiV1UsageGet: () =>
      HttpClientRequest.get(`/api/v1/usage`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(UsageDto),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getUserApiV1UsersUserIdGet: (userId) =>
      HttpClientRequest.get(`/api/v1/users/${userId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(UserDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteUserApiV1UsersUserIdDelete: (userId) =>
      HttpClientRequest.del(`/api/v1/users/${userId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listUsersApiV1UsersGet: () =>
      HttpClientRequest.get(`/api/v1/users`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ListUsersApiV1UsersGet200),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getCurrentUserInfoApiV1AuthMeGet: () =>
      HttpClientRequest.get(`/api/v1/auth/me`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(UserDto),
            orElse: unexpectedStatus,
          }),
        ),
      ),
  }
}

export interface Client {
  readonly httpClient: HttpClient.HttpClient
  /**
   * Health Check
   */
  readonly healthCheckHealthGet: () => Effect.Effect<
    typeof HealthCheckHealthGet200.Type,
    HttpClientError.HttpClientError | ParseError
  >
  /**
   * List all projects for a user.
   */
  readonly listProjectsApiV1ProjectsGet: () => Effect.Effect<
    typeof ListProjectsApiV1ProjectsGet200.Type,
    HttpClientError.HttpClientError | ParseError
  >
  /**
   * Create a new project.
   */
  readonly createProjectApiV1ProjectsPost: (
    options: typeof ProjectCreate.Encoded,
  ) => Effect.Effect<
    typeof ProjectDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a project by ID.
   */
  readonly getProjectApiV1ProjectsProjectIdGet: (
    projectId: string,
  ) => Effect.Effect<
    typeof ProjectDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a project.
   */
  readonly deleteProjectApiV1ProjectsProjectIdDelete: (
    projectId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Update a project.
   */
  readonly updateProjectApiV1ProjectsProjectIdPatch: (
    projectId: string,
    options: typeof ProjectUpdate.Encoded,
  ) => Effect.Effect<
    typeof ProjectDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Upload one or more documents. Processing happens asynchronously in background.
   */
  readonly uploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost: (
    projectId: string,
    options: typeof BodyUploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost.Encoded,
  ) => Effect.Effect<
    typeof UploadDocumentApiV1ProjectsProjectIdDocumentsUploadPost201.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all documents for a project.
   */
  readonly listDocumentsApiV1ProjectsProjectIdDocumentsGet: (
    projectId: string,
  ) => Effect.Effect<
    typeof ListDocumentsApiV1ProjectsProjectIdDocumentsGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new document.
   */
  readonly createDocumentApiV1ProjectsProjectIdDocumentsPost: (
    projectId: string,
    options: typeof DocumentCreate.Encoded,
  ) => Effect.Effect<
    typeof DocumentDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a document by ID.
   */
  readonly getDocumentApiV1ProjectsProjectIdDocumentsDocumentIdGet: (
    projectId: string,
    documentId: string,
  ) => Effect.Effect<
    typeof DocumentDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a document.
   */
  readonly deleteDocumentApiV1ProjectsProjectIdDocumentsDocumentIdDelete: (
    projectId: string,
    documentId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Update a document.
   */
  readonly updateDocumentApiV1ProjectsProjectIdDocumentsDocumentIdPatch: (
    projectId: string,
    documentId: string,
    options: typeof DocumentUpdate.Encoded,
  ) => Effect.Effect<
    typeof DocumentDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all chats for a project.
   */
  readonly listChatsApiV1ProjectsProjectIdChatsGet: (
    projectId: string,
  ) => Effect.Effect<
    typeof ListChatsApiV1ProjectsProjectIdChatsGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new chat.
   */
  readonly createChatApiV1ProjectsProjectIdChatsPost: (
    projectId: string,
    options: typeof ChatCreate.Encoded,
  ) => Effect.Effect<
    typeof ChatDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a chat by ID.
   */
  readonly getChatApiV1ProjectsProjectIdChatsChatIdGet: (
    projectId: string,
    chatId: string,
  ) => Effect.Effect<
    typeof ChatDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a chat.
   */
  readonly deleteChatApiV1ProjectsProjectIdChatsChatIdDelete: (
    projectId: string,
    chatId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Update a chat.
   */
  readonly updateChatApiV1ProjectsProjectIdChatsChatIdPatch: (
    projectId: string,
    chatId: string,
    options: typeof ChatUpdate.Encoded,
  ) => Effect.Effect<
    typeof ChatDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Send a message to a chat with streaming response
   */
  readonly sendStreamingMessageApiV1ProjectsProjectIdChatsChatIdMessagesStreamPost: (
    projectId: string,
    chatId: string,
    options: typeof ChatCompletionRequest.Encoded,
  ) => Effect.Effect<
    typeof SendStreamingMessageApiV1ProjectsProjectIdChatsChatIdMessagesStreamPost200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all notes for a project.
   */
  readonly listNotesApiV1ProjectsProjectIdNotesGet: (
    projectId: string,
  ) => Effect.Effect<
    typeof ListNotesApiV1ProjectsProjectIdNotesGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new note.
   */
  readonly createNoteApiV1ProjectsProjectIdNotesPost: (
    projectId: string,
    options: typeof NoteCreate.Encoded,
  ) => Effect.Effect<
    typeof NoteDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a note by ID.
   */
  readonly getNoteApiV1ProjectsProjectIdNotesNoteIdGet: (
    projectId: string,
    noteId: string,
  ) => Effect.Effect<
    typeof NoteDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a note.
   */
  readonly deleteNoteApiV1ProjectsProjectIdNotesNoteIdDelete: (
    projectId: string,
    noteId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Update a note.
   */
  readonly updateNoteApiV1ProjectsProjectIdNotesNoteIdPatch: (
    projectId: string,
    noteId: string,
    options: typeof NoteUpdate.Encoded,
  ) => Effect.Effect<
    typeof NoteDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Generate note content using AI and populate an existing note.
   */
  readonly generateNoteApiV1ProjectsProjectIdNotesNoteIdGeneratePost: (
    projectId: string,
    noteId: string,
    options: typeof GenerateRequest.Encoded,
  ) => Effect.Effect<
    typeof NoteDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Generate note content using AI with streaming progress updates.
   */
  readonly generateNoteStreamApiV1ProjectsProjectIdNotesNoteIdGenerateStreamPost: (
    projectId: string,
    noteId: string,
    options: typeof GenerateRequest.Encoded,
  ) => Effect.Effect<
    typeof GenerateNoteStreamApiV1ProjectsProjectIdNotesNoteIdGenerateStreamPost200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all quizzes for a project.
   */
  readonly listQuizzesApiV1ProjectsProjectIdQuizzesGet: (
    projectId: string,
  ) => Effect.Effect<
    typeof ListQuizzesApiV1ProjectsProjectIdQuizzesGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new quiz.
   */
  readonly createQuizApiV1ProjectsProjectIdQuizzesPost: (
    projectId: string,
    options: typeof QuizCreate.Encoded,
  ) => Effect.Effect<
    typeof QuizDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a quiz by ID.
   */
  readonly getQuizApiV1ProjectsProjectIdQuizzesQuizIdGet: (
    projectId: string,
    quizId: string,
  ) => Effect.Effect<
    typeof QuizDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a quiz.
   */
  readonly deleteQuizApiV1ProjectsProjectIdQuizzesQuizIdDelete: (
    projectId: string,
    quizId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Update a quiz.
   */
  readonly updateQuizApiV1ProjectsProjectIdQuizzesQuizIdPatch: (
    projectId: string,
    quizId: string,
    options: typeof QuizUpdate.Encoded,
  ) => Effect.Effect<
    typeof QuizDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Generate quiz questions using AI and populate an existing quiz.
   */
  readonly generateQuizApiV1ProjectsProjectIdQuizzesQuizIdGeneratePost: (
    projectId: string,
    quizId: string,
    options: typeof GenerateRequest.Encoded,
  ) => Effect.Effect<
    typeof QuizDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Generate quiz questions using AI with streaming progress updates.
   */
  readonly generateQuizStreamApiV1ProjectsProjectIdQuizzesQuizIdGenerateStreamPost: (
    projectId: string,
    quizId: string,
    options: typeof GenerateRequest.Encoded,
  ) => Effect.Effect<
    typeof GenerateQuizStreamApiV1ProjectsProjectIdQuizzesQuizIdGenerateStreamPost200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all questions in a quiz.
   */
  readonly listQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsGet: (
    projectId: string,
    quizId: string,
  ) => Effect.Effect<
    typeof ListQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new question in a quiz.
   */
  readonly createQuizQuestionApiV1ProjectsProjectIdQuizzesQuizIdQuestionsPost: (
    projectId: string,
    quizId: string,
    options: typeof QuizQuestionCreate.Encoded,
  ) => Effect.Effect<
    typeof QuizQuestionDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a question by ID.
   */
  readonly getQuizQuestionApiV1ProjectsProjectIdQuizzesQuizIdQuestionsQuestionIdGet: (
    projectId: string,
    quizId: string,
    questionId: string,
  ) => Effect.Effect<
    typeof QuizQuestionDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a question.
   */
  readonly deleteQuizQuestionApiV1ProjectsProjectIdQuizzesQuizIdQuestionsQuestionIdDelete: (
    projectId: string,
    quizId: string,
    questionId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Update a question.
   */
  readonly updateQuizQuestionApiV1ProjectsProjectIdQuizzesQuizIdQuestionsQuestionIdPatch: (
    projectId: string,
    quizId: string,
    questionId: string,
    options: typeof QuizQuestionUpdate.Encoded,
  ) => Effect.Effect<
    typeof QuizQuestionDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Reorder questions in a quiz.
   */
  readonly reorderQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsReorderPatch: (
    projectId: string,
    quizId: string,
    options: typeof QuizQuestionReorder.Encoded,
  ) => Effect.Effect<
    typeof ReorderQuizQuestionsApiV1ProjectsProjectIdQuizzesQuizIdQuestionsReorderPatch200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all flashcard groups for a project.
   */
  readonly listFlashcardGroupsApiV1ProjectsProjectIdFlashcardGroupsGet: (
    projectId: string,
    options?:
      | typeof ListFlashcardGroupsApiV1ProjectsProjectIdFlashcardGroupsGetParams.Encoded
      | undefined,
  ) => Effect.Effect<
    typeof ListFlashcardGroupsApiV1ProjectsProjectIdFlashcardGroupsGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new flashcard group.
   */
  readonly createFlashcardGroupApiV1ProjectsProjectIdFlashcardGroupsPost: (
    projectId: string,
    options: typeof FlashcardGroupCreate.Encoded,
  ) => Effect.Effect<
    typeof FlashcardGroupDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a flashcard group by ID.
   */
  readonly getFlashcardGroupApiV1ProjectsProjectIdFlashcardGroupsGroupIdGet: (
    projectId: string,
    groupId: string,
  ) => Effect.Effect<
    typeof FlashcardGroupDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a flashcard group.
   */
  readonly deleteFlashcardGroupApiV1ProjectsProjectIdFlashcardGroupsGroupIdDelete: (
    projectId: string,
    groupId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Update a flashcard group.
   */
  readonly updateFlashcardGroupApiV1ProjectsProjectIdFlashcardGroupsGroupIdPatch: (
    projectId: string,
    groupId: string,
    options: typeof FlashcardGroupUpdate.Encoded,
  ) => Effect.Effect<
    typeof FlashcardGroupDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Generate flashcards using AI and populate an existing flashcard group.
   */
  readonly generateFlashcardsApiV1ProjectsProjectIdFlashcardGroupsGroupIdGeneratePost: (
    projectId: string,
    groupId: string,
    options: typeof GenerateRequest.Encoded,
  ) => Effect.Effect<
    typeof FlashcardGroupDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Generate flashcards using AI with streaming progress updates.
   */
  readonly generateFlashcardsStreamApiV1ProjectsProjectIdFlashcardGroupsGroupIdGenerateStreamPost: (
    projectId: string,
    groupId: string,
    options: typeof GenerateRequest.Encoded,
  ) => Effect.Effect<
    typeof GenerateFlashcardsStreamApiV1ProjectsProjectIdFlashcardGroupsGroupIdGenerateStreamPost200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all flashcards in a group.
   */
  readonly listFlashcardsApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsGet: (
    projectId: string,
    groupId: string,
  ) => Effect.Effect<
    typeof ListFlashcardsApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new flashcard in a group.
   */
  readonly createFlashcardApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsPost: (
    projectId: string,
    groupId: string,
    options: typeof FlashcardCreate.Encoded,
  ) => Effect.Effect<
    typeof FlashcardDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a flashcard by ID.
   */
  readonly getFlashcardApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsFlashcardIdGet: (
    projectId: string,
    groupId: string,
    flashcardId: string,
  ) => Effect.Effect<
    typeof FlashcardDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a flashcard.
   */
  readonly deleteFlashcardApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsFlashcardIdDelete: (
    projectId: string,
    groupId: string,
    flashcardId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Update a flashcard.
   */
  readonly updateFlashcardApiV1ProjectsProjectIdFlashcardGroupsGroupIdFlashcardsFlashcardIdPatch: (
    projectId: string,
    groupId: string,
    flashcardId: string,
    options: typeof FlashcardUpdate.Encoded,
  ) => Effect.Effect<
    typeof FlashcardDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List practice records for a project.
   */
  readonly listPracticeRecordsApiV1ProjectsProjectIdPracticeRecordsGet: (
    projectId: string,
  ) => Effect.Effect<
    typeof ListPracticeRecordsApiV1ProjectsProjectIdPracticeRecordsGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a single practice record.
   */
  readonly createPracticeRecordApiV1ProjectsProjectIdPracticeRecordsPost: (
    projectId: string,
    options: typeof PracticeRecordCreate.Encoded,
  ) => Effect.Effect<
    typeof PracticeRecordDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create multiple practice records.
   */
  readonly createPracticeRecordsBatchApiV1ProjectsProjectIdPracticeRecordsBatchPost: (
    projectId: string,
    options: typeof PracticeRecordBatchCreate.Encoded,
  ) => Effect.Effect<
    typeof CreatePracticeRecordsBatchApiV1ProjectsProjectIdPracticeRecordsBatchPost201.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all mind maps for a project.
   */
  readonly listMindMapsApiV1ProjectsProjectIdMindMapsGet: (
    projectId: string,
  ) => Effect.Effect<
    typeof ListMindMapsApiV1ProjectsProjectIdMindMapsGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Generate/create a mind map.
   *
   * Note: AI generation is not yet implemented in edu-shared service.
   * This endpoint creates a basic mind map structure.
   */
  readonly createMindMapApiV1ProjectsProjectIdMindMapsPost: (
    projectId: string,
    options: typeof MindMapCreate.Encoded,
  ) => Effect.Effect<
    typeof MindMapDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a mind map by ID.
   */
  readonly getMindMapApiV1ProjectsProjectIdMindMapsMindMapIdGet: (
    projectId: string,
    mindMapId: string,
  ) => Effect.Effect<
    typeof MindMapDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Generate mind map with streaming progress updates.
   *
   * Note: AI generation is not yet implemented in edu-shared service.
   * This endpoint provides a streaming interface but returns a basic structure.
   */
  readonly createMindMapStreamApiV1ProjectsProjectIdMindMapsStreamPost: (
    projectId: string,
    options: typeof MindMapCreate.Encoded,
  ) => Effect.Effect<
    typeof CreateMindMapStreamApiV1ProjectsProjectIdMindMapsStreamPost200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List study sessions for a project.
   */
  readonly listStudySessionsApiV1ProjectsProjectIdStudySessionsGet: (
    projectId: string,
    options?:
      | typeof ListStudySessionsApiV1ProjectsProjectIdStudySessionsGetParams.Encoded
      | undefined,
  ) => Effect.Effect<
    typeof ListStudySessionsApiV1ProjectsProjectIdStudySessionsGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Generate/create a study session.
   *
   * Note: AI generation is not yet implemented in edu-shared service.
   * This endpoint creates a basic study session structure.
   */
  readonly createStudySessionApiV1ProjectsProjectIdStudySessionsPost: (
    projectId: string,
    options: typeof StudySessionCreate.Encoded,
  ) => Effect.Effect<
    typeof StudySessionDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a study session by ID.
   */
  readonly getStudySessionApiV1StudySessionsSessionIdGet: (
    sessionId: string,
  ) => Effect.Effect<
    typeof StudySessionDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get current usage statistics for the authenticated user
   */
  readonly getUsageApiV1UsageGet: () => Effect.Effect<
    typeof UsageDto.Type,
    HttpClientError.HttpClientError | ParseError
  >
  /**
   * Get a user by ID.
   */
  readonly getUserApiV1UsersUserIdGet: (
    userId: string,
  ) => Effect.Effect<
    typeof UserDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a user.
   */
  readonly deleteUserApiV1UsersUserIdDelete: (
    userId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all users.
   */
  readonly listUsersApiV1UsersGet: () => Effect.Effect<
    typeof ListUsersApiV1UsersGet200.Type,
    HttpClientError.HttpClientError | ParseError
  >
  /**
   * Get authenticated user information (requires auth)
   */
  readonly getCurrentUserInfoApiV1AuthMeGet: () => Effect.Effect<
    typeof UserDto.Type,
    HttpClientError.HttpClientError | ParseError
  >
}

export interface ClientError<Tag extends string, E> {
  readonly _tag: Tag
  readonly request: HttpClientRequest.HttpClientRequest
  readonly response: HttpClientResponse.HttpClientResponse
  readonly cause: E
}

class ClientErrorImpl extends Data.Error<{
  _tag: string
  cause: any
  request: HttpClientRequest.HttpClientRequest
  response: HttpClientResponse.HttpClientResponse
}> {}

export const ClientError = <Tag extends string, E>(
  tag: Tag,
  cause: E,
  response: HttpClientResponse.HttpClientResponse,
): ClientError<Tag, E> =>
  new ClientErrorImpl({
    _tag: tag,
    cause,
    response,
    request: response.request,
  }) as any
