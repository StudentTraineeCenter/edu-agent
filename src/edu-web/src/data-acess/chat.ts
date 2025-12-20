import type {
  ChatCreate,
  ChatDto,
  ChatMessageDto,
  ChatUpdate,
} from '@/integrations/api/client'
import {
  FilePartDto,
  SourceDocumentPartDto,
  TextPartDto,
  ToolCallPartDto,
} from '@/integrations/api/client'
import { ApiClientService } from '@/integrations/api/http'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { NetworkMonitor } from '@/lib/network-monitor'
import { withToast } from '@/lib/with-toast'
import { Atom, Registry, Result } from '@effect-atom/atom-react'
import { HttpBody } from '@effect/platform'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { Array as Arr, Data, Effect, Layer, Schema, Stream } from 'effect'
import { UsageLimitExceededError, usageAtom } from './usage'

const runtime = makeAtomRuntime(
  Layer.mergeAll(
    BrowserKeyValueStore.layerLocalStorage,
    NetworkMonitor.Default,
    ApiClientService.Default,
  ),
)

type ChatsAction = Data.TaggedEnum<{
  Upsert: { readonly chat: ChatDto }
  Delete: { readonly chatId: string }
}>
const ChatsAction = Data.taggedEnum<ChatsAction>()

type ChatMessagesAction = Data.TaggedEnum<{
  Append: { readonly chatId: string; readonly message: ChatMessageDto }
  RemoveTemporaryMessage: {}
  UpdateParts: {
    readonly chatId: string
    readonly messageId: string
    readonly parts: ReadonlyArray<
      TextPartDto | FilePartDto | ToolCallPartDto | SourceDocumentPartDto
    >
  }
  UpdateStatus: {
    readonly chatId: string
    readonly messageId: string
    readonly status: string | null
  }
}>
const ChatMessagesAction = Data.taggedEnum<ChatMessagesAction>()

// Sort chats by last message created date (most recent first)
// Sort chats by last message created date (most recent first)
const byLastMessageCreatedAt = (a: ChatDto, b: ChatDto): -1 | 0 | 1 => {
  const aDate = new Date(a.last_message_at ?? a.updated_at).getTime()
  const bDate = new Date(b.last_message_at ?? b.updated_at).getTime()
  if (bDate > aDate) return 1
  if (bDate < aDate) return -1
  return 0
}

export const chatsRemoteAtom = Atom.family((projectId: string) =>
  runtime
    .atom(
      Effect.fn(function* () {
        const { apiClient } = yield* ApiClientService
        const resp = yield* apiClient.listChatsApiV1ProjectsProjectIdChatsGet(projectId)
        return Arr.sort(byLastMessageCreatedAt)(resp)
      }),
    )
    .pipe(Atom.keepAlive),
)

export const chatRemoteAtom = Atom.family((input: string) =>
  runtime
    .atom(
      Effect.fn(function* () {
        const [projectId, chatId] = input.split(':')

        const { apiClient } = yield* ApiClientService
        return yield* apiClient.getChatApiV1ProjectsProjectIdChatsChatIdGet(
          projectId,
          chatId,
        )
      }),
    )
    .pipe(Atom.keepAlive),
)

export const chatsAtom = Atom.family((projectId: string) =>
  Object.assign(
    Atom.writable(
      (get: Atom.Context) => get(chatsRemoteAtom(projectId)),
      (ctx, action: ChatsAction) => {
        const result = ctx.get(chatsAtom(projectId))
        if (!Result.isSuccess(result)) return

        const update = ChatsAction.$match(action, {
          Upsert: ({ chat }) => {
            const existing = result.value.find((c) => c.id === chat.id)
            if (existing)
              return result.value.map((c) => (c.id === chat.id ? chat : c))
            return Arr.prepend(result.value, chat)
          },
          Delete: ({ chatId }) => {
            return result.value.filter((c) => c.id !== chatId)
          },
        })

        ctx.setSelf(Result.success(update))
      },
    ),
    {
      remote: chatsRemoteAtom(projectId),
    },
  ),
)

