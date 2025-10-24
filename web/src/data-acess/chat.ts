import { baseUrl, createApiClient } from '@/integrations/api'
import type { Chat, ChatCreateRequest, ChatUpdateRequest, Source, ToolCall } from '@/integrations/api'
import { useMutation, useQuery, type QueryKey } from '@tanstack/react-query'
import { useAuth } from '@/hooks/use-auth'
import type { MutationOptions } from '@/data-acess/utils'

export const CHATS_QUERY_KEY = (projectId: string): QueryKey => ['project', projectId, 'chats']

export const useChatsQuery = (projectId: string) => {
  const { getAccessToken } = useAuth()
  return useQuery({
    queryKey: CHATS_QUERY_KEY(projectId),
    queryFn: async () => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.GET(`/v1/chats`, {
        params: {
          query: {
            project_id: projectId,
          },
        },
      })
      if (!data) throw new Error('Failed to get chat')
      return data
    },
  })
}

export const CHAT_QUERY_KEY = (chatId: string): QueryKey => ['chat', chatId]

export const useChatQuery = (chatId: string) => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: CHAT_QUERY_KEY(chatId),
    queryFn: async () => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.GET(`/v1/chats/{chat_id}`, {
        params: {
          path: {
            chat_id: chatId,
          },
        },
      })
      if (!data) throw new Error('Failed to get chat')
      return data
    },
  })
}


type StreamMessageMutationVariables = { chatId: string; message: string }
type StreamMessageMutationData = { content: string; messageId: string }
type OnChunkCallback = (content: string, messageId: string, sources?: Source[], tools?: ToolCall[]) => void

export const useStreamMessageMutation = (
  options?: MutationOptions<StreamMessageMutationData, StreamMessageMutationVariables> & { onChunk?: OnChunkCallback },
) => {
  const { getAccessToken } = useAuth()

  return useMutation({
    ...options,
    mutationFn: async ({ chatId, message }) => {
      try {
        if (!chatId || chatId === '') {
          throw new Error('Chat ID is required')
        }

        const token = await getAccessToken()
        if (!token) throw new Error('No token')

        const response = await fetch(
          `${baseUrl}/v1/chats/${chatId}/messages/stream`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ message }),
          },
        )

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error('No reader available')
        }

        const decoder = new TextDecoder()
        let accumulatedContent = ''
        let messageId = ''

        try {
          while (true) {
            const { done, value } = await reader.read()

            if (done) break

            const chunk = decoder.decode(value, { stream: true })
            const lines = chunk.split('\n')

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6))

                  if (data.id) {
                    messageId = data.id
                  }

                  if (data.chunk) {
                    accumulatedContent += data.chunk
                    options?.onChunk?.(
                      accumulatedContent,
                      messageId,
                      data.sources,
                      data.tools,
                    )
                  } else if (data.error) {
                    throw new Error(data.error)
                  }

                  // Handle sources and tools in updates
                  if (data.sources || data.tools) {
                    options?.onChunk?.(
                      accumulatedContent,
                      messageId,
                      data.sources,
                      data.tools,
                    )
                  }

                  // Handle final chunk
                  if (data.done) {
                    options?.onChunk?.(
                      accumulatedContent,
                      messageId,
                      data.sources,
                      data.tools,
                    )
                  }
                } catch (e) {
                  // Ignore JSON parse errors for incomplete chunks
                }
              }
            }
          }
        } finally {
          reader.releaseLock()
        }

        return { content: accumulatedContent, messageId }
      } catch (e) {
        throw e
      }
    },
  })
}

type CreateChatMutationVariables = ChatCreateRequest
type CreateChatMutationData = Chat

export const useCreateChatMutation = (options?: MutationOptions<CreateChatMutationData, CreateChatMutationVariables>) => {
  const { getAccessToken } = useAuth()

  return useMutation({
    ...options,
    mutationFn: async ({ project_id }) => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.POST(`/v1/chats`, {
        body: { project_id },
      })
      if (!data) throw new Error('Failed to create chat')
      return data
    },
  })
}

type UpdateChatMutationVariables = ChatUpdateRequest & { chatId: string }
type UpdateChatMutationData = Chat

export const useUpdateChatMutation = (options?: MutationOptions<UpdateChatMutationData, UpdateChatMutationVariables>) => {
  const { getAccessToken } = useAuth()

  return useMutation({
    ...options,
    mutationFn: async ({ chatId, title }) => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.PUT(`/v1/chats/{chat_id}`, {
        params: {
          path: {
            chat_id: chatId,
          },
        },
        body: { title },
      })
      if (!data) throw new Error('Failed to update chat')
      return data
    },
    onSuccess: options?.onSuccess,
  })
}
