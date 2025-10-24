import { CHAT_QUERY_KEY, useChatQuery, useStreamMessageMutation } from '@/data-acess/chat'
import { chatDetailRoute } from '@/routes/_config'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { nanoid } from 'nanoid'
import {
  Message,
  MessageAvatar,
  MessageContent,
} from '@/components/ai-elements/message'
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation'
import { MessageSquareIcon } from 'lucide-react'
import {
  PromptInput,
  PromptInputBody,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputSubmit,
  type PromptInputMessage,
} from '@/components/ai-elements/prompt-input'
import { useMemo, useRef, useState, useEffect } from 'react'
import type React from 'react'
import type { ChatMessage } from '@/integrations/api'
import { Response } from '@/components/ai-elements/response'
import {
  Sources,
  SourcesTrigger,
  SourcesContent,
  Source,
} from '@/components/ai-elements/sources'
import {
  Tool,
  ToolHeader,
  ToolContent,
  ToolInput,
  ToolOutput,
} from '@/components/ai-elements/tool'
import { useNavigate } from '@tanstack/react-router'
import { projectDetailRoute } from '@/routes/_config'
import { useQueryClient } from '@tanstack/react-query'
import { PROJECT_QUERY_KEY } from '@/data-acess/project'
import { useProfilePhotoQuery } from "@/data-acess/auth.ts";

const ChatHeader = ({ title }: { title?: string }) => (
  <header className="bg-background sticky top-0 flex h-14 shrink-0 items-center gap-2">
    <div className="flex flex-1 items-center gap-2 px-3">
      <SidebarTrigger />
      <Separator
        orientation="vertical"
        className="mr-2 data-[orientation=vertical]:h-4"
      />
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1">{title}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    </div>
  </header>
)

const ChatMessages = ({ messages }: { messages: ChatMessage[] }) => {
  const navigate = useNavigate()
  const { projectId } = projectDetailRoute.useParams()

  const { data: photoUrl } = useProfilePhotoQuery()

  useEffect(() => {
    return () => {
      if (photoUrl) {
        URL.revokeObjectURL(photoUrl)
      }
    }
  }, [photoUrl])

  return (
    <Conversation className="flex-1 overflow-hidden">
      <ConversationContent>
        {messages.length === 0 ? (
          <ConversationEmptyState
            icon={<MessageSquareIcon className="size-6" />}
            title="Start a conversation"
            description="Messages will appear here as the conversation progresses."
          />
        ) : (
          messages.map((msg, index) => (
            <Message
              from={msg.role === 'user' ? 'user' : 'assistant'}
              key={msg.id ?? index}
            >
              {msg.role === 'user' ? (
                <MessageContent>{msg.content}</MessageContent>
              ) : (
                <MessageContent>
                  {msg.tools && msg.tools.length > 0 && (
                    <div className="space-y-2">
                      {msg.tools.map((tool) => (
                        <Tool key={tool.id} >
                          <ToolHeader
                            title={tool.name}
                            type={`tool-${tool.type}`}
                            state={tool.state}
                          />
                          <ToolContent>
                            {tool.input && <ToolInput input={tool.input} />}
                            {(tool.output || tool.error_text) && (
                              <ToolOutput
                                output={tool.output}
                                errorText={tool.error_text ?? undefined}
                              />
                            )}
                          </ToolContent>
                        </Tool>
                      ))}
                    </div>
                  )}
                  <Response>{msg.content}</Response>
                  {msg.sources && msg.sources.length > 0 && (
                    <Sources>
                      <SourcesTrigger count={msg.sources.length} />
                      <SourcesContent>
                        {msg.sources.map((source) => (
                          <Source
                            key={source.id}
                            href="#"
                            onClick={(e) => {
                              e.preventDefault()
                              if (!source.document_id) return
                              navigate({
                                to: '/projects/$projectId/documents/$documentId',
                                params: {
                                  projectId,
                                  documentId: source.document_id,
                                },
                                search: (prev) => ({
                                  ...prev,
                                }),
                              })
                            }}
                            title={`[${source.citation_index}] ${source.title}`}
                          />
                        ))}
                      </SourcesContent>
                    </Sources>
                  )}
                </MessageContent>
              )}
              <MessageAvatar
                name={msg.role === 'user' ? 'User' : 'AI'}
                src={
                  msg.role === 'user'
                    ? photoUrl ?? ''
                    : 'https://github.com/openai.png'
                }
              />
            </Message>
          ))
        )}
      </ConversationContent>
      <ConversationScrollButton />
    </Conversation>
  )
}