export const chatAtom = Atom.family((input: string) =>
  Object.assign(
    Atom.writable(
      (get: Atom.Context) => get(chatRemoteAtom(input)),
      (ctx, action: ChatMessagesAction) => {
        // Handle direct ChatMessageDto[] updates (for refreshing)
        // if (Array.isArray(action)) {
        //   ctx.setSelf(Result.success(action))
        //   return
        // }

        // Handle message actions
        const result = ctx.get(chatAtom(input))
        if (!Result.isSuccess(result)) return

        const messages = Array.from(result.value.messages ?? [])

        const update: ReadonlyArray<ChatMessageDto> = ChatMessagesAction.$match(
          action,
          {
            Append: ({ message }) => {
              return [...messages, message] as ReadonlyArray<ChatMessageDto>
            },
            UpdateParts: ({ messageId, parts }) => {
              return messages.map((msg: ChatMessageDto) =>
                msg.id === messageId ? { ...msg, parts } : msg,
              ) as ReadonlyArray<ChatMessageDto>
            },
            UpdateStatus: ({ messageId, status }) => {
              return messages.map((msg: ChatMessageDto) =>
                msg.id === messageId
                  ? {
                      ...msg,
                      parts: (msg.parts
                        ? Array.from(msg.parts).map((part) =>
                            // Update status of any tool call parts
                            part.type === 'tool_call'
                              ? { ...part, tool_state: status }
                              : part,
                          )
                        : []) as ReadonlyArray<
                        | TextPartDto
                        | FilePartDto
                        | ToolCallPartDto
                        | SourceDocumentPartDto
                      >,
                    }
                  : msg,
              ) as ReadonlyArray<ChatMessageDto>
            },
            RemoveTemporaryMessage: () => {
              return messages.filter(
                (msg: ChatMessageDto) => msg.id !== 'temporary-message-id',
              ) as ReadonlyArray<ChatMessageDto>
            },
          },
        )

        ctx.setSelf(Result.success({ ...result.value, messages: update }))
      },
    ),
    {
      remote: chatRemoteAtom(input),
    },
  ),
)

// Atom to track current streaming status for a chat
export const chatStreamStatusAtom = Atom.family((_chatId: string) =>
  Atom.make<string | null>(null),
)

// Schema for streaming events
const StreamEventSchema = Schema.Struct({
  message_id: Schema.String,
  chat_id: Schema.String,
  role: Schema.String,
  created_at: Schema.String,
  delta: Schema.optional(Schema.Union(Schema.String, Schema.Any)),
  part_id: Schema.optional(Schema.String),
  parts: Schema.optional(
    Schema.Array(
      Schema.Union(
        TextPartDto,
        FilePartDto,
        ToolCallPartDto,
        SourceDocumentPartDto,
      ),
    ),
  ),
  status: Schema.optional(Schema.String),
  done: Schema.optional(Schema.Boolean),
})

type StreamEvent = Schema.Schema.Type<typeof StreamEventSchema>

