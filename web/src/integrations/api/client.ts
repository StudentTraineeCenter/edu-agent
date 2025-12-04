import type * as HttpClient from '@effect/platform/HttpClient'
import * as HttpClientError from '@effect/platform/HttpClientError'
import * as HttpClientRequest from '@effect/platform/HttpClientRequest'
import * as HttpClientResponse from '@effect/platform/HttpClientResponse'
import * as Data from 'effect/Data'
import * as Effect from 'effect/Effect'
import type { ParseError } from 'effect/ParseResult'
import * as S from 'effect/Schema'

/**
 * Response model for project data.
 */
export class ProjectDto extends S.Class<ProjectDto>('ProjectDto')({
  /**
   * Unique ID of the project
   */
  id: S.String,
  /**
   * ID of the project owner
   */
  owner_id: S.String,
  /**
   * Name of the project
   */
  name: S.String,
  /**
   * Description of the project
   */
  description: S.NullOr(S.String),
  /**
   * Language code
   */
  language_code: S.String,
  /**
   * Creation timestamp
   */
  created_at: S.String,
}) {}

/**
 * Response model for listing projects.
 */
export class ProjectListResponse extends S.Class<ProjectListResponse>(
  'ProjectListResponse',
)({
  /**
   * List of projects
   */
  data: S.Array(ProjectDto),
}) {}

/**
 * Request model for creating a new project.
 */
export class ProjectCreateRequest extends S.Class<ProjectCreateRequest>(
  'ProjectCreateRequest',
)({
  /**
   * Name of the project
   */
  name: S.String,
  /**
   * Description of the project
   */
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * Language code (e.g., 'en', 'es', 'fr')
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

/**
 * Request model for updating a project.
 */
export class ProjectUpdateRequest extends S.Class<ProjectUpdateRequest>(
  'ProjectUpdateRequest',
)({
  /**
   * Name of the project
   */
  name: S.optionalWith(S.String, { nullable: true }),
  /**
   * Description of the project
   */
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * Language code (e.g., 'en', 'es', 'fr')
   */
  language_code: S.optionalWith(S.String, { nullable: true }),
}) {}

export class ListChatsV1ChatsGetParams extends S.Struct({
  project_id: S.String,
}) {}

/**
 * Response model for source document data.
 */
export class SourceDto extends S.Class<SourceDto>('SourceDto')({
  /**
   * Unique ID of the source segment
   */
  id: S.String,
  /**
   * Citation number for [n] references
   */
  citation_index: S.Int,
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
  /**
   * URL to preview/download the document
   */
  preview_url: S.optionalWith(S.String, { nullable: true }),
  /**
   * Relevance score of the source
   */
  score: S.Number,
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

/**
 * Response model for tool call data.
 */
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

/**
 * Response model for chat message data.
 */
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
   * Creation timestamp
   */
  created_at: S.String,
}) {}

/**
 * Response model for last chat message data.
 */
export class LastChatMessageDto extends S.Class<LastChatMessageDto>(
  'LastChatMessageDto',
)({
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
   * Creation timestamp
   */
  created_at: S.String,
}) {}

/**
 * Response model for chat data.
 */
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
  title: S.NullOr(S.String),
  /**
   * List of messages in the chat
   */
  messages: S.optionalWith(S.Array(ChatMessageDto), { nullable: true }),
  /**
   * Creation timestamp
   */
  created_at: S.String,
  /**
   * Last update timestamp
   */
  updated_at: S.String,
  /**
   * Last message in the chat
   */
  last_message: S.optionalWith(LastChatMessageDto, { nullable: true }),
}) {}

/**
 * Response model for listing chats.
 */
export class ChatListResponse extends S.Class<ChatListResponse>(
  'ChatListResponse',
)({
  /**
   * List of chats
   */
  data: S.Array(ChatDto),
}) {}

/**
 * Request model for creating a new chat.
 */
export class ChatCreateRequest extends S.Class<ChatCreateRequest>(
  'ChatCreateRequest',
)({
  /**
   * ID of the project this chat belongs to
   */
  project_id: S.String,
}) {}

/**
 * Request model for updating a chat.
 */
export class ChatUpdateRequest extends S.Class<ChatUpdateRequest>(
  'ChatUpdateRequest',
)({
  /**
   * Title of the chat
   */
  title: S.optionalWith(S.String, { nullable: true }),
}) {}

/**
 * Request model for chat completion with RAG.
 */
export class ChatCompletionRequest extends S.Class<ChatCompletionRequest>(
  'ChatCompletionRequest',
)({
  /**
   * User message to process
   */
  message: S.String,
}) {}

export class SendStreamingMessageV1ChatsChatIdMessagesStreamPost200 extends S.Struct(
  {},
) {}

export class UploadDocumentV1DocumentsUploadPostParams extends S.Struct({
  project_id: S.String,
}) {}

export class BodyUploadDocumentV1DocumentsUploadPost extends S.Class<BodyUploadDocumentV1DocumentsUploadPost>(
  'BodyUploadDocumentV1DocumentsUploadPost',
)({
  files: S.Array(S.instanceOf(globalThis.Blob)),
}) {}

export class DocumentUploadResponse extends S.Class<DocumentUploadResponse>(
  'DocumentUploadResponse',
)({
  /**
   * IDs of the uploaded documents
   */
  document_ids: S.Array(S.String),
}) {}

