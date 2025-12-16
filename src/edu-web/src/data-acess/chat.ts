import { Atom, Registry, Result } from '@effect-atom/atom-react'
import {
  Array as Arr,
  Data,
  Effect,
  Layer,
  Order,
  Schema,
  Stream,
} from 'effect'
import { HttpBody } from '@effect/platform'
import { BrowserKeyValueStore } from '@effect/platform-browser'
import { UsageLimitExceededError, usageAtom } from './usage'
import type {
  ChatCompletionRequest,
  ChatCreate,
  ChatDto,
  ChatMessageDto,
  ChatUpdate,
} from '@/integrations/api/client'
import { ApiClientService } from '@/integrations/api/http'
import { SourceDto, ToolCallDto } from '@/integrations/api/client'
import { makeAtomRuntime } from '@/lib/make-atom-runtime'
import { withToast } from '@/lib/with-toast'
import { NetworkMonitor } from '@/lib/network-monitor'

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
  UpdateContent: {
    readonly chatId: string
    readonly messageId: string
    readonly content: string
  }
  UpdateSources: {
    readonly chatId: string
    readonly messageId: string
    readonly sources: Array<SourceDto>
  }
  UpdateTools: {
    readonly chatId: string
    readonly messageId: string
    readonly tools: Array<ToolCallDto>
  }
}>
const ChatMessagesAction = Data.taggedEnum<ChatMessagesAction>()

const byLastMessageCreatedAt = Order.mapInput(Order.Date, (chat: ChatDto) => {
  // const val = chat.last_message?.created_at
  const val = chat.messages?.at(-1)?.created_at
  return val ? new Date(val) : new Date(chat.created_at)
})

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
      (ctx, action: ChatMessagesAction | ChatDto) => {
        // Handle direct ChatDto updates (for backward compatibility)
        if ('id' in action && 'project_id' in action) {
          ctx.setSelf(Result.success(action))
          return
        }

        // Handle message actions
        const result = ctx.get(chatAtom(input))
        if (!Result.isSuccess(result)) return

        const chat = result.value
        const messages = Array.from(chat.messages ?? [])

        const update = ChatMessagesAction.$match(action, {
          Append: ({ message }) => {
            return [...messages, message]
          },
          UpdateContent: ({ messageId, content }) => {
            return messages.map((msg) =>
              msg.id === messageId ? { ...msg, content } : msg,
            )
          },
          UpdateSources: ({ messageId, sources }) => {
            return messages.map((msg) =>
              msg.id === messageId ? { ...msg, sources } : msg,
            )
          },
          UpdateTools: ({ messageId, tools }) => {
            return messages.map((msg) =>
              msg.id === messageId ? { ...msg, tools } : msg,
            )
          },
          RemoveTemporaryMessage: () => {
            return messages.filter((msg) => msg.id !== 'temporary-message-id')
          },
        })

        ctx.setSelf(
          Result.success({
            ...chat,
            messages: update,
          }),
        )
      },
    ),
    {
      remote: chatRemoteAtom(input),
    },
  ),
)

const MessageChunk = Schema.Struct({
  id: Schema.String,
  chunk: Schema.String,
  done: Schema.Boolean,
  status: Schema.NullOr(Schema.String),
  sources: Schema.NullOr(Schema.Array(SourceDto)),
  tools: Schema.NullOr(Schema.Array(ToolCallDto)),
})

// Atom to track current streaming status for a chat
export const chatStreamStatusAtom = Atom.family((_chatId: string) =>
  Atom.make<string | null>(null),
)