const handleStreamPart = (
  input: { chatId: string; projectId: string },
  get: Atom.FnContext,
  registry: Registry.Registry,
) =>
  Effect.fn(function* (partEvent: StreamEvent) {
    const chatKey = `${input.projectId}:${input.chatId}`
    const messageId = partEvent.message_id

    // Update stream status if provided
    if (partEvent.status) {
      get.set(chatStreamStatusAtom(input.chatId), partEvent.status)
    } else if (partEvent.done) {
      get.set(chatStreamStatusAtom(input.chatId), null)
    }

    // Skip if done and no parts/delta to process
    if (
      partEvent.done &&
      (!partEvent.parts || partEvent.parts.length === 0) &&
      !partEvent.delta
    ) {
      return
    }

    // Get current messages
    const currentMessagesResult = registry.get(chatAtom(chatKey))
    const currentMessages = Result.isSuccess(currentMessagesResult)
      ? (currentMessagesResult.value.messages ?? [])
      : []
    const msgIdx = currentMessages.findIndex(
      (msg: ChatMessageDto) => msg.id === messageId,
    )

    if (msgIdx === -1) {
      // Create new assistant message
      // Initialize parts based on what we received
      let initialParts: ReadonlyArray<
        TextPartDto | FilePartDto | ToolCallPartDto | SourceDocumentPartDto
      > = []

      if (partEvent.parts) {
        initialParts = partEvent.parts
      } else if (partEvent.delta && typeof partEvent.delta === 'string') {
        // Create initial text part from delta
        initialParts = [
          {
            type: 'text',
            text_content: partEvent.delta,
            order: 0,
            id: partEvent.part_id, // Use part_id if available
          } as TextPartDto,
        ]
      }

      const newMessage: ChatMessageDto = {
        id: messageId,
        chat_id: partEvent.chat_id,
        role: partEvent.role,
        created_at: partEvent.created_at,
        parts: initialParts,
      }
      get.set(
        chatAtom(chatKey),
        ChatMessagesAction.Append({
          chatId: input.chatId,
          message: newMessage,
        }),
      )
    } else {
      // Update existing message
      const existingMessage = currentMessages[msgIdx]
      const existingParts = existingMessage.parts || []
      let newParts = [...existingParts]

      if (partEvent.parts) {
        // Handle full parts list update (usually final chunk or tool updates)
        for (const part of partEvent.parts) {
          const partId = part.id
          let existingPartIdx = -1

          if (partId) {
            existingPartIdx = newParts.findIndex((p: any) => p.id === partId)
          }

          // Fallback: search by order for TextParts
          if (existingPartIdx === -1 && part.type === 'text') {
            existingPartIdx = newParts.findIndex(
              (p) => p.type === 'text' && p.order === part.order,
            )
          }

          if (existingPartIdx !== -1) {
            const existingPart = newParts[existingPartIdx]
            if (part.type === 'text' && existingPart.type === 'text') {
              // For parts list, we usually replace, but if it's text streaming reuse, check logic
              // However, if server sends 'parts', it contains the FULL state or DELTA?
              // Spec says: "And then comes all the parts" implies final state.
              // So replacing is safer than appending if we get the full parts list.
              newParts[existingPartIdx] = part
            } else {
              newParts[existingPartIdx] = part
            }
          } else {
            newParts.push(part)
          }
        }
      } else if (partEvent.delta && typeof partEvent.delta === 'string') {
        // Handle text delta streaming
        const partId = partEvent.part_id
        let existingPartIdx = -1

        if (partId) {
          existingPartIdx = newParts.findIndex((p: any) => p.id === partId)
        }

        // Fallback: assume first text part if no ID match (common for single text response)
        if (existingPartIdx === -1) {
          existingPartIdx = newParts.findIndex((p) => p.type === 'text')
        }

        if (existingPartIdx !== -1) {
          const existingPart = newParts[existingPartIdx] as TextPartDto
          newParts[existingPartIdx] = {
            ...existingPart,
            text_content: existingPart.text_content + partEvent.delta,
          }
        } else {
          // No text part found, create one
          newParts.push({
            type: 'text',
            text_content: partEvent.delta,
            order: 0, // Default order
            id: partId,
          } as TextPartDto)
        }
      }

      get.set(
        chatAtom(chatKey),
        ChatMessagesAction.UpdateParts({
          chatId: input.chatId,
          messageId,
          parts: newParts as ReadonlyArray<
            | TextPartDto
            | FilePartDto
            | ToolCallPartDto
            | SourceDocumentPartDto
          >,
        }),
      )
    }

    // If stream is done, fetch fresh data for all messages
    if (partEvent.done) {
      yield* Effect.sync(() => {
        get.set(chatStreamStatusAtom(input.chatId), null)
      })
    }
  })