export class ListDocumentsV1DocumentsGetParams extends S.Struct({
  project_id: S.String,
}) {}

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
  id: S.String,
  owner_id: S.String,
  project_id: S.NullOr(S.String),
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
   * Auto-generated summary
   */
  summary: S.optionalWith(S.String, { nullable: true }),
  uploaded_at: S.String,
  processed_at: S.NullOr(S.String),
}) {}

export class DocumentListResponse extends S.Class<DocumentListResponse>(
  'DocumentListResponse',
)({
  /**
   * List of documents
   */
  data: S.Array(DocumentDto),
}) {}

export class DocumentPreviewResponse extends S.Class<DocumentPreviewResponse>(
  'DocumentPreviewResponse',
)({
  /**
   * SAS URL for direct blob access
   */
  preview_url: S.String,
  /**
   * Content type of the document
   */
  content_type: S.String,
}) {}

export class StreamDocumentV1DocumentsDocumentIdStreamGet200 extends S.Struct(
  {},
) {}

export class ListFlashcardGroupsV1FlashcardsGetParams extends S.Struct({
  project_id: S.String,
}) {}

/**
 * Flashcard group data transfer object.
 */
export class FlashcardGroupDto extends S.Class<FlashcardGroupDto>(
  'FlashcardGroupDto',
)({
  id: S.String,
  project_id: S.String,
  name: S.String,
  description: S.optionalWith(S.String, { nullable: true }),
  spaced_repetition_enabled: S.optionalWith(S.Boolean, {
    nullable: true,
    default: () => false as const,
  }),
  created_at: S.String,
  updated_at: S.String,
}) {}

/**
 * Response model for listing flashcard groups.
 */
export class FlashcardGroupListResponse extends S.Class<FlashcardGroupListResponse>(
  'FlashcardGroupListResponse',
)({
  /**
   * List of flashcard groups
   */
  data: S.Array(FlashcardGroupDto),
}) {}

export class CreateFlashcardGroupV1FlashcardsPostParams extends S.Struct({
  project_id: S.String,
}) {}

/**
 * Request model for creating a flashcard group.
 */
export class CreateFlashcardGroupRequest extends S.Class<CreateFlashcardGroupRequest>(
  'CreateFlashcardGroupRequest',
)({
  /**
   * Number of flashcards to generate
   */
  flashcard_count: S.optionalWith(
    S.Int.pipe(S.greaterThanOrEqualTo(1), S.lessThanOrEqualTo(100)),
    { nullable: true, default: () => 30 as const },
  ),
  /**
   * Topic or custom instructions for flashcard generation. If provided, will filter documents by topic relevance.
   */
  user_prompt: S.optionalWith(S.String.pipe(S.maxLength(2000)), {
    nullable: true,
  }),
}) {}

/**
 * Response model for flashcard group operations.
 */
export class FlashcardGroupResponse extends S.Class<FlashcardGroupResponse>(
  'FlashcardGroupResponse',
)({
  flashcard_group: FlashcardGroupDto,
  message: S.String,
}) {}

/**
 * Flashcard data transfer object.
 */
export class FlashcardDto extends S.Class<FlashcardDto>('FlashcardDto')({
  id: S.String,
  group_id: S.String,
  project_id: S.String,
  question: S.String,
  answer: S.String,
  difficulty_level: S.String,
  created_at: S.String,
}) {}

/**
 * Response model for listing flashcards.
 */
export class FlashcardListResponse extends S.Class<FlashcardListResponse>(
  'FlashcardListResponse',
)({
  /**
   * List of flashcards
   */
  data: S.Array(FlashcardDto),
}) {}

export class GetDueFlashcardsV1FlashcardsGroupIdDueForReviewGetParams extends S.Struct(
  {
    /**
     * Maximum number of flashcards to return
     */
    limit: S.optionalWith(
      S.Int.pipe(S.greaterThanOrEqualTo(1), S.lessThanOrEqualTo(100)),
      { nullable: true },
    ),
  },
) {}

/**
 * Whether to enable spaced repetition
 */
export class ToggleSpacedRepetitionV1FlashcardsGroupIdSpacedRepetitionPatchRequest extends S.Boolean {}

export class ExportFlashcardGroupV1FlashcardsGroupIdExportGet200 extends S.Struct(
  {},
) {}

export class ListQuizzesV1QuizzesGetParams extends S.Struct({
  project_id: S.String,
}) {}

/**
 * Quiz data transfer object.
 */
export class QuizDto extends S.Class<QuizDto>('QuizDto')({
  id: S.String,
  project_id: S.String,
  name: S.String,
  description: S.optionalWith(S.String, { nullable: true }),
  created_at: S.String,
  updated_at: S.String,
}) {}

/**
 * Response model for listing quizzes.
 */
export class QuizListResponse extends S.Class<QuizListResponse>(
  'QuizListResponse',
)({
  /**
   * List of quizzes
   */
  data: S.Array(QuizDto),
}) {}

export class CreateQuizV1QuizzesPostParams extends S.Struct({
  project_id: S.String,
}) {}

/**
 * Request model for creating a quiz.
 */