export const streamMessageAtom = runtime
  .fn(
    Effect.fn(function* (
      input: typeof ChatCompletionRequest.Encoded & {
        projectId: string
        chatId: string
      },
      get: Atom.FnContext,
    ) {
      const registry = yield* Registry.AtomRegistry

      // Add user message using the new action pattern
      const userMessage: ChatMessageDto = {
        id: 'temporary-message-id',
        role: 'user',
        content: input.message,
        sources: undefined,
        tools: undefined,
        created_at: new Date().toISOString(),
      }
      const chatKey = `${input.projectId}:${input.chatId}`
      get.set(
        chatAtom(chatKey),
        ChatMessagesAction.Append({
          chatId: input.chatId,
          message: userMessage,
        }),
      )

      const { httpClient } = yield* ApiClientService
      const body = HttpBody.unsafeJson({ message: input.message })
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
            Effect.sync(() => get.refresh(chatRemoteAtom(chatKey))),
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
              Schema.decodeUnknown(Schema.parseJson(MessageChunk))(line),
            ),
          )
        }),
        Stream.tap((chunk) =>
          Effect.gen(function* () {
            const messageId = chunk.id

            // Update stream status if provided
            if (chunk.status) {
              get.set(chatStreamStatusAtom(input.chatId), chunk.status)
            }

            // Skip message creation/update if this is just a status update with no content/metadata
            const hasContent = chunk.chunk && chunk.chunk.length > 0
            const hasMetadata =
              (chunk.sources && chunk.sources.length > 0) ||
              (chunk.tools && chunk.tools.length > 0)

            if (!hasContent && !hasMetadata) {
              // This is just a status update - skip message processing
              return
            }

            const chat = yield* get.result(chatAtom(chatKey))
            const messages = Array.from(chat.messages ?? [])
            const msgIdx = messages.findIndex((msg) => msg.id === messageId)
            const content =
              (messages[msgIdx]?.content ?? '') + (chunk.chunk || '')

            if (msgIdx === -1) {
              // Create new assistant message
              const assistantMessage: ChatMessageDto = {
                id: messageId,
                role: 'assistant',
                content,
                sources: chunk.sources ?? [],
                tools: chunk.tools ?? [],
                created_at: new Date().toISOString(),
              }
              get.set(
                chatAtom(chatKey),
                ChatMessagesAction.Append({
                  chatId: input.chatId,
                  message: assistantMessage,
                }),
              )
            } else {
              // Update existing message content
              get.set(
                chatAtom(chatKey),
                ChatMessagesAction.UpdateContent({
                  chatId: input.chatId,
                  messageId,
                  content,
                }),
              )

              // Helper to get current message state
              const getCurrentMessage = function* () {
                const chat = yield* get.result(chatAtom(chatKey))
                return Array.from(chat.messages ?? []).find(
                  (msg) => msg.id === messageId,
                )
              }

              // Update sources if provided
              if (chunk.sources && chunk.sources.length > 0) {
                const currentMessage = yield* getCurrentMessage()
                const existingSources = currentMessage?.sources ?? []
                const uniqueNewSources = chunk.sources.filter(
                  (newSource) =>
                    !existingSources.some(
                      (existing) => existing.id === newSource.id,
                    ),
                )

                if (uniqueNewSources.length > 0) {
                  get.set(
                    chatAtom(chatKey),
                    ChatMessagesAction.UpdateSources({
                      chatId: input.chatId,
                      messageId,
                      sources: [...existingSources, ...uniqueNewSources],
                    }),
                  )
                }
              }

              // Update tools if provided - deep merge by ID
              if (chunk.tools && chunk.tools.length > 0) {
                const currentMessage = yield* getCurrentMessage()
                const existingTools = currentMessage?.tools ?? []

                // Deep merge tools by ID in a single pass
                const mergedTools = [
                  ...existingTools.map((existing) => {
                    const newTool = chunk.tools!.find(
                      (t) => t.id === existing.id,
                    )
                    return newTool ? { ...existing, ...newTool } : existing
                  }),
                  ...chunk.tools.filter(
                    (newTool) =>
                      !existingTools.some((t) => t.id === newTool.id),
                  ),
                ]

                get.set(
                  chatAtom(chatKey),
                  ChatMessagesAction.UpdateTools({
                    chatId: input.chatId,
                    messageId,
                    tools: mergedTools,
                  }),
                )
              }
            }

            // If stream is done, fetch fresh data and update atomically
            if (chunk.done) {
              yield* Effect.sync(() => {
                get.set(chatStreamStatusAtom(input.chatId), null)
              })
              // Fetch fresh data in background without triggering loading state
              const { apiClient } = yield* ApiClientService
              const freshChat =
                yield* apiClient.getChatApiV1ProjectsProjectIdChatsChatIdGet(
                  input.projectId,
                  input.chatId,
                )
              // Update atom with fresh data once fetched
              get.set(chatAtom(chatKey), freshChat)
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

    const chatKey = `${input.projectId}:${input.chatId}`
    registry.set(chatAtom(chatKey), res)
    registry.set(chatsAtom(res.project_id), ChatsAction.Upsert({ chat: res }))
    return res
  }),
)

export const appendMessageAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    chatId: string
    message: ChatMessageDto
  }) {
    const registry = yield* Registry.AtomRegistry
    const chatKey = `${input.projectId}:${input.chatId}`
    registry.set(
      chatAtom(chatKey),
      ChatMessagesAction.Append({
        chatId: input.chatId,
        message: input.message,
      }),
    )
  }),
)

export const updateMessageContentAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    chatId: string
    messageId: string
    content: string
  }) {
    const registry = yield* Registry.AtomRegistry
    const chatKey = `${input.projectId}:${input.chatId}`
    registry.set(
      chatAtom(chatKey),
      ChatMessagesAction.UpdateContent({
        chatId: input.chatId,
        messageId: input.messageId,
        content: input.content,
      }),
    )
  }),
)

export const updateMessageSourcesAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    chatId: string
    messageId: string
    sources: Array<SourceDto>
  }) {
    const registry = yield* Registry.AtomRegistry
    const chatKey = `${input.projectId}:${input.chatId}`
    registry.set(
      chatAtom(chatKey),
      ChatMessagesAction.UpdateSources({
        chatId: input.chatId,
        messageId: input.messageId,
        sources: input.sources,
      }),
    )
  }),
)

export const updateMessageToolsAtom = runtime.fn(
  Effect.fn(function* (input: {
    projectId: string
    chatId: string
    messageId: string
    tools: Array<ToolCallDto>
  }) {
    const registry = yield* Registry.AtomRegistry
    const chatKey = `${input.projectId}:${input.chatId}`
    registry.set(
      chatAtom(chatKey),
      ChatMessagesAction.UpdateTools({
        chatId: input.chatId,
        messageId: input.messageId,
        tools: input.tools,
      }),
    )
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