export const streamMessageAtom = runtime
  .fn(
    Effect.fn(function* (
      input: {
        message: ChatMessageDto
        projectId: string
        chatId: string
      },
      get: Atom.FnContext,
    ) {
      const registry = yield* Registry.AtomRegistry

      // Add user message using the new action pattern
      const chatKey = `${input.projectId}:${input.chatId}`
      get.set(
        chatAtom(chatKey),
        ChatMessagesAction.Append({
          chatId: input.chatId,
          message: {
            ...input.message,
            id: 'temporary-message-id', // Mark as temporary until actual ID is received from backend
          },
        }),
      )

      const { httpClient } = yield* ApiClientService

      // Transform ChatMessageDto parts to API format (TextPart/FilePart)
      const apiParts = (input.message.parts || []).map((part) => {
        if (part.type === 'text') {
          return {
            type: 'text' as const,
            text: part.text_content,
          }
        } else if (part.type === 'file') {
          return {
            type: 'file' as const,
            mediaType: part.file_type,
            filename: part.file_name,
            url: part.file_url,
          }
        }
        // Fallback for other part types (shouldn't happen for user messages)
        return part
      })

      const body = HttpBody.unsafeJson({ parts: apiParts })
      const resp = yield* httpClient
        .post(
          `/api/v1/projects/${input.projectId}/chats/${input.chatId}/messages/stream`,
          {
            body,
          },
        )
        .pipe(
          // If the request fails, remove the temporary message
          Effect.tapError(() =>
            Effect.sync(() =>
              get.set(
                chatAtom(chatKey),
                ChatMessagesAction.RemoveTemporaryMessage(),
              ),
            ),
          ),
        )

      if (resp.status === 429) {
        registry.set(
          chatAtom(chatKey),
          ChatMessagesAction.RemoveTemporaryMessage(),
        )
        registry.refresh(usageAtom)
        return yield* new UsageLimitExceededError({
          message: 'Usage limit exceeded',
        })
      }

      yield* resp.stream.pipe(
        Stream.decodeText(),
        Stream.splitLines,
        Stream.filter((line) => line.startsWith('data: ')),
        Stream.map((line) => line.slice(6)),
        Stream.filter((line) => line.length > 0),
        Stream.mapEffect((line) =>
          Schema.decodeUnknown(Schema.parseJson(StreamEventSchema))(line),
        ),
        Stream.tap(handleStreamPart(input, get, registry)),
        Stream.runCollect,
      )

      // Refresh usage only
      get.refresh(usageAtom)
    }),
  )
  .pipe(Atom.keepAlive)

export const createChatAtom = runtime.fn(
  Effect.fn(function* (
    input: typeof ChatCreate.Encoded & { projectId: string },
  ) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    const res = yield* apiClient.createChatApiV1ProjectsProjectIdChatsPost(
      input.projectId,
      input,
    )

    registry.set(chatsAtom(input.projectId), ChatsAction.Upsert({ chat: res }))
    registry.refresh(chatsRemoteAtom(input.projectId))
    return res
  }),
)

export const updateChatAtom = runtime.fn(
  Effect.fn(function* (
    input: typeof ChatUpdate.Encoded & { projectId: string; chatId: string },
  ) {
    const registry = yield* Registry.AtomRegistry
    const { apiClient } = yield* ApiClientService
    const res =
      yield* apiClient.updateChatApiV1ProjectsProjectIdChatsChatIdPatch(
        input.projectId,
        input.chatId,
        input,
      )

    registry.set(chatsAtom(res.project_id), ChatsAction.Upsert({ chat: res }))
    return res
  }),
)