export class CreateQuizRequest extends S.Class<CreateQuizRequest>(
  'CreateQuizRequest',
)({
  /**
   * Number of quiz questions to generate
   */
  question_count: S.optionalWith(
    S.Int.pipe(S.greaterThanOrEqualTo(1), S.lessThanOrEqualTo(100)),
    { nullable: true, default: () => 30 as const },
  ),
  /**
   * Topic or custom instructions for quiz generation. If provided, will filter documents by topic relevance.
   */
  user_prompt: S.optionalWith(S.String.pipe(S.maxLength(2000)), {
    nullable: true,
  }),
}) {}

/**
 * Response model for quiz operations.
 */
export class QuizResponse extends S.Class<QuizResponse>('QuizResponse')({
  quiz: QuizDto,
  message: S.String,
}) {}

/**
 * Quiz question data transfer object.
 */
export class QuizQuestionDto extends S.Class<QuizQuestionDto>(
  'QuizQuestionDto',
)({
  id: S.String,
  quiz_id: S.String,
  project_id: S.String,
  question_text: S.String,
  option_a: S.String,
  option_b: S.String,
  option_c: S.String,
  option_d: S.String,
  correct_option: S.String,
  explanation: S.optionalWith(S.String, { nullable: true }),
  difficulty_level: S.String,
  created_at: S.String,
}) {}

/**
 * Response model for listing quiz questions.
 */
export class QuizQuestionListResponse extends S.Class<QuizQuestionListResponse>(
  'QuizQuestionListResponse',
)({
  /**
   * List of quiz questions
   */
  data: S.Array(QuizQuestionDto),
}) {}

export class ExportQuizV1QuizzesQuizIdExportGet200 extends S.Struct({}) {}

export class ListNotesV1NotesGetParams extends S.Struct({
  project_id: S.String,
}) {}

/**
 * Note data transfer object.
 */
export class NoteDto extends S.Class<NoteDto>('NoteDto')({
  id: S.String,
  project_id: S.String,
  title: S.String,
  description: S.optionalWith(S.String, { nullable: true }),
  content: S.String,
  created_at: S.String,
  updated_at: S.String,
}) {}

/**
 * Response model for listing notes.
 */
export class NoteListResponse extends S.Class<NoteListResponse>(
  'NoteListResponse',
)({
  /**
   * List of notes
   */
  data: S.Array(NoteDto),
}) {}

export class CreateNoteV1NotesPostParams extends S.Struct({
  project_id: S.String,
}) {}

/**
 * Request model for creating a note.
 */
export class CreateNoteRequest extends S.Class<CreateNoteRequest>(
  'CreateNoteRequest',
)({
  /**
   * Topic or custom instructions for note generation. If provided, will filter documents by topic relevance.
   */
  user_prompt: S.optionalWith(S.String.pipe(S.maxLength(2000)), {
    nullable: true,
  }),
}) {}

/**
 * Response model for note operations.
 */
export class NoteResponse extends S.Class<NoteResponse>('NoteResponse')({
  note: NoteDto,
  message: S.String,
}) {}

/**
 * Request model for updating a note.
 */
export class UpdateNoteRequest extends S.Class<UpdateNoteRequest>(
  'UpdateNoteRequest',
)({
  /**
   * Title of the note
   */
  title: S.optionalWith(S.String.pipe(S.minLength(1), S.maxLength(255)), {
    nullable: true,
  }),
  /**
   * Description of the note
   */
  description: S.optionalWith(S.String.pipe(S.maxLength(1000)), {
    nullable: true,
  }),
  /**
   * Markdown content of the note
   */
  content: S.optionalWith(S.String.pipe(S.minLength(1)), { nullable: true }),
}) {}

export class ListPracticeRecordsV1PracticeRecordsGetParams extends S.Struct({
  /**
   * Optional project ID filter
   */
  project_id: S.optionalWith(S.String, { nullable: true }),
}) {}

/**
 * Practice record data transfer object.
 */
export class PracticeRecordDto extends S.Class<PracticeRecordDto>(
  'PracticeRecordDto',
)({
  id: S.String,
  user_id: S.String,
  project_id: S.String,
  item_type: S.String,
  item_id: S.String,
  topic: S.String,
  user_answer: S.optionalWith(S.String, { nullable: true }),
  correct_answer: S.String,
  was_correct: S.Boolean,
  created_at: S.String,
}) {}

/**
 * Response model for listing practice records.
 */
export class PracticeRecordListResponse extends S.Class<PracticeRecordListResponse>(
  'PracticeRecordListResponse',
)({
  /**
   * List of practice records
   */
  data: S.Array(PracticeRecordDto),
}) {}

export class CreatePracticeRecordV1PracticeRecordsPostParams extends S.Struct({
  project_id: S.String,
}) {}

/**
 * Request model for creating a practice record.
 */
export class CreatePracticeRecordRequest extends S.Class<CreatePracticeRecordRequest>(
  'CreatePracticeRecordRequest',
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
  /**
   * Quality rating for spaced repetition (0-5). Only for flashcards with SR enabled.
   */
  quality_rating: S.optionalWith(
    S.Int.pipe(S.greaterThanOrEqualTo(0), S.lessThanOrEqualTo(5)),
    { nullable: true },
  ),
}) {}

/**
 * Response model for practice record operations.
 */
export class PracticeRecordResponse extends S.Class<PracticeRecordResponse>(
  'PracticeRecordResponse',
)({
  practice_record: PracticeRecordDto,
  message: S.String,
}) {}