const ChatPrompt = ({
  value,
  onChange,
  status,
  onSubmit,
  textareaRef,
}: {
  value: string
  onChange: (value: string) => void
  status: 'streaming' | 'error' | 'ready'
  onSubmit: (message: PromptInputMessage) => void
  textareaRef: React.RefObject<HTMLTextAreaElement | null>
}) => (
  <div className="border-t p-4">
    <PromptInput multiple onSubmit={onSubmit}>
      <PromptInputBody>
        <PromptInputTextarea
          onChange={(e) => onChange(e.target.value)}
          ref={textareaRef}
          value={value}
        />
      </PromptInputBody>
      <PromptInputToolbar className="justify-end">
        <PromptInputSubmit status={status} />
      </PromptInputToolbar>
    </PromptInput>
  </div>
)

export const ChatDetailPage = () => {
  const { chatId } = chatDetailRoute.useParams()
  const chatQuery = useChatQuery(chatId)
  const chat = chatQuery.data

  const queryClient = useQueryClient()

  const [prompt, setPrompt] = useState<string>('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])

  useEffect(() => {
    if (chat?.messages) setMessages(chat.messages)
  }, [chat?.messages])

  const streamMessageMutation = useStreamMessageMutation(
    {
      onChunk: (chunk, messageId, sources, tools) => {
        setMessages((prev) => {
          const messageIdx = prev.findIndex((msg) => msg.id === messageId)

          if (messageIdx !== -1) {
            return prev.map((msg, idx) =>
              idx === messageIdx
                ? {
                  ...msg,
                  content: chunk,
                  sources: sources ?? msg.sources,
                  tools: tools ?? msg.tools,
                }
                : msg,
            )
          } else {
            return [
              ...prev,
              {
                id: messageId,
                role: 'assistant',
                content: chunk,
                sources: sources ?? [],
                tools: tools ?? [],
              },
            ]
          }
        })
      },
      onSettled: () => {
        queryClient.invalidateQueries({ queryKey: CHAT_QUERY_KEY(chatId) })
        if (chat?.project_id)
          queryClient.invalidateQueries({ queryKey: PROJECT_QUERY_KEY(chat.project_id) })
      }
    }
  )

  const status = useMemo(() => {
    if (streamMessageMutation.isPending) return 'streaming'
    if (streamMessageMutation.isError) return 'error'
    return 'ready'
  }, [streamMessageMutation.isPending, streamMessageMutation.isError])

  const handleSubmit = (message: PromptInputMessage) => {
    const value = message.text
    if (!value) return
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: value, sources: [], id: nanoid() },
    ])
    streamMessageMutation.mutate({
      message: value,
      chatId,
    })
    setPrompt('')
  }

  return (
    <>
      <ChatHeader title={chat?.title ?? undefined} />
      <div className="flex flex-1 flex-col p-4">
        <div className="max-w-5xl mx-auto w-full flex flex-col rounded-lg border h-[calc(100vh-6rem)]">
          <ChatMessages messages={messages} />
          <ChatPrompt
            value={prompt}
            onChange={setPrompt}
            status={status}
            onSubmit={handleSubmit}
            textareaRef={textareaRef}
          />
        </div>
      </div>
    </>
  )
}
