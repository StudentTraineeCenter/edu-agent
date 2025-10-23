import { baseUrl, createApiClient } from '@/integrations/api'
import type { ChatCreateRequest, Source, ToolCall } from '@/integrations/api'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useAuth } from '@/hooks/use-auth'

export const useChatsQuery = (projectId: string) => {
  const { getAccessToken } = useAuth()
  return useQuery({
    queryKey: ['chats', projectId],
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
      return data
    },
  })
}

export const useChatQuery = (chatId: string) => {
  const { getAccessToken } = useAuth()

  return useQuery({
    queryKey: ['chat', chatId],
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
      return data
    },
  })
}

export const useStreamMessageMutation = (
  chatId: string,
  onChunk: (
    content: string,
    messageId: string,
    sources?: Source[],
    tools?: ToolCall[],
  ) => void,
) => {
  const { getAccessToken } = useAuth()

  return useMutation({
    mutationFn: async (message: string) => {
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
                    onChunk(
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
                    onChunk(
                      accumulatedContent,
                      messageId,
                      data.sources,
                      data.tools,
                    )
                  }

                  // Handle final chunk
                  if (data.done) {
                    onChunk(
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

export const useCreateChatMutation = (options?: { onSuccess?: () => void }) => {
  const { getAccessToken } = useAuth()

  return useMutation({
    mutationFn: async (chat: ChatCreateRequest) => {
      const token = await getAccessToken()
      if (!token) throw new Error('No token')

      const client = createApiClient(token)

      const { data } = await client.POST(`/v1/chats`, {
        body: chat,
      })
      return data
    },
    onSuccess: options?.onSuccess,
  })
}