export class CreatePracticeRecordsBatchV1PracticeRecordsBatchPostParams extends S.Struct(
  {
    project_id: S.String,
  },
) {}

/**
 * Request model for creating multiple practice records.
 */
export class CreatePracticeRecordBatchRequest extends S.Class<CreatePracticeRecordBatchRequest>(
  'CreatePracticeRecordBatchRequest',
)({
  /**
   * List of practice records to create
   */
  practice_records: S.NonEmptyArray(CreatePracticeRecordRequest).pipe(
    S.minItems(1),
    S.maxItems(100),
  ),
}) {}

export class UserDto extends S.Class<UserDto>('UserDto')({
  id: S.String,
  name: S.optionalWith(S.String, { nullable: true }),
  email: S.optionalWith(S.String, { nullable: true }),
  azure_oid: S.optionalWith(S.String, { nullable: true }),
  created_at: S.String,
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
   * Document upload usage statistics
   */
  document_uploads: UsageLimitDto,
}) {}

/**
 * Response model for usage statistics.
 */
export class UsageResponse extends S.Class<UsageResponse>('UsageResponse')({
  /**
   * User usage statistics
   */
  usage: UsageDto,
}) {}

/**
 * Mind map data transfer object.
 */
export class MindMapDto extends S.Class<MindMapDto>('MindMapDto')({
  id: S.String,
  user_id: S.String,
  project_id: S.String,
  title: S.String,
  description: S.optionalWith(S.String, { nullable: true }),
  /**
   * Structured mind map data (nodes, edges)
   */
  map_data: S.Record({ key: S.String, value: S.Unknown }),
  generated_at: S.String,
  updated_at: S.String,
}) {}

/**
 * Response model for listing mind maps.
 */
export class MindMapListResponse extends S.Class<MindMapListResponse>(
  'MindMapListResponse',
)({
  data: S.Array(MindMapDto),
}) {}

/**
 * Request model for creating a mind map.
 */
export class CreateMindMapRequest extends S.Class<CreateMindMapRequest>(
  'CreateMindMapRequest',
)({
  /**
   * Optional user instructions (topic or focus area)
   */
  user_prompt: S.optionalWith(S.String, { nullable: true }),
}) {}

export class ListStudySessionsV1ProjectsProjectIdStudySessionsGetParams extends S.Struct(
  {
    limit: S.optionalWith(
      S.Int.pipe(S.greaterThanOrEqualTo(1), S.lessThanOrEqualTo(100)),
      { nullable: true, default: () => 50 as const },
    ),
  },
) {}

export class StudySessionResponse extends S.Class<StudySessionResponse>(
  'StudySessionResponse',
)({
  session_id: S.String,
  flashcard_group_id: S.optionalWith(S.String, { nullable: true }),
  flashcards: S.Array(S.Record({ key: S.String, value: S.Unknown })),
  estimated_time_minutes: S.Int,
  focus_topics: S.Array(S.String),
  learning_objectives: S.Array(S.String),
  generated_at: S.String,
}) {}

export class ListStudySessionsV1ProjectsProjectIdStudySessionsGet200 extends S.Array(
  StudySessionResponse,
) {}

export class GenerateStudySessionV1ProjectsProjectIdStudySessionsPostParams extends S.Struct(
  {
    session_length_minutes: S.optionalWith(
      S.Int.pipe(S.greaterThanOrEqualTo(10), S.lessThanOrEqualTo(120)),
      { nullable: true, default: () => 30 as const },
    ),
    focus_topics: S.optionalWith(S.Array(S.String), { nullable: true }),
  },
) {}

export class BodyImportFlashcardGroupV1ProjectsProjectIdFlashcardGroupsImportPost extends S.Class<BodyImportFlashcardGroupV1ProjectsProjectIdFlashcardGroupsImportPost>(
  'BodyImportFlashcardGroupV1ProjectsProjectIdFlashcardGroupsImportPost',
)({
  file: S.instanceOf(globalThis.Blob),
  group_name: S.String,
  group_description: S.optionalWith(S.String, { nullable: true }),
}) {}

export class ImportResponse extends S.Class<ImportResponse>('ImportResponse')({
  id: S.String,
}) {}

export class BodyImportQuizV1ProjectsProjectIdQuizzesImportPost extends S.Class<BodyImportQuizV1ProjectsProjectIdQuizzesImportPost>(
  'BodyImportQuizV1ProjectsProjectIdQuizzesImportPost',
)({
  file: S.instanceOf(globalThis.Blob),
  quiz_name: S.String,
  quiz_description: S.optionalWith(S.String, { nullable: true }),
}) {}

