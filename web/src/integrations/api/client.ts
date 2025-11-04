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
  /**
   * Total number of projects
   */
  total_count: S.Int,
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
  output: S.optionalWith(S.Record({ key: S.String, value: S.Unknown }), {
    nullable: true,
  }),
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
  /**
   * Total number of chats
   */
  total_count: S.Int,
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

export class ListChatMessagesV1ChatsChatIdMessagesGet200 extends S.Array(
  ChatMessageDto,
) {}

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
  file: S.instanceOf(globalThis.Blob),
}) {}

export class DocumentUploadResponse extends S.Class<DocumentUploadResponse>(
  'DocumentUploadResponse',
)({
  /**
   * ID of the uploaded document
   */
  document_id: S.String,
}) {}

export class ListDocumentsV1DocumentsGetParams extends S.Struct({
  project_id: S.String,
}) {}

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
  status: S.String,
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
  data: S.Array(DocumentDto),
  total_count: S.Int.pipe(S.greaterThanOrEqualTo(0)),
}) {}

export class DocumentSearchRequest extends S.Class<DocumentSearchRequest>(
  'DocumentSearchRequest',
)({
  /**
   * Search query
   */
  query: S.String.pipe(S.minLength(1)),
  /**
   * Project ID to search within
   */
  project_id: S.String,
  /**
   * Number of results to return
   */
  top_k: S.optionalWith(
    S.Int.pipe(S.greaterThanOrEqualTo(1), S.lessThanOrEqualTo(50)),
    { nullable: true, default: () => 5 as const },
  ),
}) {}

export class SearchResultDto extends S.Class<SearchResultDto>(
  'SearchResultDto',
)({
  /**
   * Citation number
   */
  citation_index: S.Int.pipe(S.greaterThanOrEqualTo(1)),
  /**
   * Document ID
   */
  document_id: S.String,
  /**
   * Document title
   */
  title: S.String,
  /**
   * Relevant content excerpt
   */
  content: S.String,
  /**
   * Relevance score
   */
  score: S.Number.pipe(S.greaterThanOrEqualTo(0), S.lessThanOrEqualTo(1)),
}) {}

export class DocumentSearchResponse extends S.Class<DocumentSearchResponse>(
  'DocumentSearchResponse',
)({
  results: S.Array(SearchResultDto),
  total_count: S.Int.pipe(S.greaterThanOrEqualTo(0)),
  query: S.String,
}) {}

export class PreviewDocumentV1DocumentsDocumentIdPreviewGet200 extends S.Struct(
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
  created_at: S.String,
  updated_at: S.String,
}) {}

/**
 * Response model for listing flashcard groups.
 */
