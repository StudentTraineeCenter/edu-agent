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
const byLastMessageCreatedAt = (a: ChatDto, b: ChatDto): -1 | 0 | 1 => {
  const aDate = new Date(a.updated_at).getTime()
  const bDate = new Date(b.updated_at).getTime()
  if (bDate > aDate) return -1
  if (bDate < aDate) return 1
  return 0
}

export const chatsRemoteAtom = Atom.family((projectId: string) =>
  runtime
    .atom(
      Effect.fn(function* () {
        const { apiClient } = yield* ApiClientService
        const resp =
          yield* apiClient.listChatsApiV1ProjectsProjectIdChatsGet(projectId)
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

      const decoder = new TextDecoder()

      const respStream = resp.stream.pipe(
        Stream.map((value) => decoder.decode(value, { stream: true })),
        Stream.map((chunk) => {
          const chunkLines = chunk.split('\n')
          const res = chunkLines
            .map((line) =>
              line.startsWith('data: ') ? line.replace('data: ', '') : '',
            )
            .filter((line) => line !== '')
            .join('\n')
          return res
        }),
        Stream.filter((chunk) => chunk !== ''),
        Stream.flatMap((chunk) => {
          const lines = chunk.trim().split('\n')
          return Stream.fromIterable(lines).pipe(
            Stream.filter((line) => line.trim() !== ''),
            Stream.flatMap((line) =>
              Schema.decodeUnknown(
                Schema.parseJson(
                  Schema.Struct({
                    message_id: Schema.String,
                    chat_id: Schema.String,
                    role: Schema.String,
                    created_at: Schema.String,
                    // delta is a string for text parts in streaming chunks (done: false)
                    // or an object for non-text parts
                    delta: Schema.optional(
                      Schema.Union(Schema.String, Schema.Any),
                    ),
                    // part_id is for tracking parts during streaming (similar to Vercel AI SDK)
                    part_id: Schema.optional(Schema.String),
                    // part is for final chunk (done: true) - full aggregated part object (includes order and id)
                    part: Schema.optional(
                      Schema.Union(
                        TextPartDto,
                        FilePartDto,
                        ToolCallPartDto,
                        SourceDocumentPartDto,
                      ),
                    ),
                    status: Schema.optional(Schema.String),
                    done: Schema.optional(Schema.Boolean),
                  }),
                ),
              )(line),
            ),
          )
        }),
        Stream.tap((partEvent) =>
          Effect.gen(function* () {
            const messageId = partEvent.message_id

            // Update stream status if provided
            if (partEvent.status) {
              get.set(chatStreamStatusAtom(input.chatId), partEvent.status)
            } else if (partEvent.done) {
              get.set(chatStreamStatusAtom(input.chatId), null)
            }

            // Skip if no part/delta to process
            if (partEvent.done && !partEvent.part) {
              return
            }
            if (!partEvent.done && !partEvent.delta) {
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
              // Create new assistant message with this part/delta
              let initialParts: ReadonlyArray<
                | TextPartDto
                | FilePartDto
                | ToolCallPartDto
                | SourceDocumentPartDto
              >

              if (partEvent.done && partEvent.part) {
                // Final chunk: use the full part
                initialParts = [partEvent.part]
              } else if (partEvent.delta) {
                // Streaming chunk: create part from delta
                if (typeof partEvent.delta === 'string') {
                  // Delta is a string (text content)
                  // Order will be set correctly in the final part (done: true)
                  initialParts = [
                    {
                      type: 'text',
                      text_content: partEvent.delta,
                      order: 0,
                    } as TextPartDto,
                  ]
                } else {
                  // Delta is an object (non-text part)
                  initialParts = [
                    partEvent.delta as
                      | TextPartDto
                      | FilePartDto
                      | ToolCallPartDto
                      | SourceDocumentPartDto,
                  ]
                }
              } else {
                return
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

              // If done is true, replace parts (final chunk contains full aggregated part)
              if (partEvent.done && partEvent.part) {
                // For final chunk, replace the part by ID first, then by order and type
                const finalPart = partEvent.part
                const partId = (finalPart as any).id
                const partOrder = (finalPart as any).order ?? 0
                const partType = finalPart.type

                // For source-document parts, also check by source_id to prevent duplicates
                const sourceId =
                  partType === 'source-document'
                    ? (finalPart as SourceDocumentPartDto).source_id
                    : null

                // Try to find by ID first (most reliable), then by source_id for source-documents, then by order and type
                const existingPartIdx = existingParts.findIndex(
                  (p) =>
                    (partId && 'id' in p && (p as any).id === partId) ||
                    (sourceId &&
                      p.type === 'source-document' &&
                      (p as SourceDocumentPartDto).source_id === sourceId) ||
                    ((p as any).order === partOrder && p.type === partType),
                )

                let updatedParts: ReadonlyArray<
                  | TextPartDto
                  | FilePartDto
                  | ToolCallPartDto
                  | SourceDocumentPartDto
                >

                if (existingPartIdx !== -1) {
                  // Replace the part at this index completely (no merging)
                  // This prevents duplication by replacing accumulated deltas with final part
                  const newParts = [...existingParts]
                  newParts[existingPartIdx] = finalPart
                  updatedParts = newParts as ReadonlyArray<
                    | TextPartDto
                    | FilePartDto
                    | ToolCallPartDto
                    | SourceDocumentPartDto
                  >
                } else if (partType === 'text' && existingParts.length > 0) {
                  // Fallback for text parts: if exact match not found, replace first text part
                  // This handles cases where part matching fails but we need to prevent duplication
                  const firstTextPartIdx = existingParts.findIndex(
                    (p) => p.type === 'text',
                  )
                  if (firstTextPartIdx !== -1) {
                    const newParts = [...existingParts]
                    newParts[firstTextPartIdx] = finalPart
                    updatedParts = newParts as ReadonlyArray<
                      | TextPartDto
                      | FilePartDto
                      | ToolCallPartDto
                      | SourceDocumentPartDto
                    >
                  } else {
                    // No text part found, append (shouldn't happen)
                    updatedParts = [
                      ...existingParts,
                      finalPart,
                    ] as ReadonlyArray<
                      | TextPartDto
                      | FilePartDto
                      | ToolCallPartDto
                      | SourceDocumentPartDto
                    >
                  }
                } else if (
                  partType === 'source-document' &&
                  sourceId &&
                  existingParts.length > 0
                ) {
                  // Fallback for source-document parts: if exact match not found, replace by source_id
                  // This handles cases where part matching fails but we need to prevent duplication
                  const sourceDocPartIdx = existingParts.findIndex(
                    (p) =>
                      p.type === 'source-document' &&
                      (p as SourceDocumentPartDto).source_id === sourceId,
                  )
                  if (sourceDocPartIdx !== -1) {
                    const newParts = [...existingParts]
                    newParts[sourceDocPartIdx] = finalPart
                    updatedParts = newParts as ReadonlyArray<
                      | TextPartDto
                      | FilePartDto
                      | ToolCallPartDto
                      | SourceDocumentPartDto
                    >
                  } else {
                    // No matching source-document part found, append
                    updatedParts = [
                      ...existingParts,
                      finalPart,
                    ] as ReadonlyArray<
                      | TextPartDto
                      | FilePartDto
                      | ToolCallPartDto
                      | SourceDocumentPartDto
                    >
                  }
                } else {
                  // Part not found and not a text/source-document part, append
                  updatedParts = [...existingParts, finalPart] as ReadonlyArray<
                    | TextPartDto
                    | FilePartDto
                    | ToolCallPartDto
                    | SourceDocumentPartDto
                  >
                }

                get.set(
                  chatAtom(chatKey),
                  ChatMessagesAction.UpdateParts({
                    chatId: input.chatId,
                    messageId,
                    parts: updatedParts,
                  }),
                )
              } else if (partEvent.delta) {
                // For streaming chunks (done: false), merge/append delta
                const delta = partEvent.delta

                if (typeof delta === 'string') {
                  // Delta is a string (text content) - append to existing text part
                  // Use part_id to find the correct part (similar to Vercel AI SDK)
                  const partId = partEvent.part_id
                  const existingTextPartIdx = existingParts.findIndex(
                    (p) =>
                      p.type === 'text' &&
                      (partId && 'id' in p
                        ? (p as any).id === partId
                        : (p as TextPartDto).order === 0),
                  )

                  if (existingTextPartIdx !== -1) {
                    // Append to existing text part
                    const existingTextPart = existingParts[
                      existingTextPartIdx
                    ] as TextPartDto
                    const mergedPart: TextPartDto = {
                      ...existingTextPart,
                      text_content: existingTextPart.text_content + delta,
                    }
                    const updatedParts = [...existingParts]
                    updatedParts[existingTextPartIdx] = mergedPart
                    get.set(
                      chatAtom(chatKey),
                      ChatMessagesAction.UpdateParts({
                        chatId: input.chatId,
                        messageId,
                        parts: updatedParts as ReadonlyArray<
                          | TextPartDto
                          | FilePartDto
                          | ToolCallPartDto
                          | SourceDocumentPartDto
                        >,
                      }),
                    )
                  } else {
                    // Create new text part with part_id (order will be set correctly in final part)
                    const newTextPart = {
                      type: 'text' as const,
                      id: partEvent.part_id,
                      text_content: delta,
                      order: 0,
                    } as TextPartDto & { id?: string }
                    const updatedParts = [
                      ...existingParts,
                      newTextPart,
                    ] as ReadonlyArray<
                      | TextPartDto
                      | FilePartDto
                      | ToolCallPartDto
                      | SourceDocumentPartDto
                    >
                    get.set(
                      chatAtom(chatKey),
                      ChatMessagesAction.UpdateParts({
                        chatId: input.chatId,
                        messageId,
                        parts: updatedParts,
                      }),
                    )
                  }
                } else {
                  // Delta is an object (non-text part) - handle as before
                  const deltaObj = delta as
                    | TextPartDto
                    | FilePartDto
                    | ToolCallPartDto
                    | SourceDocumentPartDto
                  const isDuplicate = existingParts.some((existingPart) => {
                    // For text parts, check by order
                    if (
                      deltaObj.type === 'text' &&
                      existingPart.type === 'text'
                    ) {
                      return (
                        (deltaObj as TextPartDto).order ===
                        (existingPart as TextPartDto).order
                      )
                    }
                    // For source-document parts, check by source_id to prevent duplicates
                    if (
                      deltaObj.type === 'source-document' &&
                      existingPart.type === 'source-document'
                    ) {
                      return (
                        (deltaObj as SourceDocumentPartDto).source_id ===
                        (existingPart as SourceDocumentPartDto).source_id
                      )
                    }
                    // For other parts, check by type and order
                    return (
                      deltaObj.type === existingPart.type &&
                      (deltaObj as any).order === (existingPart as any).order
                    )
                  })

                  if (!isDuplicate) {
                    const updatedParts = [
                      ...existingParts,
                      deltaObj,
                    ] as ReadonlyArray<
                      | TextPartDto
                      | FilePartDto
                      | ToolCallPartDto
                      | SourceDocumentPartDto
                    >
                    get.set(
                      chatAtom(chatKey),
                      ChatMessagesAction.UpdateParts({
                        chatId: input.chatId,
                        messageId,
                        parts: updatedParts,
                      }),
                    )
                  }
                }
              }
            }

            // If stream is done, fetch fresh data for all messages
            if (partEvent.done) {
              yield* Effect.sync(() => {
                get.set(chatStreamStatusAtom(input.chatId), null)
              })
              // Fetch fresh data in background without triggering loading state
              // get.refresh(getChatMessagesAtom(chatKey))
            }
          }),
        ),
      )
      yield* Stream.runCollect(respStream)

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