export class HealthCheckHealthGet200 extends S.Struct({}) {}

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
    listProjectsV1ProjectsGet: () =>
      HttpClientRequest.get(`/v1/projects`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ProjectListResponse),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createProjectV1ProjectsPost: (options) =>
      HttpClientRequest.post(`/v1/projects`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ProjectDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getProjectV1ProjectsProjectIdGet: (projectId) =>
      HttpClientRequest.get(`/v1/projects/${projectId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ProjectDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    updateProjectV1ProjectsProjectIdPut: (projectId, options) =>
      HttpClientRequest.put(`/v1/projects/${projectId}`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ProjectDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteProjectV1ProjectsProjectIdDeletePost: (projectId) =>
      HttpClientRequest.post(`/v1/projects/${projectId}/delete`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listChatsV1ChatsGet: (options) =>
      HttpClientRequest.get(`/v1/chats`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options?.['project_id'] as any,
        }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ChatListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createChatV1ChatsPost: (options) =>
      HttpClientRequest.post(`/v1/chats`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ChatDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getChatV1ChatsChatIdGet: (chatId) =>
      HttpClientRequest.get(`/v1/chats/${chatId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ChatDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    updateChatV1ChatsChatIdPut: (chatId, options) =>
      HttpClientRequest.put(`/v1/chats/${chatId}`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ChatDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteChatV1ChatsChatIdDeletePost: (chatId) =>
      HttpClientRequest.post(`/v1/chats/${chatId}/delete`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    sendStreamingMessageV1ChatsChatIdMessagesStreamPost: (chatId, options) =>
      HttpClientRequest.post(`/v1/chats/${chatId}/messages/stream`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              SendStreamingMessageV1ChatsChatIdMessagesStreamPost200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    uploadDocumentV1DocumentsUploadPost: (options) =>
      HttpClientRequest.post(`/v1/documents/upload`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options.params?.['project_id'] as any,
        }),
        HttpClientRequest.bodyFormDataRecord(options.payload as any),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(DocumentUploadResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listDocumentsV1DocumentsGet: (options) =>
      HttpClientRequest.get(`/v1/documents`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options?.['project_id'] as any,
        }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(DocumentListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getDocumentV1DocumentsDocumentIdGet: (documentId) =>
      HttpClientRequest.get(`/v1/documents/${documentId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(DocumentDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteDocumentV1DocumentsDocumentIdDelete: (documentId) =>
      HttpClientRequest.del(`/v1/documents/${documentId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    previewDocumentV1DocumentsDocumentIdPreviewGet: (documentId) =>
      HttpClientRequest.get(`/v1/documents/${documentId}/preview`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(DocumentPreviewResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    streamDocumentV1DocumentsDocumentIdStreamGet: (documentId) =>
      HttpClientRequest.get(`/v1/documents/${documentId}/stream`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              StreamDocumentV1DocumentsDocumentIdStreamGet200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listFlashcardGroupsV1FlashcardsGet: (options) =>
      HttpClientRequest.get(`/v1/flashcards`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options?.['project_id'] as any,
        }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(FlashcardGroupListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createFlashcardGroupV1FlashcardsPost: (options) =>
      HttpClientRequest.post(`/v1/flashcards`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options.params?.['project_id'] as any,
        }),
        HttpClientRequest.bodyUnsafeJson(options.payload),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(FlashcardGroupResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getFlashcardGroupV1FlashcardsGroupIdGet: (groupId) =>
      HttpClientRequest.get(`/v1/flashcards/${groupId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(FlashcardGroupResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteFlashcardGroupV1FlashcardsGroupIdDelete: (groupId) =>
      HttpClientRequest.del(`/v1/flashcards/${groupId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listFlashcardsV1FlashcardsGroupIdFlashcardsGet: (groupId) =>
      HttpClientRequest.get(`/v1/flashcards/${groupId}/flashcards`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(FlashcardListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getDueFlashcardsV1FlashcardsGroupIdDueForReviewGet: (groupId, options) =>
      HttpClientRequest.get(`/v1/flashcards/${groupId}/due-for-review`).pipe(
        HttpClientRequest.setUrlParams({ limit: options?.['limit'] as any }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(FlashcardListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    toggleSpacedRepetitionV1FlashcardsGroupIdSpacedRepetitionPatch: (
      groupId,
      options,
    ) =>
      HttpClientRequest.patch(
        `/v1/flashcards/${groupId}/spaced-repetition`,
      ).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(FlashcardGroupResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    exportFlashcardGroupV1FlashcardsGroupIdExportGet: (groupId) =>
      HttpClientRequest.get(`/v1/flashcards/${groupId}/export`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              ExportFlashcardGroupV1FlashcardsGroupIdExportGet200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listQuizzesV1QuizzesGet: (options) =>
      HttpClientRequest.get(`/v1/quizzes`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options?.['project_id'] as any,
        }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(QuizListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createQuizV1QuizzesPost: (options) =>
      HttpClientRequest.post(`/v1/quizzes`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options.params?.['project_id'] as any,
        }),
        HttpClientRequest.bodyUnsafeJson(options.payload),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(QuizResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getQuizV1QuizzesQuizIdGet: (quizId) =>
      HttpClientRequest.get(`/v1/quizzes/${quizId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(QuizResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteQuizV1QuizzesQuizIdDelete: (quizId) =>
      HttpClientRequest.del(`/v1/quizzes/${quizId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listQuizQuestionsV1QuizzesQuizIdQuestionsGet: (quizId) =>
      HttpClientRequest.get(`/v1/quizzes/${quizId}/questions`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(QuizQuestionListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    exportQuizV1QuizzesQuizIdExportGet: (quizId) =>
      HttpClientRequest.get(`/v1/quizzes/${quizId}/export`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ExportQuizV1QuizzesQuizIdExportGet200),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listNotesV1NotesGet: (options) =>
      HttpClientRequest.get(`/v1/notes`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options?.['project_id'] as any,
        }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(NoteListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createNoteV1NotesPost: (options) =>
      HttpClientRequest.post(`/v1/notes`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options.params?.['project_id'] as any,
        }),
        HttpClientRequest.bodyUnsafeJson(options.payload),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(NoteResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getNoteV1NotesNoteIdGet: (noteId) =>
      HttpClientRequest.get(`/v1/notes/${noteId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(NoteResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    updateNoteV1NotesNoteIdPut: (noteId, options) =>
      HttpClientRequest.put(`/v1/notes/${noteId}`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(NoteResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    deleteNoteV1NotesNoteIdDelete: (noteId) =>
      HttpClientRequest.del(`/v1/notes/${noteId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listPracticeRecordsV1PracticeRecordsGet: (options) =>
      HttpClientRequest.get(`/v1/practice-records`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options?.['project_id'] as any,
        }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(PracticeRecordListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createPracticeRecordV1PracticeRecordsPost: (options) =>
      HttpClientRequest.post(`/v1/practice-records`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options.params?.['project_id'] as any,
        }),
        HttpClientRequest.bodyUnsafeJson(options.payload),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(PracticeRecordResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createPracticeRecordsBatchV1PracticeRecordsBatchPost: (options) =>
      HttpClientRequest.post(`/v1/practice-records/batch`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options.params?.['project_id'] as any,
        }),
        HttpClientRequest.bodyUnsafeJson(options.payload),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(PracticeRecordListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getCurrentUserInfoV1AuthMeGet: () =>
      HttpClientRequest.get(`/v1/auth/me`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(UserDto),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getUsageV1UsageGet: () =>
      HttpClientRequest.get(`/v1/usage`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(UsageResponse),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listMindMapsV1ProjectsProjectIdMindMapsGet: (projectId) =>
      HttpClientRequest.get(`/v1/projects/${projectId}/mind-maps`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(MindMapListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    generateMindMapV1ProjectsProjectIdMindMapsPost: (projectId, options) =>
      HttpClientRequest.post(`/v1/projects/${projectId}/mind-maps`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(MindMapDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getMindMapV1MindMapsMindMapIdGet: (mindMapId) =>
      HttpClientRequest.get(`/v1/mind-maps/${mindMapId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(MindMapDto),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listStudySessionsV1ProjectsProjectIdStudySessionsGet: (
      projectId,
      options,
    ) =>
      HttpClientRequest.get(`/v1/projects/${projectId}/study-sessions`).pipe(
        HttpClientRequest.setUrlParams({ limit: options?.['limit'] as any }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              ListStudySessionsV1ProjectsProjectIdStudySessionsGet200,
            ),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    generateStudySessionV1ProjectsProjectIdStudySessionsPost: (
      projectId,
      options,
    ) =>
      HttpClientRequest.post(`/v1/projects/${projectId}/study-sessions`).pipe(
        HttpClientRequest.setUrlParams({
          session_length_minutes: options?.['session_length_minutes'] as any,
          focus_topics: options?.['focus_topics'] as any,
        }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(StudySessionResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    getStudySessionV1StudySessionsSessionIdGet: (sessionId) =>
      HttpClientRequest.get(`/v1/study-sessions/${sessionId}`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(StudySessionResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    importFlashcardGroupV1ProjectsProjectIdFlashcardGroupsImportPost: (
      projectId,
      options,
    ) =>
      HttpClientRequest.post(
        `/v1/projects/${projectId}/flashcard-groups/import`,
      ).pipe(
        HttpClientRequest.bodyFormDataRecord(options as any),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ImportResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    importQuizV1ProjectsProjectIdQuizzesImportPost: (projectId, options) =>
      HttpClientRequest.post(`/v1/projects/${projectId}/quizzes/import`).pipe(
        HttpClientRequest.bodyFormDataRecord(options as any),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ImportResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    healthCheckHealthGet: () =>
      HttpClientRequest.get(`/health`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(HealthCheckHealthGet200),
            orElse: unexpectedStatus,
          }),
        ),
      ),
  }
}

export interface Client {
  readonly httpClient: HttpClient.HttpClient
  /**
   * List all projects
   */
  readonly listProjectsV1ProjectsGet: () => Effect.Effect<
    typeof ProjectListResponse.Type,
    HttpClientError.HttpClientError | ParseError
  >
  /**
   * Create a new project
   */
  readonly createProjectV1ProjectsPost: (
    options: typeof ProjectCreateRequest.Encoded,
  ) => Effect.Effect<
    typeof ProjectDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a project by id
   */
  readonly getProjectV1ProjectsProjectIdGet: (
    projectId: string,
  ) => Effect.Effect<
    typeof ProjectDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Update a project
   */
  readonly updateProjectV1ProjectsProjectIdPut: (
    projectId: string,
    options: typeof ProjectUpdateRequest.Encoded,
  ) => Effect.Effect<
    typeof ProjectDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a project by id
   */
  readonly deleteProjectV1ProjectsProjectIdDeletePost: (
    projectId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all chats
   */
  readonly listChatsV1ChatsGet: (
    options: typeof ListChatsV1ChatsGetParams.Encoded,
  ) => Effect.Effect<
    typeof ChatListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new project
   */
  readonly createChatV1ChatsPost: (
    options: typeof ChatCreateRequest.Encoded,
  ) => Effect.Effect<
    typeof ChatDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a chat by id
   */
  readonly getChatV1ChatsChatIdGet: (
    chatId: string,
  ) => Effect.Effect<
    typeof ChatDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Update a chat by id
   */
  readonly updateChatV1ChatsChatIdPut: (
    chatId: string,
    options: typeof ChatUpdateRequest.Encoded,
  ) => Effect.Effect<
    typeof ChatDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a chat by id
   */
  readonly deleteChatV1ChatsChatIdDeletePost: (
    chatId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Send a message to a chat with streaming response
   */
  readonly sendStreamingMessageV1ChatsChatIdMessagesStreamPost: (
    chatId: string,
    options: typeof ChatCompletionRequest.Encoded,
  ) => Effect.Effect<
    typeof SendStreamingMessageV1ChatsChatIdMessagesStreamPost200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Upload one or more documents for the project. Processing happens asynchronously.
   */
  readonly uploadDocumentV1DocumentsUploadPost: (options: {
    readonly params: typeof UploadDocumentV1DocumentsUploadPostParams.Encoded
    readonly payload: typeof BodyUploadDocumentV1DocumentsUploadPost.Encoded
  }) => Effect.Effect<
    typeof DocumentUploadResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all documents for a project
   */
  readonly listDocumentsV1DocumentsGet: (
    options: typeof ListDocumentsV1DocumentsGetParams.Encoded,
  ) => Effect.Effect<
    typeof DocumentListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a document by id
   */
  readonly getDocumentV1DocumentsDocumentIdGet: (
    documentId: string,
  ) => Effect.Effect<
    typeof DocumentDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a document by id
   */
  readonly deleteDocumentV1DocumentsDocumentIdDelete: (
    documentId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a URL for previewing the document (streamed through backend with inline disposition)
   */
  readonly previewDocumentV1DocumentsDocumentIdPreviewGet: (
    documentId: string,
  ) => Effect.Effect<
    typeof DocumentPreviewResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Stream document content with Content-Disposition: inline for browser preview
   */
  readonly streamDocumentV1DocumentsDocumentIdStreamGet: (
    documentId: string,
  ) => Effect.Effect<
    typeof StreamDocumentV1DocumentsDocumentIdStreamGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all flashcard groups for a project
   */
  readonly listFlashcardGroupsV1FlashcardsGet: (
    options: typeof ListFlashcardGroupsV1FlashcardsGetParams.Encoded,
  ) => Effect.Effect<
    typeof FlashcardGroupListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new flashcard group with AI-generated flashcards
   */
  readonly createFlashcardGroupV1FlashcardsPost: (options: {
    readonly params: typeof CreateFlashcardGroupV1FlashcardsPostParams.Encoded
    readonly payload: typeof CreateFlashcardGroupRequest.Encoded
  }) => Effect.Effect<
    typeof FlashcardGroupResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a specific flashcard group by ID
   */
  readonly getFlashcardGroupV1FlashcardsGroupIdGet: (
    groupId: string,
  ) => Effect.Effect<
    typeof FlashcardGroupResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a flashcard group and all its flashcards
   */
  readonly deleteFlashcardGroupV1FlashcardsGroupIdDelete: (
    groupId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all flashcards in a group
   */
  readonly listFlashcardsV1FlashcardsGroupIdFlashcardsGet: (
    groupId: string,
  ) => Effect.Effect<
    typeof FlashcardListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get flashcards that are due for review based on spaced repetition algorithm
   */
  readonly getDueFlashcardsV1FlashcardsGroupIdDueForReviewGet: (
    groupId: string,
    options?:
      | typeof GetDueFlashcardsV1FlashcardsGroupIdDueForReviewGetParams.Encoded
      | undefined,
  ) => Effect.Effect<
    typeof FlashcardListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Enable or disable spaced repetition for a flashcard group
   */
  readonly toggleSpacedRepetitionV1FlashcardsGroupIdSpacedRepetitionPatch: (
    groupId: string,
    options: typeof ToggleSpacedRepetitionV1FlashcardsGroupIdSpacedRepetitionPatchRequest.Encoded,
  ) => Effect.Effect<
    typeof FlashcardGroupResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Export a flashcard group to CSV format
   */
  readonly exportFlashcardGroupV1FlashcardsGroupIdExportGet: (
    groupId: string,
  ) => Effect.Effect<
    typeof ExportFlashcardGroupV1FlashcardsGroupIdExportGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all quizzes for a project
   */
  readonly listQuizzesV1QuizzesGet: (
    options: typeof ListQuizzesV1QuizzesGetParams.Encoded,
  ) => Effect.Effect<
    typeof QuizListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new quiz with AI-generated questions
   */
  readonly createQuizV1QuizzesPost: (options: {
    readonly params: typeof CreateQuizV1QuizzesPostParams.Encoded
    readonly payload: typeof CreateQuizRequest.Encoded
  }) => Effect.Effect<
    typeof QuizResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a specific quiz by ID
   */
  readonly getQuizV1QuizzesQuizIdGet: (
    quizId: string,
  ) => Effect.Effect<
    typeof QuizResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a quiz and all its questions
   */
  readonly deleteQuizV1QuizzesQuizIdDelete: (
    quizId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all questions in a quiz
   */
  readonly listQuizQuestionsV1QuizzesQuizIdQuestionsGet: (
    quizId: string,
  ) => Effect.Effect<
    typeof QuizQuestionListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Export a quiz to CSV format
   */
  readonly exportQuizV1QuizzesQuizIdExportGet: (
    quizId: string,
  ) => Effect.Effect<
    typeof ExportQuizV1QuizzesQuizIdExportGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all notes for a project
   */
  readonly listNotesV1NotesGet: (
    options: typeof ListNotesV1NotesGetParams.Encoded,
  ) => Effect.Effect<
    typeof NoteListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new note with AI-generated markdown content
   */
  readonly createNoteV1NotesPost: (options: {
    readonly params: typeof CreateNoteV1NotesPostParams.Encoded
    readonly payload: typeof CreateNoteRequest.Encoded
  }) => Effect.Effect<
    typeof NoteResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a specific note by ID
   */
  readonly getNoteV1NotesNoteIdGet: (
    noteId: string,
  ) => Effect.Effect<
    typeof NoteResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Update a note
   */
  readonly updateNoteV1NotesNoteIdPut: (
    noteId: string,
    options: typeof UpdateNoteRequest.Encoded,
  ) => Effect.Effect<
    typeof NoteResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Delete a note
   */
  readonly deleteNoteV1NotesNoteIdDelete: (
    noteId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List practice records for the current user, optionally filtered by project
   */
  readonly listPracticeRecordsV1PracticeRecordsGet: (
    options?:
      | typeof ListPracticeRecordsV1PracticeRecordsGetParams.Encoded
      | undefined,
  ) => Effect.Effect<
    typeof PracticeRecordListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new practice record for a flashcard or quiz question
   */
  readonly createPracticeRecordV1PracticeRecordsPost: (options: {
    readonly params: typeof CreatePracticeRecordV1PracticeRecordsPostParams.Encoded
    readonly payload: typeof CreatePracticeRecordRequest.Encoded
  }) => Effect.Effect<
    typeof PracticeRecordResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create multiple practice records in a single batch operation
   */
  readonly createPracticeRecordsBatchV1PracticeRecordsBatchPost: (options: {
    readonly params: typeof CreatePracticeRecordsBatchV1PracticeRecordsBatchPostParams.Encoded
    readonly payload: typeof CreatePracticeRecordBatchRequest.Encoded
  }) => Effect.Effect<
    typeof PracticeRecordListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get authenticated user information (requires auth)
   */
  readonly getCurrentUserInfoV1AuthMeGet: () => Effect.Effect<
    typeof UserDto.Type,
    HttpClientError.HttpClientError | ParseError
  >
  /**
   * Get current usage statistics for the authenticated user
   */
  readonly getUsageV1UsageGet: () => Effect.Effect<
    typeof UsageResponse.Type,
    HttpClientError.HttpClientError | ParseError
  >
  /**
   * List all mind maps for a project
   */
  readonly listMindMapsV1ProjectsProjectIdMindMapsGet: (
    projectId: string,
  ) => Effect.Effect<
    typeof MindMapListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Generate a new mind map from project documents
   */
  readonly generateMindMapV1ProjectsProjectIdMindMapsPost: (
    projectId: string,
    options: typeof CreateMindMapRequest.Encoded,
  ) => Effect.Effect<
    typeof MindMapDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a specific mind map by ID
   */
  readonly getMindMapV1MindMapsMindMapIdGet: (
    mindMapId: string,
  ) => Effect.Effect<
    typeof MindMapDto.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all study sessions for a project
   */
  readonly listStudySessionsV1ProjectsProjectIdStudySessionsGet: (
    projectId: string,
    options?:
      | typeof ListStudySessionsV1ProjectsProjectIdStudySessionsGetParams.Encoded
      | undefined,
  ) => Effect.Effect<
    typeof ListStudySessionsV1ProjectsProjectIdStudySessionsGet200.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Generate a personalized study session based on performance and spaced repetition
   */
  readonly generateStudySessionV1ProjectsProjectIdStudySessionsPost: (
    projectId: string,
    options?:
      | typeof GenerateStudySessionV1ProjectsProjectIdStudySessionsPostParams.Encoded
      | undefined,
  ) => Effect.Effect<
    typeof StudySessionResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Get a study session by ID
   */
  readonly getStudySessionV1StudySessionsSessionIdGet: (
    sessionId: string,
  ) => Effect.Effect<
    typeof StudySessionResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Import flashcards from CSV file
   */
  readonly importFlashcardGroupV1ProjectsProjectIdFlashcardGroupsImportPost: (
    projectId: string,
    options: typeof BodyImportFlashcardGroupV1ProjectsProjectIdFlashcardGroupsImportPost.Encoded,
  ) => Effect.Effect<
    typeof ImportResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Import quiz from CSV file
   */
  readonly importQuizV1ProjectsProjectIdQuizzesImportPost: (
    projectId: string,
    options: typeof BodyImportQuizV1ProjectsProjectIdQuizzesImportPost.Encoded,
  ) => Effect.Effect<
    typeof ImportResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Simple health check that doesn't require database
   */
  readonly healthCheckHealthGet: () => Effect.Effect<
    typeof HealthCheckHealthGet200.Type,
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