export class FlashcardGroupListResponse extends S.Class<FlashcardGroupListResponse>(
  'FlashcardGroupListResponse',
)({
  data: S.Array(FlashcardGroupDto),
  total: S.Int,
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
   * Custom prompt to enhance generation
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
 * Request model for updating a flashcard group.
 */
export class UpdateFlashcardGroupRequest extends S.Class<UpdateFlashcardGroupRequest>(
  'UpdateFlashcardGroupRequest',
)({
  /**
   * Name of the flashcard group
   */
  name: S.optionalWith(S.String.pipe(S.minLength(1), S.maxLength(255)), {
    nullable: true,
  }),
  /**
   * Description of the flashcard group
   */
  description: S.optionalWith(S.String.pipe(S.maxLength(1000)), {
    nullable: true,
  }),
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
  flashcards: S.Array(FlashcardDto),
  total: S.Int,
}) {}

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
  data: S.Array(QuizDto),
  total: S.Int,
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
   * Custom prompt to enhance generation
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
 * Request model for updating a quiz.
 */
export class UpdateQuizRequest extends S.Class<UpdateQuizRequest>(
  'UpdateQuizRequest',
)({
  /**
   * Name of the quiz
   */
  name: S.optionalWith(S.String.pipe(S.minLength(1), S.maxLength(255)), {
    nullable: true,
  }),
  /**
   * Description of the quiz
   */
  description: S.optionalWith(S.String.pipe(S.maxLength(1000)), {
    nullable: true,
  }),
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
  quiz_questions: S.Array(QuizQuestionDto),
  total: S.Int,
}) {}

export class ListAttemptsV1AttemptsGetParams extends S.Struct({
  /**
   * Optional project ID filter
   */
  project_id: S.optionalWith(S.String, { nullable: true }),
}) {}

/**
 * Attempt data transfer object.
 */
export class AttemptDto extends S.Class<AttemptDto>('AttemptDto')({
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
 * Response model for listing attempts.
 */
export class AttemptListResponse extends S.Class<AttemptListResponse>(
  'AttemptListResponse',
)({
  attempts: S.Array(AttemptDto),
  total: S.Int,
}) {}

export class CreateAttemptV1AttemptsPostParams extends S.Struct({
  project_id: S.String,
}) {}

/**
 * Request model for creating an attempt record.
 */
export class CreateAttemptRequest extends S.Class<CreateAttemptRequest>(
  'CreateAttemptRequest',
)({
  /**
   * Type of item: flashcard or quiz
   */
  item_type: S.String.pipe(S.pattern(new RegExp('^(flashcard|quiz)$'))),
  /**
   * ID of the flashcard or quiz question
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

/**
 * Response model for attempt operations.
 */
export class AttemptResponse extends S.Class<AttemptResponse>(
  'AttemptResponse',
)({
  attempt: AttemptDto,
  message: S.String,
}) {}

export class CreateAttemptsBatchV1AttemptsBatchPostParams extends S.Struct({
  project_id: S.String,
}) {}

/**
 * Request model for creating multiple attempt records.
 */
export class CreateAttemptBatchRequest extends S.Class<CreateAttemptBatchRequest>(
  'CreateAttemptBatchRequest',
)({
  /**
   * List of attempts to create
   */
  attempts: S.NonEmptyArray(CreateAttemptRequest).pipe(
    S.minItems(1),
    S.maxItems(100),
  ),
}) {}

export class UserDto extends S.Class<UserDto>('UserDto')({
  id: S.String,
  name: S.String,
  email: S.String,
  azure_oid: S.String,
  created_at: S.String,
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
    archiveProjectV1ProjectsProjectIdArchivePost: (projectId) =>
      HttpClientRequest.post(`/v1/projects/${projectId}/archive`).pipe(
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
    archiveChatV1ChatsChatIdArchivePost: (chatId) =>
      HttpClientRequest.post(`/v1/chats/${chatId}/archive`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            '204': () => Effect.void,
            orElse: unexpectedStatus,
          }),
        ),
      ),
    listChatMessagesV1ChatsChatIdMessagesGet: (chatId) =>
      HttpClientRequest.get(`/v1/chats/${chatId}/messages`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(ListChatMessagesV1ChatsChatIdMessagesGet200),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
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
    searchDocumentsV1DocumentsSearchPost: (options) =>
      HttpClientRequest.post(`/v1/documents/search`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(DocumentSearchResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    previewDocumentV1DocumentsDocumentIdPreviewGet: (documentId) =>
      HttpClientRequest.get(`/v1/documents/${documentId}/preview`).pipe(
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(
              PreviewDocumentV1DocumentsDocumentIdPreviewGet200,
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
    updateFlashcardGroupV1FlashcardsGroupIdPut: (groupId, options) =>
      HttpClientRequest.put(`/v1/flashcards/${groupId}`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
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
    updateQuizV1QuizzesQuizIdPut: (quizId, options) =>
      HttpClientRequest.put(`/v1/quizzes/${quizId}`).pipe(
        HttpClientRequest.bodyUnsafeJson(options),
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
    listAttemptsV1AttemptsGet: (options) =>
      HttpClientRequest.get(`/v1/attempts`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options?.['project_id'] as any,
        }),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(AttemptListResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createAttemptV1AttemptsPost: (options) =>
      HttpClientRequest.post(`/v1/attempts`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options.params?.['project_id'] as any,
        }),
        HttpClientRequest.bodyUnsafeJson(options.payload),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(AttemptResponse),
            '422': decodeError('HTTPValidationError', HTTPValidationError),
            orElse: unexpectedStatus,
          }),
        ),
      ),
    createAttemptsBatchV1AttemptsBatchPost: (options) =>
      HttpClientRequest.post(`/v1/attempts/batch`).pipe(
        HttpClientRequest.setUrlParams({
          project_id: options.params?.['project_id'] as any,
        }),
        HttpClientRequest.bodyUnsafeJson(options.payload),
        withResponse(
          HttpClientResponse.matchStatus({
            '2xx': decodeSuccess(AttemptListResponse),
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
   * Update a project by id
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
   * Archive a project by id
   */
  readonly archiveProjectV1ProjectsProjectIdArchivePost: (
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
   * Archive a chat by id
   */
  readonly archiveChatV1ChatsChatIdArchivePost: (
    chatId: string,
  ) => Effect.Effect<
    void,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * List all messages in a chat with sources
   */
  readonly listChatMessagesV1ChatsChatIdMessagesGet: (
    chatId: string,
  ) => Effect.Effect<
    typeof ListChatMessagesV1ChatsChatIdMessagesGet200.Type,
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
   * Upload and process a document for the project
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
   * Search documents within a project using semantic search
   */
  readonly searchDocumentsV1DocumentsSearchPost: (
    options: typeof DocumentSearchRequest.Encoded,
  ) => Effect.Effect<
    typeof DocumentSearchResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Stream document content for preview in browser
   */
  readonly previewDocumentV1DocumentsDocumentIdPreviewGet: (
    documentId: string,
  ) => Effect.Effect<
    typeof PreviewDocumentV1DocumentsDocumentIdPreviewGet200.Type,
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
   * Create a new flashcard group for a project, optionally with generated flashcards
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
   * Update a flashcard group
   */
  readonly updateFlashcardGroupV1FlashcardsGroupIdPut: (
    groupId: string,
    options: typeof UpdateFlashcardGroupRequest.Encoded,
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
   * Create a new quiz for a project, optionally with generated questions
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
   * Update a quiz
   */
  readonly updateQuizV1QuizzesQuizIdPut: (
    quizId: string,
    options: typeof UpdateQuizRequest.Encoded,
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
   * List study attempt records for the current user, optionally filtered by project
   */
  readonly listAttemptsV1AttemptsGet: (
    options?: typeof ListAttemptsV1AttemptsGetParams.Encoded | undefined,
  ) => Effect.Effect<
    typeof AttemptListResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create a new study attempt record for a flashcard or quiz question
   */
  readonly createAttemptV1AttemptsPost: (options: {
    readonly params: typeof CreateAttemptV1AttemptsPostParams.Encoded
    readonly payload: typeof CreateAttemptRequest.Encoded
  }) => Effect.Effect<
    typeof AttemptResponse.Type,
    | HttpClientError.HttpClientError
    | ParseError
    | ClientError<'HTTPValidationError', typeof HTTPValidationError.Type>
  >
  /**
   * Create multiple study attempt records in a single batch operation
   */
  readonly createAttemptsBatchV1AttemptsBatchPost: (options: {
    readonly params: typeof CreateAttemptsBatchV1AttemptsBatchPostParams.Encoded
    readonly payload: typeof CreateAttemptBatchRequest.Encoded
  }) => Effect.Effect<
    typeof AttemptListResponse.Type,
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
