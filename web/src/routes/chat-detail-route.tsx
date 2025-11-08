import {
  chatAtom,
  currentChatIdAtom,
  streamMessageAtom,
} from '@/data-acess/chat'
import { chatDetailRoute } from '@/routes/_config'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
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
import { Loader2Icon, MessageSquareIcon } from 'lucide-react'
import { type PromptInputMessage } from '@/components/ai-elements/prompt-input'
import { useMemo, useRef, useState, useEffect } from 'react'
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
import {
  Result,
  useAtom,
  useAtomSet,
  useAtomValue,
} from '@effect-atom/atom-react'
import { profilePhotoAtom } from '@/data-acess/auth'
import type { ChatMessageDto } from '@/integrations/api/client'
import { Skeleton } from '@/components/ui/skeleton'
import { ChatInput } from '@/components/chats/chat-input'

const ChatHeader = ({ title }: { title?: string }) => (
  <header className="bg-background sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b px-2">
    <div className="flex flex-1 items-center gap-2 px-3">
      <SidebarTrigger />
      <Separator
        orientation="vertical"
        className="mr-2 data-[orientation=vertical]:h-4"
      />
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              {title}
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    </div>
  </header>
)

const ChatMessages = ({
  messages,
}: {
  messages: ReadonlyArray<ChatMessageDto>
}) => {
  const navigate = useNavigate()
  const { projectId } = chatDetailRoute.useParams()

  const profilePhotoResult = useAtomValue(profilePhotoAtom)
  const photoUrl =
    profilePhotoResult._tag === 'Success' ? profilePhotoResult.value : undefined

  useEffect(() => {
    return () => {
      if (photoUrl) {
        URL.revokeObjectURL(photoUrl)
      }
    }
  }, [photoUrl])

  return (
    <Conversation className="flex-1 min-h-0 max-h-full w-full">
      <ConversationContent className="max-w-5xl mx-auto">
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
                        <Tool key={tool.id}>
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
                    ? (photoUrl ?? '')
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

export const ChatDetailPage = () => {
  const params = chatDetailRoute.useParams()
  const setCurrentChat = useAtomSet(currentChatIdAtom)

  const chatResult = useAtomValue(chatAtom(params.chatId))

  const [prompt, setPrompt] = useState<string>('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const [streamMessageResult, streamMessage] = useAtom(streamMessageAtom, {
    mode: 'promise',
  })

  const status = useMemo(() => {
    if (streamMessageResult.waiting) return 'streaming'
    // if (streamMessageResult._tag === 'Failure') return 'error'
    if (streamMessageResult._tag === 'Success') return 'submitted'
    return 'ready'
  }, [streamMessageResult.waiting, streamMessageResult._tag])

  const handleSubmit = async (message: PromptInputMessage) => {
    const value = message.text
    if (!value) return
    setPrompt('')
    try {
      await streamMessage({
        message: value,
        chatId: params.chatId,
      })
    } catch {
      setPrompt(value)
    }
  }

  useEffect(() => {
    setCurrentChat(params.chatId)
  }, [params.chatId, setCurrentChat])

  return (
    <div className="flex h-full flex-col max-h-screen">
      {Result.builder(chatResult)
        .onSuccess((chat) => (
          <ChatHeader title={chat.title ?? 'Untitled chat'} />
        ))
        .onInitialOrWaiting(() => (
          <div className="h-14 shrink-0">
            <Skeleton className="w-72 h-7 mt-3 ml-4" />
          </div>
        ))
        .render()}

      <div className="flex flex-1 flex-col min-h-0 max-h-[calc(100vh-3.5rem)] overflow-hidden w-full">
        {Result.builder(chatResult)
          .onInitialOrWaiting(() => (
            <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
              <Loader2Icon className="size-4 animate-spin" />
              <span>Loading chat...</span>
            </div>
          ))
          .onFailure(() => (
            <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
              <span>Failed to load chat</span>
            </div>
          ))
          .onSuccess((chat) => (
            <>
              <div className="flex-1 min-h-0 max-h-full overflow-hidden w-full">
                <ChatMessages messages={chat.messages ?? []} />
              </div>
              <div className="shrink-0 bg-background w-full pb-4">
                <div className="max-w-5xl mx-auto">
                  <ChatInput
                    value={prompt}
                    onChange={setPrompt}
                    status={status}
                    onSubmit={handleSubmit}
                    textareaRef={textareaRef}
                  />
                </div>
              </div>
            </>
          ))
          .render()}
      </div>
    </div>
  )
}