export const updateMessageToolsAtom = runtime.fn(
  Effect.fn(function* (
    input: {
      projectId: string
      chatId: string
      messageId: string
      tools: Array<ToolCallPartDto>
    },
    get: Atom.FnContext,
  ) {
    const registry = yield* Registry.AtomRegistry
    const chatKey = `${input.projectId}:${input.chatId}`

    const chat = yield* get.result(chatAtom(chatKey))
    const messages = chat.messages ?? []

    const messageToUpdate = messages.find(
      (msg: ChatMessageDto) => msg.id === input.messageId,
    )

    if (messageToUpdate) {
      const updatedParts = (
        messageToUpdate.parts
          ? Array.from(messageToUpdate.parts).map((part) => {
              if (part.type === 'tool_call') {
                const correspondingTool = input.tools.find(
                  (tool) => tool.tool_call_id === part.tool_call_id,
                )
                if (correspondingTool) {
                  return correspondingTool
                }
              }
              return part
            })
          : []
      ) as ReadonlyArray<
        TextPartDto | FilePartDto | ToolCallPartDto | SourceDocumentPartDto
      >

      registry.set(
        chatAtom(chatKey),
        ChatMessagesAction.UpdateParts({
          chatId: input.chatId,
          messageId: input.messageId,
          parts: updatedParts,
        }),
      )
    }
  }),
)

// File upload is handled in the stream endpoint, no separate upload function needed

export const upsertMessageAtom = runtime.fn(
  Effect.fn(function* (
    input: {
      projectId: string
      chatId: string
      messageId: string
      message: ChatMessageDto
    },
    get: Atom.FnContext,
  ) {
    const registry = yield* Registry.AtomRegistry
    const { httpClient } = yield* ApiClientService
    const chatKey = `${input.projectId}:${input.chatId}`

    // Strip SAS tokens from file URLs before persisting
    const messageToPersist: ChatMessageDto = {
      ...input.message,
      parts: Array.from(input.message.parts || []).map((part) => {
        if (part.type === 'file' && part.file_url?.includes('?')) {
          return {
            ...part,
            file_url: part.file_url.split('?')[0], // Remove SAS token
          }
        }
        return part
      }),
    }

    // Send to backend to persist
    const body = HttpBody.unsafeJson({
      id: input.messageId,
      chatId: input.chatId,
      message: messageToPersist,
    })

    yield* httpClient
      .post(
        `/api/v1/projects/${input.projectId}/chats/${input.chatId}/messages/upsert`,
        {
          body,
        },
      )
      .pipe(
        Effect.catchAll(() => {
          // If upsert endpoint doesn't exist yet, just update local state
          return Effect.void
        }),
      )

    // Update local state
    const chat = yield* get.result(chatAtom(chatKey))
    const currentMessages = chat.messages ?? []

    const messageIndex = currentMessages.findIndex(
      (msg: ChatMessageDto) => msg.id === input.messageId,
    )

    if (messageIndex === -1) {
      registry.set(
        chatAtom(chatKey),
        ChatMessagesAction.Append({
          chatId: input.chatId,
          message: messageToPersist,
        }),
      )
    } else {
      registry.set(
        chatAtom(chatKey),
        ChatMessagesAction.UpdateParts({
          chatId: input.chatId,
          messageId: input.messageId,
          parts: messageToPersist.parts || [],
        }),
      )
    }
  }),
)

export const deleteChatAtom = runtime.fn(
  Effect.fn(
    function* (input: { projectId: string; chatId: string }) {
      const registry = yield* Registry.AtomRegistry
      const { apiClient } = yield* ApiClientService
      const networkMonitor = yield* NetworkMonitor

      yield* apiClient
        .deleteChatApiV1ProjectsProjectIdChatsChatIdDelete(
          input.projectId,
          input.chatId,
        )
        .pipe(networkMonitor.latch.whenOpen)

      registry.set(
        chatsAtom(input.projectId),
        ChatsAction.Delete({ chatId: input.chatId }),
      )
    },
    withToast({
      onWaiting: () => 'Deleting chat...',
      onSuccess: 'Chat deleted',
      onFailure: 'Failed to delete chat',
    }),
  ),
)
